# 🛒 E-Commerce Data Engineering Pipeline

## 🚀 Overview

This project implements a **production-like end-to-end data pipeline** using modern data engineering tools:

Python → GCS (Data Lake) → BigQuery (Warehouse) → dbt (Transformation) → Airflow (Orchestration)

---

## 🧠 Architecture

### 🔷 Pipeline Flow
Python (Ingestion)
↓
GCS (Data Lake)
↓
BigQuery (Raw Layer)
↓
dbt (Staging → Marts)
↓
Analytics-ready tables


---

## ⚙️ Tech Stack

| Layer | Tool | Role |
|------|------|------|
| Ingestion | Python | Download & upload data |
| Data Lake | Google Cloud Storage (GCS) | Raw storage |
| Warehouse | BigQuery | Scalable compute |
| Transformation | dbt | SQL modeling |
| Orchestration | Airflow (Astro) | Scheduling |
| Integration | Cosmos | dbt + Airflow |

---

## 🏗️ Project Structure


e-commerce/
│
├── dags/ # Airflow DAGs
│ └── olist_full_pipeline.py
│
├── include/
│ ├── scripts/ # Python ingestion scripts
│ └── gcp/
│ └── airflow-sa.json # Service account key
│
├── dbt/
│ └── olist_dbt/
│ ├── models/
│ │ ├── staging/ # Cleaned data
│ │ └── marts/ # Fact & dimension tables
│ ├── dbt_project.yml
│ └── profiles.yml # Used inside Airflow
│
├── requirements.txt
└── README.md


---

## ☁️ Cloud Architecture

### 🪣 GCS (Data Lake)

- Stores raw CSV files
- Landing zone before BigQuery

### 🧱 BigQuery (Warehouse)

Datasets:


olist_raw → raw ingestion
olist_stage → staging layer
olist_marts → analytics layer


---

## 🔐 Authentication

### Service Account Key


include/gcp/airflow-sa.json


Used for:
- GCS access
- BigQuery access
- dbt execution
- Airflow tasks

---

## ⚠️ Important Concept

Local path ≠ Docker path

| Environment | Path |
|------------|------|
| Local | `/home/.../airflow-sa.json` |
| Container | `/usr/local/airflow/include/gcp/airflow-sa.json` |

---

## 🐳 Airflow (Astro)

Run:


astro dev start


This starts:
- Scheduler
- Webserver
- Worker
- Metadata DB

Project is mounted inside container at:


/usr/local/airflow/


---

## 🔄 Pipeline Orchestration

### DAG Flow


upload_to_gcs
↓
load_* (BigQuery)
↓
dbt_models (Cosmos)


---

## 🌌 dbt + Cosmos

### Why Cosmos?

Instead of:


1 task → dbt run


You get:


stg_orders
dim_customers
fct_sales
fct_orders


Each model becomes a task in Airflow.

---

### Configuration Example

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
📊 Transformation Layer
Staging models clean raw data
Dimension tables provide context
Fact tables store metrics

Flow:

staging → dimensions → facts
⭐ Data Modeling
Fact Table

fct_sales

item-level transactions
price, freight, total
Dimensions
dim_customers
dim_products
dim_sellers
dim_date
🧠 Why Star Schema?
reduces redundancy
improves performance
scalable
industry standard
🧪 Data Quality

Using dbt tests:

not_null
unique
relationships

Advanced:

store_failures
rejected data tracking
⚙️ Runtime Behavior
Airflow (container)
   ↓
runs Python + dbt
   ↓
calls GCP APIs
   ↓
BigQuery executes SQL
🧠 Mental Model
Airflow = orchestrator
dbt = transformation layer
BigQuery = compute engine
GCS = storage
Service account = authentication
⚠️ Common Pitfalls
wrong key path
mixing local vs container config
dbt profiles confusion
dependency conflicts
🚀 How to Run

Start Astro:

astro dev start

Trigger DAG:

olist_full_pipeline
🔥 Key Achievements
end-to-end pipeline
cloud integration
orchestration
star schema modeling
real-world debugging
📈 Future Improvements
incremental models
partitioning & clustering
CI/CD
monitoring
data quality dashboards
👨‍💻 Author

Salem — Data Engineering Project

🧠 Final Insight

Most failures in data engineering are caused