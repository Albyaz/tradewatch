-- int_corridor_daily.sql
-- Joins weather, news sentiment, and vessel counts per corridor per day

with weather as (
    select
        corridor,
        record_date,
        avg(wind_speed)   as avg_wind_speed,
        avg(wave_height)  as avg_wave_height,
        avg(visibility)   as avg_visibility,
        bool_or(storm_flag) as any_storm,
        count(*)          as weather_readings
    from {{ ref('stg_weather') }}
    group by corridor, record_date
),

news as (
    select
        corridor,
        publish_date,
        avg(sentiment_score) as avg_sentiment,
        count(*)             as article_count
    from {{ ref('stg_news') }}
    group by corridor, publish_date
),

vessels as (
    select
        corridor,
        position_date,
        count(distinct mmsi) as vessel_count,
        avg(speed)           as avg_speed
    from {{ ref('stg_vessels') }}
    group by corridor, position_date
),

joined as (
    select
        coalesce(w.corridor, n.corridor, v.corridor) as corridor,
        coalesce(w.record_date, n.publish_date, v.position_date) as metric_date,
        coalesce(w.avg_wind_speed, 0)  as avg_wind_speed,
        coalesce(w.avg_wave_height, 0) as avg_wave_height,
        coalesce(w.avg_visibility, 999) as avg_visibility,
        coalesce(w.any_storm, false)   as any_storm,
        coalesce(n.avg_sentiment, 0)   as avg_sentiment,
        coalesce(n.article_count, 0)   as article_count,
        coalesce(v.vessel_count, 0)    as vessel_count,
        coalesce(v.avg_speed, 0)       as avg_vessel_speed
    from weather w
    full outer join news n
        on w.corridor = n.corridor and w.record_date = n.publish_date
    full outer join vessels v
        on coalesce(w.corridor, n.corridor) = v.corridor
        and coalesce(w.record_date, n.publish_date) = v.position_date
)

select * from joined
