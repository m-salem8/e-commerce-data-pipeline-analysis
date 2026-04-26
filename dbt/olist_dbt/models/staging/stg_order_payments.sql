with source as (
    
    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    from {{ source('olist_raw', 'order_payments') }}

),
cleaned as (

    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    from source)

select * 
from cleaned
