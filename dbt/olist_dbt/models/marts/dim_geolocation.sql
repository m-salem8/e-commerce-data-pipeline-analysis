{{ config(materialized='table') }}

with source as (

    select *
    from {{ ref('stg_geolocation') }}

),

deduplicated as (

    select
        geolocation_zip_code_prefix,
        any_value(geolocation_city) as geolocation_city,
        any_value(geolocation_state) as geolocation_state,
        avg(geolocation_lat) as geolocation_lat,
        avg(geolocation_lng) as geolocation_lng
    from source
    group by geolocation_zip_code_prefix

)

select *
from deduplicated