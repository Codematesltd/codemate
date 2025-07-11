from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client
import os
from dotenv import load_dotenv
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import click
from werkzeug.utils import secure_filename
import base64
import time  # Add this import at the top with other imports

# Load environment variables
load_dotenv()

# Debug prints with more detail
print("Environment variables:")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY first 10 chars: {os.getenv('SUPABASE_KEY')[:10] if os.getenv('SUPABASE_KEY') else 'None'}")
print(f"SUPABASE_KEY length: {len(os.getenv('SUPABASE_KEY') or '')}")

# Validate environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '').strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Missing required environment variables. Please ensure SUPABASE_URL and SUPABASE_KEY are set in your .env file."
    )

if not SUPABASE_URL.startswith('https://') or not SUPABASE_URL.endswith('.supabase.co'):
    raise ValueError(
        "Invalid SUPABASE_URL format. Must be in format: https://[project-id].supabase.co"
    )

try:
    # Initialize Supabase client with debug info
    print(f"Attempting to connect to Supabase at: {SUPABASE_URL}")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Test the connection without get_session
    test = supabase.auth.get_user()
    print("Supabase connection successful")
except Exception as e:
    print(f"Failed to initialize Supabase client: {str(e)}")
    print(f"URL used: {SUPABASE_URL}")
    print(f"Key length: {len(SUPABASE_KEY)}")
    raise

# Add this after Supabase client initialization
try:
    # Check if bucket exists
    buckets = supabase.storage.list_buckets()
    bucket_exists = any(bucket.get('name') == 'refrence' for bucket in buckets)
    
    if not bucket_exists:
        # Create bucket with public access
        supabase.storage.create_bucket(
            'refrence',
            options={
                'public': True,
                'file_size_limit': 5242880,  # 5MB in bytes
                'allowed_mime_types': ['image/*']
            }
        )
        
        # Set bucket policy to allow uploads
        supabase.storage.from_('refrence').update(
            {
                'id': 'refrence',
                'policy': {
                    'policies': [
                        {
                            'effect': 'allow',
                            'actions': ['select', 'insert', 'update'],
                            'role': 'authenticated'
                        },
                        {
                            'effect': 'allow',
                            'actions': ['select'],
                            'role': 'anon'
                        }
                    ]
                }
            }
        )
        print("Created 'refrence' bucket with permissions")
    else:
        print("'refrence' bucket exists")
except Exception as e:
    print(f"Bucket check/creation error: {str(e)}")
    print("Please ensure bucket permissions are set in Supabase dashboard")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

def generate_password(length=9):
    # Get 4 random letters (mix of upper and lower case)
    letters = ''.join(random.choice(string.ascii_letters) for _ in range(4))
    
    # Get 1 special character
    special = random.choice("!@#$%^&*")
    
    # Get 4 random numbers
    numbers = ''.join(random.choice(string.digits) for _ in range(4))
    
    # Combine all parts
    password = letters + special + numbers
    
    return password

def send_credentials_email(email, project_id, password):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    print("Email Configuration:")
    print(f"Sender Email: {sender_email}")
    print(f"Password Length: {len(sender_password) if sender_password else 0}")
    
    if not sender_email or not sender_password:
        print("Email configuration missing")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = f'Your CodeMate Project Details - {project_id}'
    
    body = f"""
    Dear Client,
    
    Thank you for choosing CodeMate. Here are your project details:
    
    Project ID: {project_id}
    Login Email: {email}
    Password: {password}
    
    You can login to track your project at: http://yourwebsite.com/client/login
    
    Best regards,
    CodeMate Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print(f"Attempting to send email from {sender_email} to {email}")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.set_debuglevel(1)  # Enable debug output
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {str(e)}")
        print(f"Using email: {sender_email}")
        print("Please verify your Gmail App Password")
        return False
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_decline_email(email, project_id):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = f'CodeMates Project Update - {project_id}'
    
    body = f"""
    Dear Client,
    
    We regret to inform you that your project request (ID: {project_id}) has been declined.
    
    If you have any questions or would like to submit a new project with different requirements,
    please feel free to contact us or submit a new request.
    
    Best regards,
    CodeMate Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send decline email: {str(e)}")
        return False

