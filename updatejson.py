import os
import json
from pathlib import Path
import logging

# =====================================================
# LOGGING SETUP
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('metadata_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION
# =====================================================
OUTPUT_DIR = Path("esg_outputs")
BACKUP_DIR = Path("esg_outputs_backup")

# =====================================================
# BACKUP FUNCTION
# =====================================================
def backup_files():
    """Create backup of all JSON files before modification"""
    if BACKUP_DIR.exists():
        logger.warning(f"Backup directory already exists: {BACKUP_DIR}")
        response = input("Backup exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Backup skipped.")
            return False
    
    BACKUP_DIR.mkdir(exist_ok=True)
    
    json_files = list(OUTPUT_DIR.glob("*_esg.json"))
    logger.info(f"Backing up {len(json_files)} files...")
    
    for json_file in json_files:
        backup_file = BACKUP_DIR / json_file.name
        with open(json_file, 'r') as f:
            data = json.load(f)
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    logger.info(f"✅ Backup completed: {BACKUP_DIR}")
    return True

# =====================================================
# FIX METADATA IN JSON FILE
# =====================================================
def fix_metadata(json_file: Path) -> bool:
    """Remove tier and industry fields from metadata"""
    try:
        # Read JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        if 'metadata' not in data:
            logger.warning(f"No metadata found in {json_file.name}")
            return False
        
        metadata = data['metadata']
        company_name = metadata.get('company_name', 'Unknown')
        removed_fields = []
        
        # Remove 'tier' field if exists
        if 'tier' in metadata:
            del metadata['tier']
            removed_fields.append('tier')
        
        # Remove 'industry' field if exists
        if 'industry' in metadata:
            del metadata['industry']
            removed_fields.append('industry')
        
        if removed_fields:
            logger.info(f"Removed {', '.join(removed_fields)} from {company_name}")
        else:
            logger.debug(f"No fields to remove from {company_name}")
        
        # Write back to file
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing {json_file.name}: {e}")
        return False

# =====================================================
# MAIN EXECUTION
# =====================================================
def main():
    """Main execution function"""
    
    logger.info("="*60)
    logger.info("ESG METADATA FIX TOOL")
    logger.info("="*60)
    logger.info("This tool will remove 'tier' and 'industry' fields from all JSON files")
    logger.info("="*60)
    
    # Check if output directory exists
    if not OUTPUT_DIR.exists():
        logger.error(f"Output directory not found: {OUTPUT_DIR}")
        return
    
    # Get all JSON files
    json_files = list(OUTPUT_DIR.glob("*_esg.json"))
    if not json_files:
        logger.error(f"No JSON files found in {OUTPUT_DIR}")
        return
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Create backup
    logger.info("\n📦 Creating backup...")
    if not backup_files():
        logger.error("Backup failed. Exiting for safety.")
        return
    
    # Process all JSON files
    logger.info(f"\n🔧 Processing {len(json_files)} files...")
    logger.info("="*60)
    
    successful = 0
    failed = 0
    
    for idx, json_file in enumerate(json_files, 1):
        logger.info(f"[{idx}/{len(json_files)}] Processing: {json_file.name}")
        
        if fix_metadata(json_file):
            successful += 1
        else:
            failed += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*60)
    logger.info(f"Total files: {len(json_files)}")
    logger.info(f"✅ Successfully updated: {successful}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📦 Backup location: {BACKUP_DIR}")
    logger.info(f"📋 Detailed log: metadata_fix.log")
    logger.info("="*60)
    
    if failed > 0:
        logger.warning(f"\n⚠️  {failed} files failed to update. Check metadata_fix.log for details")
    
    # Option to restore from backup
    logger.info("\n💡 To restore from backup if needed:")
    logger.info(f"   Copy files from '{BACKUP_DIR}' back to '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()