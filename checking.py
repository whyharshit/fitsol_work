import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

# 1. Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
SERVICE_FILE = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE")
BUCKET_NAME = "carbon_scoring"

def verify_uploads(bucket_name):
    credentials = service_account.Credentials.from_service_account_file(SERVICE_FILE)
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)

    # Folders we want to check
    folders_to_check = ["json/", "extracted_text/"]

    print(f"--- Checking Bucket: {bucket_name} ---\n")

    for folder in folders_to_check:
        # List blobs with this specific prefix
        blobs = list(bucket.list_blobs(prefix=folder, max_results=5))
        
        if not blobs:
            print(f"❌ Folder '{folder}' NOT FOUND or is empty.")
        else:
            print(f"✅ Folder '{folder}' exists. Sample files:")
            for blob in blobs:
                # Calculate size in KB for quick reference
                size_kb = round(blob.size / 1024, 2)
                print(f"   - {blob.name} ({size_kb} KB)")
        print("-" * 30)

if __name__ == "__main__":
    verify_uploads(BUCKET_NAME)