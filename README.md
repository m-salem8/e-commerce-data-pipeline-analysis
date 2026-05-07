# E-Commerce Data Engineering Pipeline

## Overview

A production-like end-to-end data pipeline built with modern data engineering tools. 

```
Python → GCS (Data Lake) → BigQuery (Warehouse) → dbt (Transformation) → Airflow (Orchestration) → Power BI (Visulaization & Analysis)
```

---

## Tech Stack

| Layer | Tool | Role |
|---|---|---|
| Ingestion | Python | Download & upload data |
| Data Lake | Google Cloud Storage (GCS) | Raw storage |
| Warehouse | BigQuery | Scalable compute |
| Transformation | dbt | SQL modeling |
| Orchestration | Airflow (Astro) | Scheduling |
| Integration | Cosmos | dbt + Airflow bridge |

---

## Project Structure

```
e-commerce/
├── dags/
│   └── olist_full_pipeline.py       # Airflow DAG
├── include/
│   ├── scripts/                     # Python ingestion scripts
│   └── gcp/
│       └── airflow-sa.json          # Service account key
├── dbt/
│   └── olist_dbt/
│       ├── models/
│       │   ├── staging/             # Cleaned raw data
│       │   └── marts/               # Fact & dimension tables
│       ├── dbt_project.yml
│       └── profiles.yml             # Used inside Airflow
├── requirements.txt
└── README.md
```

---

## Cloud Architecture
![alt text](image.png)
### GCS — Data Lake

- Stores raw CSV files
- Landing zone before BigQuery ingestion

### BigQuery — Warehouse

```
olist_raw     → raw ingestion layer
olist_stage   → staging layer
olist_marts   → analytics-ready layer
```

---

## Authentication

Service account key location:

```
include/gcp/airflow-sa.json
```

Used for: GCS access, BigQuery access, dbt execution, and Airflow tasks.

> **Note:** Local path ≠ Docker container path.

| Environment | Path |
|---|---|
| Local | `/home/.../airflow-sa.json` |
| Container | `/usr/local/airflow/include/gcp/airflow-sa.json` |

---

## How to Run

**Start Astro (Airflow):**

```bash
astro dev start
```

This starts the Scheduler, Webserver, Worker, and Metadata DB. The project mounts inside the container at `/usr/local/airflow/`.

**Trigger the DAG:**

```
olist_full_pipeline
```

---

## Pipeline Orchestration

DAG execution order:

```
upload_to_gcs
      ↓
load_* (BigQuery)
      ↓
dbt_models (Cosmos)
```
![alt text](<Screenshot from 2026-04-28 21-26-00.png>)
---

## dbt + Cosmos Integration

Cosmos converts each dbt model into an individual Airflow task, instead of running everything as a single `dbt run` task.

**Configuration example:**

```python
DbtTaskGroup(
    group_id="dbt_models",
    project_config=ProjectConfig(
        dbt_project_path=DBT_PROJECT_PATH,
    ),
    profile_config=ProfileConfig(
        profile_name="olist_dbt",
        target_name="dev",
        profiles_yml_filepath=f"{DBT_PROJECT_PATH}/profiles.yml",
    ),
    execution_config=ExecutionConfig(
        dbt_executable_path=DBT_EXECUTABLE_PATH,
    ),
)
```

---

## Transformation Layer

```
staging → dimensions → facts
```

- **Staging models** — clean and normalize raw data
- **Dimension tables** — provide descriptive context
- **Fact tables** — store measurable metrics

---

## Data Modeling — Star Schema

**Fact table:**

- `fct_sales` — item-level transactions (price, freight, total)
- `fct_orders` — order-level aggregations

**Dimension tables:**

- `dim_customers`
- `dim_products`
- `dim_sellers`
- `dim_date`

Star schema reduces redundancy, improves query performance, and is the industry standard for analytics warehouses.

---

## Data Visualization & Analysis
![!\[alt text\](pwoerBI-1.png)](images/pwoerBI.png)

## Data Quality

dbt tests applied across models:

- `not_null`
- `unique`
- `relationships`
- `store_failures` — tracks rejected rows for audit

---

## Mental Model

| Component | Role |
|---|---|
| Airflow | Orchestrator — schedules and triggers tasks |
| dbt | Transformation layer — SQL modeling |
| BigQuery | Compute engine — executes SQL at scale |
| GCS | Storage — raw file landing zone |
| Service Account | Authentication — GCP access credentials |

---

## Common Pitfalls

- Wrong service account key path (local vs. container)
- Mixing local and container config values
- dbt `profiles.yml` pointing to wrong target
- Python dependency conflicts in the Astro environment
