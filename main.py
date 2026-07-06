import json
from scanner import scan_files

BASELINE_FILE = "baseline.json"

#讀取基準線
def load_baseline():
    try:
        with open(BASELINE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

#儲存(覆蓋)基準線
def save_baseline(data):
    with open(BASELINE_FILE, "w") as f: #"w"寫入
        json.dump(data, f, indent=2)

#比對新舊基準線
def compare(old, new):
    all_paths = set(old.keys()) | set(new.keys())
    for path in all_paths:
        if path not in old:
            print(f"[CREATED] {path}")
        elif path not in new:
            print(f"[DELETED] {path}")
        elif old[path] != new[path]:
            print(f"[MODIFIED] {path}")

#主流程
if __name__ == "__main__":
    files_to_watch = ["test1.txt", "test2.txt"]

    baseline = load_baseline()
    current = scan_files(files_to_watch)

    if baseline is None:
        print("找不到基準線,建立中...")
        save_baseline(current)
        print("基準線建立完成。")
    else:
        print("開始比對...")
        compare(baseline, current)
        save_baseline(current)  # 更新基準線