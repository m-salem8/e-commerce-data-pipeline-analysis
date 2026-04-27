from datetime import datetime

from airflow.decorators import dag
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

from cosmos import DbtTaskGroup
from cosmos.config import ProjectConfig, ProfileConfig, ExecutionConfig

from include.scripts.data_ingestion_to_gcs import main


PROJECT_ID = "olist-494419"
BUCKET_NAME = "ecommerce-olist_de"
BQ_DATASET = "olist_raw"

DBT_PROJECT_PATH = "/usr/local/airflow/dbt/olist_dbt"
DBT_EXECUTABLE_PATH = "/usr/local/airflow/.local/bin/dbt"

FILES_TO_TABLES = {
    "raw/olist_customers_dataset.csv": "customers",
    "raw/olist_geolocation_dataset.csv": "geolocation",
    "raw/olist_order_items_dataset.csv": "order_items",
    "raw/olist_order_payments_dataset.csv": "order_payments",
#    "raw/olist_order_reviews_dataset.csv": "order_reviews",
    "raw/olist_orders_dataset.csv": "orders",
    "raw/olist_products_dataset.csv": "products",
    "raw/olist_sellers_dataset.csv": "sellers",
}


@dag(
    dag_id="olist_full_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@monthly",
    catchup=False,
    tags=["olist", "gcs", "bigquery", "dbt", "cosmos"],
)
def olist_full_pipeline():

    upload_to_gcs = PythonOperator(
        task_id="upload_to_gcs",
        python_callable=main,
    )

    load_tasks = []

    for gcs_file, table_name in FILES_TO_TABLES.items():
        load_task = GCSToBigQueryOperator(
            task_id=f"load_{table_name}",
            bucket=BUCKET_NAME,
            source_objects=[gcs_file],
            destination_project_dataset_table=f"{PROJECT_ID}.{BQ_DATASET}.{table_name}",
            source_format="CSV",
            skip_leading_rows=1,
            autodetect=True,
            write_disposition="WRITE_TRUNCATE",
            create_disposition="CREATE_IF_NEEDED",
            gcp_conn_id="google_cloud_default",
        )

        load_tasks.append(load_task)

    dbt_models = DbtTaskGroup(
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

    upload_to_gcs >> load_tasks >> dbt_models


olist_full_pipeline()