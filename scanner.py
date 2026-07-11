import os
from hasher import calculate_sha256
import fnmatch


EXCLUDED_PATTERNS = ["*.swp", "*.swo", "*~", ".DS_Store", "Thumbs.db"]

def scan_files(filepaths):
    result = {}
    for path in filepaths:
        try:
            result[path] = calculate_sha256(path)
        except FileNotFoundError:
            print(f"[ERROR] 找不到檔案: {path}")
    return result

def is_excluded_file(filename, excluded_patterns):
    for pattern in excluded_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False

def get_files_in_folder(folder, excluded_dirs=None, excluded_patterns=None):
    if excluded_dirs is None:
        excluded_dirs = set()
    if excluded_patterns is None:
        excluded_patterns = []

    file_list = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
        for filename in filenames:
            if is_excluded_file(filename, excluded_patterns):
                continue
            full_path = os.path.join(dirpath, filename)
            file_list.append(full_path)
    return file_list
