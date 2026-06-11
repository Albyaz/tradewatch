-- corridor_risk.sql
-- Produces a daily risk score (0-100) per corridor
-- Risk score formula:
--   - Wind component:      0-30 points (wind_speed / 80 * 30)
--   - Storm bonus:         +20 points if any_storm
--   - Sentiment component: 0-25 points (negative sentiment → higher risk)
--   - Vessel density:      0-25 points (high traffic → higher risk)

with base as (
    select * from {{ ref('int_corridor_daily') }}
),

scored as (
    select
        corridor,
        metric_date,

        -- Wind risk (0-30)
        least(avg_wind_speed / 80.0 * 30, 30) as wind_score,

        -- Storm bonus
        case when any_storm then 20 else 0 end as storm_score,

        -- Sentiment risk (0-25): more negative = higher risk
        least(greatest((0 - avg_sentiment) * 25, 0), 25) as sentiment_score,

        -- Vessel density risk (0-25)
        least(vessel_count / 150.0 * 25, 25) as vessel_score,

        avg_wind_speed,
        avg_wave_height,
        avg_sentiment,
        vessel_count,
        any_storm

    from base
),

final as (
    select
        corridor,
        metric_date,
        round(
            wind_score + storm_score + sentiment_score + vessel_score
        , 1) as risk_score,
        case
            when (wind_score + storm_score + sentiment_score + vessel_score) >= 70 then 'CRITICAL'
            when (wind_score + storm_score + sentiment_score + vessel_score) >= 50 then 'HIGH'
            when (wind_score + storm_score + sentiment_score + vessel_score) >= 30 then 'MEDIUM'
            else 'LOW'
        end as risk_level,
        round(avg_wind_speed::numeric, 1)  as avg_wind_speed,
        round(avg_wave_height::numeric, 2) as avg_wave_height,
        round(avg_sentiment::numeric, 3)   as avg_sentiment,
        vessel_count,
        any_storm
    from scored
)

select * from final
