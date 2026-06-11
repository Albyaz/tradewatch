-- stg_weather.sql
-- Cleans and standardises raw weather data per corridor

with source as (
    select * from raw.corridor_weather
),

cleaned as (
    select
        id,
        corridor,
        lat,
        lon,
        wind_speed,
        wave_height,
        visibility,
        storm_flag,
        recorded_at::date as record_date,
        fetched_at
    from source
    where corridor is not null
      and wind_speed >= 0
)

select * from cleaned
