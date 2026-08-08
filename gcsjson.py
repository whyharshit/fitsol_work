import os
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

# ---------------------------------------------------
# 1. Configuration
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SERVICE_FILE = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE")
BUCKET_NAME = "carbon_scoring"

# Folders
SOURCE_FOLDER = BASE_DIR / "esg_outputs"
NEW_GCS_FOLDER = "esg_json_uploads"  # The new folder inside your bucket

# ---------------------------------------------------
# 2. Initialize GCS
# ---------------------------------------------------
credentials = service_account.Credentials.from_service_account_file(SERVICE_FILE)
storage_client = storage.Client(credentials=credentials)
bucket = storage_client.bucket(BUCKET_NAME)

# ---------------------------------------------------
# 3. Upload Logic
# ---------------------------------------------------
def upload_json_files():
    # Ensure source directory exists
    if not SOURCE_FOLDER.exists():
        print(f"Aborting: The folder {SOURCE_FOLDER} does not exist.")
        return

    # List all .json files
    json_files = list(SOURCE_FOLDER.glob("*.json"))
    
    if not json_files:
        print("No JSON files found to upload.")
        return

    print(f"Found {len(json_files)} files. Starting upload to '{NEW_GCS_FOLDER}/'...")

    for file_path in json_files:
        # Create GCS path: esg_json_uploads/filename.json
        gcs_path = f"{NEW_GCS_FOLDER}/{file_path.name}"
        blob = bucket.blob(gcs_path)

        # Skip if exists (Idempotency)
        if blob.exists():
            print(f"SKIPPED: {file_path.name} already exists in GCS.")
            continue

        try:
            blob.upload_from_filename(
                str(file_path),
                content_type="application/json"
            )
            print(f"SUCCESS: {file_path.name} -> gs://{BUCKET_NAME}/{gcs_path}")
        except Exception as e:
            print(f"FAILED: {file_path.name} | Error: {e}")

# ---------------------------------------------------
# 4. Main
# ---------------------------------------------------
if __name__ == "__main__":
    upload_json_files()