-- stg_vessels.sql
-- Cleans and standardises raw vessel positions

with source as (
    select * from raw.vessel_positions
),

cleaned as (
    select
        id,
        mmsi,
        vessel_name,
        lat,
        lon,
        speed,
        heading,
        corridor,
        timestamp::date as position_date,
        fetched_at
    from source
    where corridor is not null
      and lat between -90 and 90
      and lon between -180 and 180
)

select * from cleaned
