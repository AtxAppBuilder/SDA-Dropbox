import os
import time
import logging
from pathlib import Path

# Setup logging with timestamps
logging.basicConfig(
    filename='cleanup_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Step 1
def has_memo_in_filename(filename):
    return 'memo' in filename.lower()

# Step 2
def list_folder_contents(folder_path):
    result = {
        'memo_files': [],
        'other_files': [],
        'folders': []
    }
    path = Path(folder_path)
    for item in path.iterdir():
        if item.is_file():
            if has_memo_in_filename(item.name):
                result['memo_files'].append(str(item))
            else:
                result['other_files'].append(str(item))
        elif item.is_dir():
            result['folders'].append(str(item))
    return result

# Step 3
def delete_file(file_path, dry_run=False):
    if dry_run:
        logging.info(f"[DRY RUN] Would delete file: {file_path}")
        return True
    try:
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {e}")
        return False
    
# Step 4
def delete_folder_if_empty(folder_path, dry_run=False):
    if dry_run:
        logging.info(f"[DRY RUN] Would delete empty folder: {folder_path}")
        return True
    try:
        os.rmdir(folder_path)
        logging.info(f"Deleted empty folder: {folder_path}")
        return True
    except Exception as e:
        logging.error(f"Error deleting folder {folder_path}: {e}")
        return False
    
# Step 5
def process_folder(folder_path, delete_empty_folders=True, dry_run=True):
    logging.info(f"Processing folder: {folder_path}")
    contents = list_folder_contents(folder_path)
    logging.info(f"Found {len(contents['memo_files'])} memo files, {len(contents['other_files'])} other files, and {len(contents['folders'])} folders.")
    for file in contents['memo_files']:
        logging.info(f"Memo file found: {file}")
    for folder in contents['folders']:
        logging.info(f"Subfolder found: {folder}")

    for file in contents['memo_files']:
        delete_file(file, dry_run)

    for folder in contents['folders']:
        subfolder_path = folder
        subfolder_contents = list_folder_contents(subfolder_path)
        if (len(subfolder_contents['memo_files']) == 1 and 
            not subfolder_contents['other_files'] and 
            not subfolder_contents['folders']):
            all_deleted = True
            for file in subfolder_contents['memo_files']:
                if not delete_file(file, dry_run):
                    all_deleted = False
            if all_deleted:
                delete_folder_if_empty(subfolder_path, dry_run)
            else:
                logging.info(f"Could not delete all memo files in {subfolder_path}, skipping folder deletion.")
        else:
            process_folder(subfolder_path, delete_empty_folders, dry_run)

    if delete_empty_folders and folder_path != "":
        contents_after = os.listdir(folder_path)
        if not contents_after:
            delete_folder_if_empty(folder_path, dry_run)

# Step 6
def main():
    logging.info("Local Folder Memo File Cleanup Tool started")
    print("Local Folder Memo File Cleanup Tool")
    print("---------------------------------")
    
    folder_paths = [
        "/mnt/c/sda/"    
    ]
    for folder_path in folder_paths:
        if not os.path.exists(folder_path):
            print(f"Folder {folder_path} not found. Skipping...")
            logging.error(f"Folder {folder_path} not found.")
            continue
        
        print(f"\nProcessing folder: {folder_path}")
        start_time = time.time()
        process_folder(folder_path, dry_run=True)  # Set to False to delete
        print(f"Completed in {time.time() - start_time:.2f} seconds")
    
    print("\nAnalysis and cleanup process completed! Set dry_run=False to perform actual deletions.")
    logging.info("Analysis and cleanup process completed.")

if __name__ == "__main__":
    main()