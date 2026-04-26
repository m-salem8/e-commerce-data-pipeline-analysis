with source as (

    select
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp
    from {{ source('olist_raw', 'orders') }}

),

cleaned as (

    select
        order_id,
        customer_id,
        order_status,

        cast(order_purchase_timestamp as timestamp) as order_purchase_ts,
        date(order_purchase_timestamp) as order_purchase_date,

        extract(year from order_purchase_timestamp) as order_purchase_year,
        extract(month from order_purchase_timestamp) as order_purchase_month,
        extract(day from order_purchase_timestamp) as order_purchase_day,
        extract(hour from order_purchase_timestamp) as order_purchase_hour

    from source

)

select *
from cleaned