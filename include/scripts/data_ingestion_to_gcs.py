"""
E-Commerce Data Pipeline - Data Ingestion Script

Purpose:
--------
This script downloads a ZIP dataset from a remote URL,
extracts the CSV files locally in a temporary directory,
and uploads them to Google Cloud Storage (GCS).

Pipeline Stage:
---------------
External Source -> Local Temp Storage -> GCS Raw Layer

Main Responsibilities:
----------------------
1. Validate required environment variables
2. Download dataset ZIP file
3. Extract CSV files
4. Upload CSVs to GCS raw layer
5. Automatically clean temporary files

Author:
-------
Mahmoud Salem
"""

import os
import zipfile
import tempfile
import requests

from dotenv import load_dotenv
from google.cloud import storage


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================
# Loads variables from .env file into memory
# Example:
# DATASET_URL=...
# GCS_BUCKET=...
# PROJECT_ID=...
# =========================================================
load_dotenv()


# =========================================================
# GLOBAL CONFIGURATION
# =========================================================

# Dataset ZIP download URL
URL = os.getenv("DATASET_URL")

# Google Cloud Storage bucket name
BUCKET_NAME = os.getenv("GCS_BUCKET")

# Google Cloud project ID
PROJECT_ID = os.getenv("PROJECT_ID")

# Folder/prefix inside GCS bucket
# Files will be uploaded to:
# gs://bucket-name/raw/filename.csv
GCS_PREFIX = "raw"

# Path to service account credentials
# Used mainly inside Docker/Airflow container
SERVICE_ACCOUNT_PATH = "/usr/local/airflow/include/gcp/airflow-sa.json"


# =========================================================
# ENVIRONMENT VALIDATION
# =========================================================
# Ensures all required environment variables exist
# before pipeline execution starts.
# =========================================================
def validate_env():

    required_env_vars = {
        "DATASET_URL": URL,
        "GCS_BUCKET": BUCKET_NAME,
        "PROJECT_ID": PROJECT_ID,
    }

    # Collect missing environment variables
    missing_vars = [
        name for name, value in required_env_vars.items() if not value
    ]

    # Stop execution if any variable is missing
    if missing_vars:
        raise ValueError(
            f"Missing environment variables: {missing_vars}"
        )


# =========================================================
# DOWNLOAD DATASET ZIP FILE
# =========================================================
# Downloads dataset in streaming mode to avoid
# loading entire file into memory.
#
# Parameters:
#   url      -> dataset source URL
#   zip_path -> local output path
# =========================================================
def download_zip(url: str, zip_path: str):

    print("Downloading dataset...")

    # Stream download for memory efficiency
    with requests.get(url, stream=True) as response:

        # Raise error if request failed
        response.raise_for_status()

        # Write file in binary chunks
        with open(zip_path, "wb") as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:
                    file.write(chunk)

    print("Download complete.")


# =========================================================
# EXTRACT ZIP FILE
# =========================================================
# Extracts downloaded ZIP archive into local directory.
#
# Parameters:
#   zip_path    -> ZIP file path
#   extract_dir -> extraction destination
# =========================================================
def extract_zip(zip_path: str, extract_dir: str):

    print("Extracting ZIP file...")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print("Extraction complete.")


# =========================================================
# CREATE GCS STORAGE CLIENT
# =========================================================
# Creates authenticated Google Cloud Storage client.
#
# Logic:
#   - If service account file exists:
#       use explicit credentials
#   - Otherwise:
#       use default environment authentication
#
# Returns:
#   storage.Client
# =========================================================
def get_storage_client():

    # Use service account authentication
    if os.path.exists(SERVICE_ACCOUNT_PATH):

        return storage.Client.from_service_account_json(
            SERVICE_ACCOUNT_PATH,
            project=PROJECT_ID,
        )

    # Fallback to default authentication
    return storage.Client(project=PROJECT_ID)


# =========================================================
# UPLOAD CSV FILES TO GCS
# =========================================================
# Uploads all CSV files from extracted directory
# into GCS raw layer.
#
# Parameters:
#   local_dir -> directory containing CSV files
# =========================================================
def upload_csv_files_to_gcs(local_dir: str):

    print("Uploading CSV files to GCS...")

    # Create GCS client
    client = get_storage_client()

    # Connect to bucket
    bucket = client.bucket(BUCKET_NAME)

    uploaded_count = 0

    # Iterate through extracted files
    for file_name in os.listdir(local_dir):

        # Skip non-CSV files
        if not file_name.endswith(".csv"):
            continue

        # Full local file path
        local_path = os.path.join(local_dir, file_name)

        # Destination path inside bucket
        gcs_path = f"{GCS_PREFIX}/{file_name}"

        # Create blob object
        blob = bucket.blob(gcs_path)

        # Upload file to GCS
        blob.upload_from_filename(local_path)

        print(f"Uploaded: gs://{BUCKET_NAME}/{gcs_path}")

        uploaded_count += 1

    print(
        f"Upload complete. Total files uploaded: {uploaded_count}"
    )


# =========================================================
# MAIN PIPELINE EXECUTION
# =========================================================
# Orchestrates the complete ingestion workflow:
#
# 1. Validate configuration
# 2. Create temporary workspace
# 3. Download dataset
# 4. Extract ZIP contents
# 5. Upload CSV files to GCS
# 6. Auto-delete temporary files
# =========================================================
def main():

    # Ensure required environment variables exist
    validate_env()

    # Create temporary directory
    # Automatically deleted after execution
    with tempfile.TemporaryDirectory() as temp_dir:

        # Local ZIP path
        zip_path = os.path.join(temp_dir, "olist.zip")

        # Extraction folder path
        extract_dir = os.path.join(temp_dir, "extracted")

        # Create extraction directory
        os.makedirs(extract_dir, exist_ok=True)

        # Pipeline steps
        download_zip(URL, zip_path)

        extract_zip(zip_path, extract_dir)

        upload_csv_files_to_gcs(extract_dir)

    print("Temporary local files deleted automatically.")


# =========================================================
# SCRIPT ENTRY POINT
# =========================================================
# Ensures script only runs directly and not when imported.
# =========================================================
if __name__ == "__main__":
    main()