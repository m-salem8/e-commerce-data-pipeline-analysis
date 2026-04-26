from datetime import datetime
from airflow.decorators import dag
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from include.scripts.data_ingestion_to_gcs import main


PROJECT_ID = "olist-494419"
BUCKET_NAME = "ecommerce-olist_de"
BQ_DATASET = "olist_raw"

FILES_TO_TABLES = {
    "raw/olist_customers_dataset.csv": "customers",
    "raw/olist_geolocation_dataset.csv": "geolocation",
    "raw/olist_order_items_dataset.csv": "order_items",
    "raw/olist_order_payments_dataset.csv": "order_payments",
#    "raw/olist_order_reviews_dataset.csv": "order_reviews",
    "raw/olist_orders_dataset.csv": "orders",
    "raw/olist_products_dataset.csv": "products",
    "raw/olist_sellers_dataset.csv": "sellers",
    "raw/product_category_name_translation.csv": "product_category_translation",
}


@dag(
    dag_id="load_olist_gcs_to_bigquery",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
)
def load_olist_gcs_to_bigquery():

    # Step 1: upload data to GCS (runs once)
    ingestion_task = PythonOperator(
        task_id="upload_to_gcs",
        python_callable=main,
    )

    # Step 2: create all load tasks
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

    # Step 3: set dependency (runs once → then all loads)
    ingestion_task >> load_tasks


load_olist_gcs_to_bigquery()