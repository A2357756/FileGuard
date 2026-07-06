from hasher import calculate_sha256

def scan_files(filepaths):
    """
    輸入: ["test1.txt", "test2.txt"]
    輸出: {"test1.txt": "abc123...", "test2.txt": "def456..."}
    """
    result = {}
    for path in filepaths:
        try:
            result[path] = calculate_sha256(path)
        except FileNotFoundError:
            print(f"[ERROR] 找不到檔案: {path}")
    return result