with source as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    from {{ source('olist_raw', 'sellers') }}
    ),
cleaned as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    from source)

select * from cleaned