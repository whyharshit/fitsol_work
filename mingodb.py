import pymongo
import json
import os

# 1. Connection String (The %40 is the '@' in 'mukul@123')
uri = "mongodb+srv://mukul:mukul%40123@cluster0.wdxy6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(uri)

# 2. Point to the specific Database and Collection requested
db = client['carbon_scoring']
collection = db['meta_data']

# 3. Path to your specific backup folder
folder_path = './esg_outputs_backup' 

def upload_esg_backup():
    # Check if folder exists first
    if not os.path.exists(folder_path):
        print(f"❌ Error: The folder '{folder_path}' was not found.")
        return

    files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    print(f"📂 Found {len(files)} JSON files. starting upload...")

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                
                # We add the filename to the data so you know which file it came from later
                if isinstance(data, list):
                    for item in data:
                        item['source_file'] = filename
                    collection.insert_many(data)
                else:
                    data['source_file'] = filename
                    collection.insert_one(data)
                    
                print(f"✅ Uploaded: {filename}")
            except Exception as e:
                print(f"⚠️ Failed {filename}: {e}")

if __name__ == "__main__":
    upload_esg_backup()
    print("\n🚀 Upload to 'carbon_scoring.meta_data' complete.")