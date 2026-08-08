import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

# 1. Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SERVICE_FILE = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE")
BUCKET_NAME = "carbon_scoring"

def list_all_folders_and_files():
    try:
        credentials = service_account.Credentials.from_service_account_file(SERVICE_FILE)
        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(BUCKET_NAME)

        # First, identify the folders (prefixes)
        all_blobs = bucket.list_blobs(prefix="", delimiter="/")
        list(all_blobs) # Initialize prefixes
        
        folders = all_blobs.prefixes
        
        if not folders:
            print(f"No folders found in {BUCKET_NAME}.")
            return

        print(f"=== FULL INVENTORY FOR BUCKET: {BUCKET_NAME} ===\n")

        for folder in folders:
            print(f"📁 FOLDER: {folder}")
            
            # List files inside this specific folder
            inner_blobs = bucket.list_blobs(prefix=folder)
            file_count = 0
            
            for blob in inner_blobs:
                # Skip the folder placeholder itself
                if blob.name == folder:
                    continue
                
                # Print the first 5 files as a sample, then just count the rest
                if file_count < 5:
                    print(f"  📄 {blob.name.split('/')[-1]}")
                elif file_count == 5:
                    print(f"  ... and more files")
                
                file_count += 1
            
            print(f"  📊 Total in {folder}: {file_count} files\n")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_folders_and_files()