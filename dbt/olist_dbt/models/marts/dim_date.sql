{{ config(materialized='table') }}

with dates as (

    select
        date_day
    from unnest(generate_date_array('2016-01-01', '2018-12-31')) as date_day

)

select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    extract(quarter from date_day) as quarter,
    format_date('%A', date_day) as weekday_name,
    format_date('%B', date_day) as month_name
from dates