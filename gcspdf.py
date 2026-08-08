import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------
# 1. Configuration
# ---------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Local Source
LOCAL_TEXT_DIR = os.path.join(BASE_DIR, "extracted_text_local")

# GCS Target
SERVICE_FILE = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE")
BUCKET_NAME = "carbon_scoring"
GCS_DEST_FOLDER = "extracted_text"  # Folder name inside the bucket

# ---------------------------------------------------
# 2. Initialize GCS Client
# ---------------------------------------------------
if not SERVICE_FILE or not os.path.exists(SERVICE_FILE):
    print(f"Error: Service account file not found at {SERVICE_FILE}")
    exit()

credentials = service_account.Credentials.from_service_account_file(SERVICE_FILE)
storage_client = storage.Client(credentials=credentials)
bucket = storage_client.bucket(BUCKET_NAME)

# ---------------------------------------------------
# 3. Upload Logic
# ---------------------------------------------------
def upload_to_gcs():
    if not os.path.exists(LOCAL_TEXT_DIR):
        print(f"Error: Local folder {LOCAL_TEXT_DIR} does not exist!")
        return

    # Get list of all .txt files in the local folder
    files = [f for f in os.listdir(LOCAL_TEXT_DIR) if f.endswith(".txt")]
    
    print(f"Found {len(files)} files to upload to gs://{BUCKET_NAME}/{GCS_DEST_FOLDER}/")

    for filename in tqdm(files, desc="Uploading"):
        local_path = os.path.join(LOCAL_TEXT_DIR, filename)
        gcs_blob_path = f"{GCS_DEST_FOLDER}/{filename}"
        
        blob = bucket.blob(gcs_blob_path)
        
        try:
            # Optional: Skip if already exists in GCS
            # if blob.exists(): continue
            
            blob.upload_from_filename(local_path)
        except Exception as e:
            print(f"\nFailed to upload {filename}: {e}")

if __name__ == "__main__":
    upload_to_gcs()
    print("\nUpload complete!")