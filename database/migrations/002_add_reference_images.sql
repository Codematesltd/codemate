-- Add reference_images column to bookings table
ALTER TABLE bookings 
ADD COLUMN reference_images text[] DEFAULT '{}';

-- Update existing rows to have empty array if null
UPDATE bookings 
SET reference_images = '{}'
WHERE reference_images IS NULL;

-- Make sure column is not nullable
ALTER TABLE bookings 
ALTER COLUMN reference_images SET NOT NULL;
