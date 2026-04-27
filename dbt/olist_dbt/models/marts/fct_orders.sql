{{ config(materialized='table') }}

with orders as (

    select
        order_id,
        customer_id,
        order_status,
        order_purchase_date
    from {{ ref('stg_orders') }}

),

sales as (

    select
        order_id,
        sum(item_price) as order_items_value,
        sum(freight_value) as order_freight_value,
        sum(total_item_value) as total_order_value,
        count(order_item_id) as total_items
    from {{ ref('fct_sales') }}
    group by order_id

),

payments as (

    select
        order_id,
        sum(payment_value) as total_payment_value,
        count(payment_sequential) as payment_count,
        max(payment_installments) as max_payment_installments
    from {{ ref('stg_order_payments') }}
    group by order_id

)

select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_date,

    s.total_items,
    s.order_items_value,
    s.order_freight_value,
    s.total_order_value,

    p.total_payment_value,
    p.payment_count,
    p.max_payment_installments

from orders o

left join sales s
    on o.order_id = s.order_id

left join payments p
    on o.order_id = p.order_id