def send_project_completed_email(email, project_id):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = f'Your CodeMate Project {project_id} is Complete!'

    body = f"""
    Dear Client,

    Congratulations! Your project (ID: {project_id}) has been completed.

    Please log in to your dashboard to review the final deliverables and contact us if you have any questions.

    Thank you for choosing CodeMate!

    Best regards,
    CodeMate Team
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Project completion email sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send project completion email: {str(e)}")
        return False

# Add this after your imports
ADMIN_EMAILS = [
    'nadager990@gmail.com',
    'shrinivasnadager03@gmail.com',
    'basavarajagurikar2004@gmail.com',
    'narasareddy8296@gmail.com'
    # Add more admin emails as needed
]

def notify_admins_new_consultation(consultation_data):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        
        # Send individual emails to each admin
        for admin_email in ADMIN_EMAILS:
            msg = MIMEMultipart()  # Create new message for each recipient
            msg['From'] = sender_email
            msg['To'] = admin_email
            msg['Subject'] = 'New Consultation Request - CodeMates'
            
            body = f"""
            New consultation request received!

            Name: {consultation_data['name']}
            Email: {consultation_data['email']}
            Phone: {consultation_data['phone']}
            Service: {consultation_data['service']}
            
            Query:
            {consultation_data['query']}
            
            Please check admin dashboard for more details.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            server.send_message(msg)
            print(f"Notification sent to admin: {admin_email}")
        
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send admin notifications: {str(e)}")
        return False

