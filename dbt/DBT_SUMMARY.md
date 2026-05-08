# DBT Project Summary — `olist_dbt`

## Overview

This project uses **dbt (data build tool)** to transform Brazilian e-commerce (Olist) data that has been ingested into **Google BigQuery**. The dbt models are orchestrated via **Airflow** (using the `cosmos` package) as part of an end-to-end data pipeline.

The architecture follows a **Medallion / multi-layer** design:
- **Raw Layer** → `olist_raw` schema (source data ingested from CSV → GCS → BigQuery)
- **Staging Layer** → `olist.stage` schema (light cleaning & type casting)
- **Mart Layer** → `olist.marts` schema (dimension & fact tables for analytics)

---

## Directory Structure

```
dbt/olist_dbt/
├── dbt_project.yml        # dbt project configuration
├── profiles.yml           # BigQuery connection profile
├── README.md              # Default dbt readme
├── models/
│   ├── source.yml         # Source definitions (raw tables in BigQuery)
│   ├── staging/           # Staging models (light transformations)
│   │   ├── stg_customers.sql
│   │   ├── stg_geolocation.sql
│   │   ├── stg_order_items.sql
│   │   ├── stg_order_payments.sql
│   │   ├── stg_orders.sql
│   │   ├── stg_products.sql
│   │   └── stg_sellers.sql
│   └── marts/             # Mart / business models (tables)
│       ├── dim_customers.sql
│       ├── dim_date.sql
│       ├── dim_geolocation.sql
│       ├── dim_order_payments.sql
│       ├── dim_products.sql
│       ├── dim_sellers.sql
│       ├── fct_orders.sql
│       ├── fct_sales.sql
│       └── schema.yml     # Documentation & tests for marts
├── macros/                # (reserved for custom macros)
├── analyses/              # (reserved for analytical SQL)
├── seeds/                 # (reserved for CSV seed data)
├── snapshots/             # (reserved for snapshot models)
└── tests/                 # (reserved for custom tests)
```

---

## Configuration Files

### `dbt_project.yml`
| Setting | Value | Purpose |
|---------|-------|---------|
| `name` | `olist_dbt` | Project name |
| `profile` | `olist_dbt` | Matches the profile name in `profiles.yml` |
| `staging` materialization | `view` | Staging models are **views** (no storage cost) |
| `staging` schema | `stage` | All staging models land in `olist.stage` |
| `marts` materialization | `table` | Mart models are **tables** (for performance in BI) |
| `marts` schema | `marts` | All mart models land in `olist.marts` |

### `profiles.yml`
- **Target**: BigQuery
- **Authentication**: Service-account JSON key file (`include/gcp/airflow-sa.json`)
- **Dataset**: `olist` (within `olist-494419` project)
- **Region**: `EU`

### `source.yml`
Defines **9 source tables** from the `olist_raw` BigQuery dataset:
`customers`, `orders`, `order_items`, `order_payments`, `order_reviews`, `products`, `sellers`, `geolocation`, `product_category_translation`

---

## Staging Models (Views)

These models **source data from `olist_raw`**, perform basic cleaning and type casting, and are materialized as **views**.

| File | Source Table | Transformations | Key Columns |
|------|------------|-----------------|-------------|
| `stg_customers.sql` | `olist_raw.customers` | Renamed columns directly | `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state` |
| `stg_geolocation.sql` | `olist_raw.geolocation` | Renamed columns directly | `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng`, `geolocation_city`, `geolocation_state` |
| `stg_order_items.sql` | `olist_raw.order_items` | Casts `shipping_limit_date` → timestamp + date columns | `order_id`, `order_item_id`, `product_id`, `seller_id`, `shipping_limit_ts`, `shipping_limit_date`, `price`, `freight_value` |
| `stg_order_payments.sql` | `olist_raw.order_payments` | Renamed columns directly | `order_id`, `payment_sequential`, `payment_type`, `payment_installments`, `payment_value` |
| `stg_orders.sql` | `olist_raw.orders` | Casts `order_purchase_timestamp` → timestamp + extracts year/month/day/hour | `order_id`, `customer_id`, `order_status`, `order_purchase_ts`, `order_purchase_date`, `order_purchase_year`, `order_purchase_month`, `order_purchase_day`, `order_purchase_hour` |
| `stg_products.sql` | `olist_raw.products` | Filters out null `product_id` | `product_id`, `product_category_name`, dimensions, weight/size columns |
| `stg_sellers.sql` | `olist_raw.sellers` | Renamed columns directly | `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state` |

