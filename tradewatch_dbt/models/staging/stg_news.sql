-- stg_news.sql
-- Cleans and standardises raw news articles

with source as (
    select * from raw.news_articles
),

cleaned as (
    select
        id,
        corridor,
        title,
        source,
        sentiment_score,
        published_at::date as publish_date,
        fetched_at
    from source
    where corridor is not null
      and title is not null
)

select * from cleaned
