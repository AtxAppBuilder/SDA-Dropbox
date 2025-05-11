import os
import logging
from pathlib import Path
import dropbox
from dotenv import load_dotenv
from dropbox.exceptions import ApiError

logging.basicConfig(filename='cleanup_log.txt', level=logging.INFO)

load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

dbx = dropbox.Dropbox(ACCESS_TOKEN)


####################################################################################################
#Initialize dropbox client
try:
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    # Test authentication
    dbx.users_get_current_account()
    logging.info("Dropbox API authentication successful.")
except Exception as e:
    logging.error(f"Dropbox API authentication failed: {e}")
    raise Exception("Failed to authenticate with Dropbox API. Check ACCESS_TOKEN.")


####################################################################################################

def has_memo_in_filename(filename):
    return 'memo' in filename.lower()


####################################################################################################

def list_folder_contents(folder_path):
    result = {
        'memo_files': [],
        'other_files': [],
        'folders': []
    }
    
    try:
        # Convert local path to Dropbox path (e.g., /mnt/c/sda/TestFolder1 to /TestFolder1)
        # Assumes folders are under ~/Dropbox/
        dropbox_path = dropbox_path.strip('/')
        if not dropbox_path:
            dropbox_path = ''
        else:
            dropbox_path = f"/{dropbox_path}"

        # Use files_list_folder to get all entries
        entries = []
        response = dbx.files_list_folder(dropbox_path)
        entries.extend(response.entries)

        # Handle pagination
        while response.has_more:
            response = dbx.files_list_folder_continue(response.cursor)
            entries.extend(response.entries)

        # Process entries
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                if has_memo_in_filename(entry.name):
                    result['memo_files'].append(entry.path_display)
                else:
                    result['other_files'].append(entry.path_display)
            elif isinstance(entry, dropbox.files.FolderMetadata):
                result['folders'].append(entry.path_display)

        logging.info(f"Found {len(result['memo_files'])} memo files, {len(result['other_files'])} other files, and {len(result['folders'])} folders in {dropbox_path}.")
        return result

    except ApiError as e:
        logging.error(f"Dropbox API error listing contents of {dropbox_path}: {e}")
        return result
    
##############################################################################

# Delete a file in Dropbox using the API.

def delete_file(dropbox_path, dry_run=False):
    if dry_run:
        logging.info(f"[DRY RUN] Would delete file: {dropbox_path}")
        return True
    try:
        dbx.files_delete_v2(dropbox_path)
        logging.info(f"Deleted file in Dropbox: {dropbox_path}")
        return True
    except ApiError as e:
        logging.error(f"Error deleting file {dropbox_path}: {e}")
        return False

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
    

####################################################################################################

# Delete a Dropbox folder if it's empty using the API.

def delete_folder_if_empty(dropbox_path, dry_run=False):
    if dry_run:
        logging.info(f"[DRY RUN] Would delete empty folder: {dropbox_path}")
        return True
    try:
        # Check if folder is empty
        response = dbx.files_list_folder(dropbox_path)
        if not response.entries:  # Folder is empty
            dbx.files_delete_v2(dropbox_path)
            logging.info(f"Deleted empty folder in Dropbox: {dropbox_path}")
            return True
        else:
            logging.info(f"Folder {dropbox_path} is not empty, skipping deletion.")
            return False
    except ApiError as e:
        logging.error(f"Error deleting folder {dropbox_path}: {e}")
        return False
    

####################################################################################################

# Process a Dropbox folder, deleting memo files and optionally empty subfolders.

def process_folder(dropbox_path, delete_empty_folders=True, dry_run=True):
    logging.info(f"Processing Dropbox folder: {dropbox_path}")
    contents = list_folder_contents(dropbox_path, dry_run)
    logging.info(f"Found {len(contents['memo_files'])} memo files, {len(contents['other_files'])} other files, and {len(contents['folders'])} folders.")
    for file in contents['memo_files']:
        logging.info(f"Memo file found: {file}")
    for folder in contents['folders']:
        logging.info(f"Subfolder found: {folder}")

    # Delete memo files
    for file in contents['memo_files']:
        delete_file(file, dry_run)

    # Process subfolders
    for folder in contents['folders']:
        subfolder_path = folder
        subfolder_contents = list_folder_contents(subfolder_path, dry_run)
        if (subfolder_contents['memo_files'] and 
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

    # Delete the folder if empty (after processing)
    if delete_empty_folders and dropbox_path != "":
        try:
            response = dbx.files_list_folder(dropbox_path)
            if not response.entries:  # Folder is empty
                delete_folder_if_empty(dropbox_path, dry_run)
        except ApiError as e:
            logging.error(f"Error checking if {dropbox_path} is empty: {e}")

def main():
    logging.info("Dropbox Folder Memo File Cleanup Tool started")
    print("Dropbox Folder Memo File Cleanup Tool")
    print("---------------------------------")
    
    # Define Dropbox folder paths (relative to Dropbox root)
    # Assumes these folders are in ~/Dropbox/ (e.g., ~/Dropbox/TestFolder1)
    folder_paths = [
        "TestFolder1",
        "TestFolder2",
        "AnotherFolder"
    ]
    
    for folder_path in folder_paths:
        try:
            # Verify folder exists in Dropbox
            dbx.files_get_metadata(f"/{folder_path}")
        except ApiError as e:
            print(f"Folder {folder_path} not found in Dropbox. Skipping...")
            logging.error(f"Folder {folder_path} not found in Dropbox: {e}")
            continue
        
        print(f"\nProcessing Dropbox folder: {folder_path}")
        process_folder(folder_path, dry_run=True)  # Set to False to delete
    
    print("\nAnalysis and cleanup process completed! Set dry_run=False to perform actual deletions.")
    logging.info("Analysis and cleanup process completed.")

if __name__ == "__main__":
    main()