---

## Mart Models (Tables)

These models build on staging views to create **analytics-ready dimension and fact tables**, materialized as **tables**.

### Dimension Tables

| Model | Source | Purpose | Key Details |
|-------|--------|---------|-------------|
| **`dim_customers`** | `stg_customers` | Clean customer dimension | Selects all staging columns; used as a lookup for customer attributes |
| **`dim_date`** | Generated date series | Calendar date dimension | Generates all dates from **2016-01-01 to 2018-12-31**; includes `year`, `month`, `day`, `quarter`, `weekday_name`, `month_name` |
| **`dim_geolocation`** | `stg_geolocation` | Deduplicated location dimension | Groups by `geolocation_zip_code_prefix`; averages lat/lng; deduplicates city/state via `ANY_VALUE` |
| **`dim_order_payments`** | `stg_order_payments` | Aggregated payment per order | Groups by `order_id` using `SUM`, `COUNT`, `MAX`, and `STRING_AGG` of distinct payment types |
| **`dim_products`** | `stg_products` | Clean product dimension | Renames columns (`product_name_lenght` → `product_name_length`, etc.) |
| **`dim_sellers`** | `stg_sellers` | Clean seller dimension | Selects all staging columns directly |

### Fact Tables

| Model | Source(s) | Purpose | Key Details |
|-------|-----------|---------|-------------|
| **`fct_sales`** | `stg_orders` + `stg_order_items` | Sales fact at **order-item grain** | Each row = one product in one order. Joins orders on `order_id` to bring in `customer_id`, `order_date`, `order_status`. Computes `item_price`, `freight_value`, and `total_item_value` (price + freight). |
| **`fct_orders`** | `stg_orders` + `fct_sales` + `stg_order_payments` | Order-level fact table | Aggregates `fct_sales` by order (sums, counts items), joins payment summaries from `stg_order_payments`. One row per order with complete financial picture. |

### Schema & Tests (`schema.yml`)

- `dim_sellers`: Tests `not_null` + `unique` on `seller_id`
- `fct_sales`: Documents `order_id` and `total_item_value` columns

---

## Data Lineage (Dependency Graph)

```
Raw Layer (olist_raw)        Staging (Views)              Marts (Tables)
─────────────────────────────────────────────────────────────────────
olist_raw.customers  ─────>  stg_customers  ────────>  dim_customers
olist_raw.geolocation ────>  stg_geolocation  ──────>  dim_geolocation
olist_raw.products   ─────>  stg_products   ────────>  dim_products
olist_raw.sellers    ─────>  stg_sellers    ────────>  dim_sellers
olist_raw.orders     ─────>  stg_orders ─┐
                                          ├──> fct_sales ──> fct_orders
olist_raw.order_items ────>  stg_order_items ┘
                                                      
olist_raw.order_payments ─> stg_order_payments ─────> dim_order_payments
                                                      fct_orders ──┘
                                           (generated) ─> dim_date
```

---

## Pipeline Integration (Airflow)

The Airflow DAG **`olist_full_pipeline`** (`dags/staging_to_gcs.py`) orchestrates:

1. **`upload_to_gcs`** — Runs Python script to ingest CSV files from local to GCS
2. **`load_*` tasks** (parallel) — Loads each CSV from GCS into the corresponding `olist_raw` BigQuery table
3. **`dbt_models`** (DbtTaskGroup via Cosmos) — Executes `dbt run` to build all staging + mart models

```
upload_to_gcs → [load_customers, load_orders, ...] → dbt_models (stg → marts)
```

---

## How to Run

```bash
# Run all models
dbt run

# Run only staging
dbt run --select staging

# Run only marts (depends on staging)
dbt run --select marts

# Run specific model
dbt run --select dim_customers

# Test models
dbt test

# View documentation
dbt docs generate
dbt docs serve
```
