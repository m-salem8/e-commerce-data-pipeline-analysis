import os
import zipfile
import tempfile
import requests
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

URL = os.getenv("DATASET_URL")
BUCKET_NAME = os.getenv("GCS_BUCKET")
PROJECT_ID = os.getenv("PROJECT_ID")
GCS_PREFIX = "raw"


def validate_env():
    required = {
        "DATASET_URL": URL,
        "GCS_BUCKET": BUCKET_NAME,
        "PROJECT_ID": PROJECT_ID,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise ValueError(f"Missing environment variables: {missing}")


def download_zip(url: str, zip_path: str):
    print("Downloading dataset...")

    with requests.get(url, stream=True) as response:
        response.raise_for_status()

        with open(zip_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    print("Download complete.")


def extract_zip(zip_path: str, extract_dir: str):
    print("Extracting ZIP file...")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print("Extraction complete.")


def upload_csv_files_to_gcs(local_dir: str):
    print("Uploading CSV files to GCS...")

    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    uploaded_count = 0

    for file_name in os.listdir(local_dir):
        if file_name.endswith(".csv"):
            local_path = os.path.join(local_dir, file_name)
            gcs_path = f"{GCS_PREFIX}/{file_name}"

            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)

            print(f"Uploaded: gs://{BUCKET_NAME}/{gcs_path}")
            uploaded_count += 1

    print(f"Upload complete. Total files uploaded: {uploaded_count}")


def main():
    validate_env()

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "olist.zip")
        extract_dir = os.path.join(temp_dir, "extracted")

        os.makedirs(extract_dir, exist_ok=True)

        download_zip(URL, zip_path)
        extract_zip(zip_path, extract_dir)
        upload_csv_files_to_gcs(extract_dir)

    print("Temporary local files deleted automatically.")


if __name__ == "__main__":
    main()