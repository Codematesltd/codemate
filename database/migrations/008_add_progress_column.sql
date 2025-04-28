-- Add progress column if it doesn't exist
ALTER TABLE public.bookings 
ADD COLUMN IF NOT EXISTS progress double precision DEFAULT 0;

-- Update existing rows
UPDATE public.bookings 
SET progress = 0 
WHERE progress IS NULL;
