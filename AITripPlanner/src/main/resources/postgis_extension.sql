-- Enable PostGIS extension for spatial data support
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create custom ENUM types that Hibernate needs
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'travel_mode') THEN
        CREATE TYPE travel_mode AS ENUM ('DRIVING', 'TRANSIT', 'WALKING', 'BICYCLING');
    END IF;
END $$;
