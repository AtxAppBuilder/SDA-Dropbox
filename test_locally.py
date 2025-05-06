#!/usr/bin/env python3
import os

def has_memo_in_filename(filename):
    """
    Check if 'memo' appears in the filename (case insensitive).
    """
    return 'memo' in filename.lower()

def list_folder_contents(path):
    """
    List all files and folders in the given local path.
    Returns a list of entries.
    """
    entries = []
    for entry in os.scandir(path if path else '.'):
        entries.append(entry)
    return entries

def delete_file(file_path, dry_run=False):
    """
    Delete a file or simulate deletion in dry run mode.
    """
    if dry_run:
        print(f"[DRY RUN] Would delete file: {file_path}")
        return True
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
        return True
    except OSError as e:
        print(f"Error deleting file {file_path}: {e}")
        return False

def delete_folder_if_empty(folder_path, dry_run=False):
    """
    Delete a folder if it's empty or simulate deletion in dry run mode.
    """
    if not os.path.exists(folder_path):
        return False
    if not any(os.scandir(folder_path)):
        if dry_run:
            print(f"[DRY RUN] Would delete empty folder: {folder_path}")
            return True
        try:
            os.rmdir(folder_path)
            print(f"Deleted empty folder: {folder_path}")
            return True
        except OSError as e:
            print(f"Error deleting folder {folder_path}: {e}")
            return False
    return False

def get_folder_contents(path):
    """
    Get details about all files in a folder.
    Returns a dictionary with info about memo files and other files.
    """
    items = list_folder_contents(path)
    
    result = {
        'memo_files': [],
        'other_files': [],
        'folders': []
    }
    
    for item in items:
        if item.is_file():
            if has_memo_in_filename(item.name):
                result['memo_files'].append(item.path)
            else:
                result['other_files'].append(item.path)
        elif item.is_dir():
            result['folders'].append(item.path)
    
    return result

def process_folder(path, delete_empty_folders=True, dry_run=False):
    """
    Process a folder to find and delete memo files and handle subfolders accordingly.
    """
    print(f"\nProcessing folder: {path}")
    
    contents = get_folder_contents(path)
    
    for file_path in contents['memo_files']:
        delete_file(file_path, dry_run)
    
    for folder_path in contents['folders']:
        subfolder_contents = get_folder_contents(folder_path)
        
        if (subfolder_contents['memo_files'] and 
            not subfolder_contents['other_files'] and 
            not subfolder_contents['folders']):
            
            all_deleted = True
            for file_path in subfolder_contents['memo_files']:
                if not delete_file(file_path, dry_run):
                    all_deleted = False
            if all_deleted:
                delete_folder_if_empty(folder_path, dry_run)
            else:
                print(f"Could not delete all memo files in {folder_path}, skipping folder deletion.")
        else:
            process_folder(folder_path, delete_empty_folders, dry_run)
    
    if delete_empty_folders and path != os.getcwd():
        contents_after = list_folder_contents(path)
        if not contents_after:
            delete_folder_if_empty(path, dry_run)

def main():
    """
    Main function to clean up a local folder by removing memo files.
    """
    print("Local Folder Memo File Cleanup Tool")
    print("---------------------------------")
    
    test_folder = "/mnt/c/sda/test_folder"
    if not os.path.exists(test_folder):
        print(f"Test folder {test_folder} does not exist. Creating it.")
        os.makedirs(test_folder)
    
    process_folder(test_folder, dry_run=True)
    
    print("\nCleanup process completed! Set dry_run=False to perform actual deletions.")

if __name__ == "__main__":
    main()