{{ config(materialized='table') }}

with orders as (

    select
        order_id,
        customer_id,
        order_status,
        order_purchase_date
    from {{ ref('stg_orders') }}

),

order_items as (

    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        price,
        freight_value
    from {{ ref('stg_order_items') }}

)

select
    oi.order_id,
    oi.order_item_id,

    -- dimension keys
    o.customer_id,
    oi.product_id,
    oi.seller_id,
    o.order_purchase_date,

    -- degenerate/status attribute
    o.order_status,

    -- measures
    oi.price as item_price,
    oi.freight_value,
    oi.price + oi.freight_value as total_item_value

from order_items oi
left join orders o
    on oi.order_id = o.order_id