import hashlib

def calculate_sha256(filepath):
    sha256 = hashlib.sha256()
    #用二進位機制"rb"(read binary)開啟檔案
    with open(filepath, "rb") as f:
        while True:
            data = f.read(4096)
            if data == b"":
                break
            sha256.update(data)
    return sha256.hexdigest()
