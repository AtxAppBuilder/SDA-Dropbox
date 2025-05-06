import dropbox
from dropbox.exceptions import AuthError
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_dropbox_token():
    """
    Get Dropbox access token from user input or environment variable.
    Returns the access token as a string.
    """
    token = os.enviro.get('ACCESS_TOKEN')
    if not token:
        token = input('Enter your Dropbox access token: ')
    return token

def connect_to_dropbox(token):
    """
    Connect to Dropbox API using the provided token.
    Returns a Dropbox client object.
    """
    try:
        dbx = dropbox.Dropbox(token)
        # Check that the access token is valid
        dbx.users_get_current()
        print("Successfully connected to Dropbox!")
        return dbx
    except AuthError as e:
        print(f"Error connecting to Dropbox: {e}")
        exit(1)

def upload_file():
    pass


def has_memo_in_filename(filename):
    """
    Check if 'memo' appears in the filename (case insensitive).
    """
    return 'memo' in filename.lower()

def list_folder_contents(dbx, path):
    """
    List all files and folders in the given Dropbox path.
    Returns a list of entries.
    """
    try:
        result = dbx.files_list_folder(path)
        items = result.entries

        # Continue fetching if there are more items
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            items.extend(result.entries)
            
        return items
    except dropbox.exceptions.ApiError as e:
        print(f"Error listing folder contents: {e}")
        return []
    
def delete_file(dbx, file_path, dry_run=False):
    if dry_run:
        print(f"[DRY RUN] Would delete file: {file_path}")
        return True
    try:
        dbx.files_delete_v2(file_path)
        print(f"Deleted file: {file_path}")
        return True
    except dropbox.exceptions.ApiError as e:
        print(f"Error deleting file {file_path}: {e}")
        return False

def delete_folder_if_empty(dbx, folder_path, dry_run=False):
    contents = list_folder_contents(dbx, folder_path)
    if not contents:
        if dry_run:
            print(f"[DRY RUN] Would delete empty folder: {folder_path}")
            return True
        try:
            dbx.files_delete_v2(folder_path)
            print(f"Deleted empty folder: {folder_path}")
            return True
        except dropbox.exceptions.ApiError as e:
            print(f"Error deleting folder {folder_path}: {e}")
            return False
    return False
    

def get_folder_contents(dbx, folder_path):
    """
    Get details about all files in a folder.
    Returns a dictionary with info about memo files and other files.
    """
    items = list_folder_contents(dbx, folder_path)

    result = {
        'memo_files': [],
        'other_files': [],
        'folders': []
    }

    for item in items():
        if isinstance(item, dropbox.files.FileMetadata):
            if has_memo_in_filename(item.name):
                result['memo_files'].append(item)
            else:
                result['other_files'].append(item)

        elif isinstance(item, dropbox.files.FolderMetadata):
            result['folders'].append(item)

    return result


def process_folder(dbx, folder_path, delete_empty_folders=True, dry_run=False):
    """
    Process a folder to find and delete memo files and handle subfolders accordingly.
    """
    print(f"\nProcessing folder: {folder_path}")
    
    contents = get_folder_contents(dbx, folder_path)
    
    for file in contents['memo_files']:
        delete_file(dbx, file.path_lower, dry_run)
    
    for folder in contents['folders']:
        subfolder_path = folder.path_lower
        subfolder_contents = get_folder_contents(dbx, subfolder_path)
        
        if (subfolder_contents['memo_files'] and 
            not subfolder_contents['other_files'] and 
            not subfolder_contents['folders']):
            
            all_deleted = True
            for file in subfolder_contents['memo_files']:
                if not delete_file(dbx, file.path_lower, dry_run):
                    all_deleted = False
            if all_deleted:
                delete_folder_if_empty(dbx, subfolder_path, dry_run)
            else:
                print(f"Could not delete all memo files in {subfolder_path}, skipping folder deletion.")
        else:
            process_folder(dbx, subfolder_path, delete_empty_folders, dry_run)
    
    if delete_empty_folders and folder_path != "":
        contents_after = list_folder_contents(dbx, folder_path)
        if not contents_after:
            delete_folder_if_empty(dbx, folder_path, dry_run)

        

def main():
    """
    Main function to clean up Dropbox by removing memo files.
    """
    print("Dropbox Memo File Cleanup Tool")
    print("-----------------------------")
    
    token = get_dropbox_token()
    dbx = connect_to_dropbox(token)
    
    process_folder(dbx, "/TestCleanup", dry_run=True)  # Start with dry run on TestCleanup
    
    print("\nCleanup process completed! Set dry_run=False to perform actual deletions.")

if __name__ == "__main__":
    main()