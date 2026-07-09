import os
from hasher import calculate_sha256

def scan_files(filepaths):
    result = {}
    for path in filepaths:
        try:
            result[path] = calculate_sha256(path)
        except FileNotFoundError:
            print(f"[ERROR] 找不到檔案: {path}")
    return result

def get_files_in_folder(folder, excluded_dirs=None):
    if excluded_dirs is None:
        excluded_dirs = set()
    file_list = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            file_list.append(full_path)
    return file_list