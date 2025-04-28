-- Add status and approved columns to bookings table
ALTER TABLE public.bookings 
ADD COLUMN IF NOT EXISTS status text DEFAULT 'pending_approval',
ADD COLUMN IF NOT EXISTS approved boolean DEFAULT false;

-- Update any existing records
UPDATE public.bookings 
SET status = 'pending_approval', approved = false 
WHERE status IS NULL;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_bookings_status ON public.bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_approved ON public.bookings(approved);