def notify_admins_new_project(project_data):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        
        # Send individual emails to each admin
        for admin_email in ADMIN_EMAILS:
            msg = MIMEMultipart()  # Create new message for each recipient
            msg['From'] = sender_email
            msg['To'] = admin_email
            msg['Subject'] = f'New Project Request - {project_data["project_id"]}'
            
            body = f"""
            New project request received!

            Project ID: {project_data['project_id']}
            Name: {project_data['name']}
            Email: {project_data['email']}
            Phone: {project_data['mobile']}
            Service: {project_data['service_selected']}
            
            Additional Services: {', '.join(project_data['additional_services']) if project_data['additional_services'] else 'None'}
            
            Requirements:
            {project_data['requirements']}
            
            Reference URLs:
            {project_data['reference_urls'] or 'None'}
            
            Reference Images: {len(project_data['reference_images'])} uploaded
            
            Please check admin dashboard for more details and to approve/decline the project.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            server.send_message(msg)
            print(f"Project notification sent to admin: {admin_email}")
        
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send admin project notifications: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/project_details/<project_id>')
def project_details(project_id):
    if not session.get('admin_logged_in'):
        return {'error': 'Unauthorized'}, 401
    
    try:
        # Fetch project details including reference images
        result = supabase.table('bookings').select('*').eq('project_id', project_id).execute()
        
        if not result.data:
            return {'error': 'Project not found'}, 404
        
        project = result.data[0]
        
        # Get public URLs for all reference images
        if project.get('reference_images'):
            # Images are already stored as public URLs
            image_urls = project['reference_images']
        else:
            image_urls = []
        
        return {
            **project,
            'reference_images': image_urls
        }
    except Exception as e:
        print(f"Error fetching project details: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        try:
            form_data = request.form
            result = supabase.table('bookings').select('id').execute()
            project_id = f"CMDT-{len(result.data) + 1:04d}"
            password = generate_password()
            
            image_urls = []
            if 'reference_images' in request.files:
                uploaded_files = request.files.getlist('reference_images')
                for file in uploaded_files:
                    if file and file.filename:
                        try:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{project_id}_{int(time.time())}_{filename}"
                            file_data = file.read()

                            print(f"Attempting to upload {unique_filename} to 'refrence' bucket")
                            
                            # Simplified upload call
                            storage_response = supabase.storage.from_('refrence').upload(
                                unique_filename,
                                file_data
                            )
                            
                            print(f"Upload response: {storage_response}")
                            
                            # Get public URL
                            if storage_response:
                                file_url = supabase.storage.from_('refrence').get_public_url(unique_filename)
                                image_urls.append(file_url)
                                print(f"File uploaded successfully: {file_url}")
                            
                        except Exception as upload_error:
                            print(f"Detailed upload error: {str(upload_error)}")
                            continue

            booking_data = {
                'project_id': project_id,
                'name': form_data['name'],
                'email': form_data['email'],
                'mobile': f"{form_data['country_code']}{form_data['phone']}",
                'service_selected': form_data['service'],
                'additional_services': request.form.getlist('additional_services'),
                'requirements': form_data['requirements'],
                'reference_urls': form_data.get('reference_urls', ''),
                'reference_images': image_urls,
                'progress': 0,
                'password': password,
                'status': 'pending_approval'  # Remove approved field since it has default value
            }

            print("Attempting to insert booking with data:", booking_data)
            try:
                booking_result = supabase.table('bookings').insert(booking_data).execute()
                print("Booking created:", booking_result.data)
                
                # Notify admins about new project
                notify_admins_new_project(booking_data)
                
                return render_template('thank_you.html', project_id=project_id)
            except Exception as db_error:
                print(f"Database error: {str(db_error)}")
                raise db_error

        except Exception as e:
            print(f"Order submission error: {str(e)}")
            return str(e), 500

    return render_template('order.html')

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    bookings = supabase.table('bookings').select('*').execute()
    # Update booking status to completed if progress is 100%
    for booking in bookings.data:
        if booking.get('progress') == 100:
            booking['status'] = 'completed'
    
    consultations = supabase.table('consultations').select('*').order('id', desc=True).execute()
    return render_template('admin_dashboard.html', bookings=bookings.data, consultations=consultations.data)

@app.cli.command("create-admin")
@click.argument("email")
@click.argument("password")
def create_admin(email, password):
    """Create a new admin user."""
    try:
        # Check if admin already exists
        existing = supabase.table('admin_users').select('*').eq('email', email).execute()
        if existing.data:
            print(f"Admin with email {email} already exists!")
            return
        
        # Create new admin user with hashed password
        admin = supabase.table('admin_users').insert({
            'email': email,
            'password_hash': generate_password_hash(password)
        }).execute()
        print(f"Admin user {email} created successfully!")
    except Exception as e:
        print(f"Error creating admin: {str(e)}")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            
            # Check admin credentials against admin_users table
            admin = supabase.table('admin_users').select('*').eq('email', email).execute()
            
            if admin.data and len(admin.data) > 0 and check_password_hash(admin.data[0]['password_hash'], password):
                session['admin_logged_in'] = True
                return redirect(url_for('admin'))
            else:
                return render_template('admin_login.html', error='Invalid credentials')
        except Exception as e:
            print(f"Login error: {str(e)}")
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/client')
def client():
    if not session.get('client_logged_in'):  # Fixed extra parenthesis
        return redirect(url_for('client_login'))
    
    client_email = session.get('client_email')
    try:
        projects = supabase.table('bookings').select('*').eq('email', client_email).execute()
        
        for project in projects.data:
            # Fetch notes
            notes = supabase.table('progress_notes').select('*')\
                .eq('project_id', project['project_id'])\
                .order('created_at', desc=True)\
                .execute()
            project['notes'] = notes.data
            
            # Fetch and process snapshots
            snapshots = supabase.table('project_snapshots')\
                .select('*')\
                .eq('project_id', project['project_id'])\
                .order('created_at', desc=True)\
                .execute()
            
            print(f"Fetched snapshots for {project['project_id']}: {snapshots.data}")  # Debug print
            
            # Process snapshot URLs
            for snapshot in snapshots.data:
                if not snapshot['image_url'].startswith('http'):
                    snapshot['image_url'] = supabase.storage.from_('refrence')\
                        .get_public_url(f"snapshots/{project['project_id']}/{snapshot['image_url']}")
            
            project['snapshots'] = snapshots.data

            # Process reference images
            if project.get('reference_images'):
                project['reference_images'] = [
                    url if url.startswith('http') else supabase.storage.from_('refrence').get_public_url(url)
                    for url in project['reference_images']
                ]
        
        return render_template('client_dashboard.html', projects=projects.data)
    except Exception as e:
        print(f"Error fetching client projects: {str(e)}")
        return render_template('client_dashboard.html', projects=[])

@app.route('/client/register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            # Register new user in Supabase Auth
            user = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return render_template('client_login.html', message='Registration successful! Please login.')
        except Exception as e:
            return render_template('client_register.html', error=str(e))
    
    return render_template('client_register.html')

@app.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            
            # Check credentials against bookings table
            user = supabase.table('bookings').select('*').eq('email', email).eq('password', password).execute()
            
            if user.data and len(user.data) > 0:
                session['client_logged_in'] = True
                session['client_email'] = email
                return redirect(url_for('client'))
            else:
                return render_template('client_login.html', error='Invalid credentials')
        except Exception as e:
            print(f"Login error: {str(e)}")
            return render_template('client_login.html', error='Invalid credentials')
    
    return render_template('client_login.html')

@app.route('/client/logout', methods=['POST'])
def client_logout():
    session.pop('client_logged_in', None)
    session.pop('client_email', None)
    return redirect(url_for('client_login'))

@app.route('/admin/update_project', methods=['POST'])
def update_project():
    if not session.get('admin_logged_in'):
        return {'error': 'Unauthorized'}, 401
    
    try:
        data = request.form
        project_id = data.get('project_id')
        progress = float(data.get('progress', 0))
        note = data.get('note')
        
        # Add status update when progress is 100%
        update_data = {
            'progress': progress,
            'status': 'completed' if progress == 100 else 'approved'
        }
        
        # Update project progress and status
        result = supabase.table('bookings').update(update_data).eq('project_id', project_id).execute()
        print("Update result:", result)  # Debug print

        # Check for errors in the response
        if hasattr(result, 'error') and result.error:
            print("Supabase update error:", result.error)
            return {'error': str(result.error)}, 500

        # result.data is a list of updated rows
        if result.data and len(result.data) > 0:
            # Add note if provided
            if note:
                supabase.table('progress_notes').insert({
                    'project_id': project_id,
                    'note': note,
                    'progress_value': progress,
                    'created_at': 'NOW()'
                }).execute()

            # Send completion email if progress is 100%
            if progress == 100:
                project = supabase.table('bookings').select('email').eq('project_id', project_id).execute()
                if project.data and len(project.data) > 0 and project.data[0].get('email'):
                    send_project_completed_email(project.data[0]['email'], project_id)

            return {'success': True, 'message': 'Project updated successfully'}

        print("No rows updated for project_id:", project_id)
        return {'error': 'Project not found'}, 404
        
    except Exception as e:
        print(f"Error updating project: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/admin/approve_project/<project_id>', methods=['POST'])
def approve_project(project_id):  # Add project_id parameter
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        # Update project status without needing form data
        result = supabase.table('bookings').update({
            'status': 'approved',
            'approved': True
        }).eq('project_id', project_id).execute()

        if result.data:
            # Get project details from the result
            project = result.data[0]
            # Send welcome email with credentials ONLY after approval
            send_credentials_email(project['email'], project_id, project['password'])
            return {'success': True, 'message': 'Project approved successfully'}
        
        return {'error': 'Project not found'}, 404
        
    except Exception as e:
        print(f"Approval error: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/admin/decline_project/<project_id>', methods=['POST'])
def decline_project(project_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        # Update project status
        result = supabase.table('bookings').update({
            'status': 'declined',
            'approved': False
        }).eq('project_id', project_id).execute()

        if result.data:
            # Get project details
            project = result.data[0]
            # Send decline email
            send_decline_email(project['email'], project_id)
            return {'success': True}
        
        return {'error': 'Project not found'}, 404
        
    except Exception as e:
        print(f"Decline error: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/consultation', methods=['GET', 'POST'])
def consultation():
    if request.method == 'POST':
        try:
            consultation_data = {
                'name': request.form['name'],
                'email': request.form['email'],
                'phone': request.form['phone'],
                'service': request.form['service'],
                'query': request.form['query']
            }
            
            # Insert into database
            supabase.table('consultations').insert(consultation_data).execute()
            
            # Notify admins
            notify_admins_new_consultation(consultation_data)
            
            return render_template('consultation_thankyou.html')
        except Exception as e:
            return render_template('consultation.html', error=str(e))
    return render_template('consultation.html')

@app.route('/admin/consultations')
def admin_consultations():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    consultations = supabase.table('consultations').select('*').order('id', desc=True).execute()
    return render_template('admin_consultations.html', consultations=consultations.data)

@app.route('/admin/consultation/<int:consultation_id>/complete', methods=['POST'])
def mark_consultation_completed(consultation_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    supabase.table('consultations').update({'completed': True}).eq('id', consultation_id).execute()
    return redirect(url_for('admin'))

@app.route('/admin/consultation/<int:consultation_id>/pending', methods=['POST'])
def mark_consultation_pending(consultation_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    supabase.table('consultations').update({'completed': False}).eq('id', consultation_id).execute()
    return redirect(url_for('admin'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)