import json
import time
import argparse
from scanner import scan_files
from database import init_db, log_event, get_baseline, update_file
from plyer import notification

class Colors:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

#讀取config
def load_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("[錯誤] 找不到 config.json,請先建立設定檔並指定要監控的檔案。")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        print(f"[錯誤] config.json 格式錯誤: {e}")
        print("請檢查 JSON 語法是否正確(例如逗號、引號是否完整)。")
        raise SystemExit(1)

    return config["watch_files"]


#比對新舊基準線
def compare(old, new):
    all_paths = set(old.keys()) | set(new.keys())
    events_found = False
    for path in all_paths:
        #檔案是新增的
        if path not in old:
            print(f"[CREATED] {path}")
            log_event(path, "CREATED")
            send_alert(path, "新增")
            events_found = True
        #檔案是被刪除
        elif path not in new:
            print(f"[DELETED] {path}")
            log_event(path, "DELETED")
            send_alert(path, "刪除")
            events_found = True
        #檔案是被修改(hash值不同)
        elif old[path] != new[path]:
            print(f"[MODIFIED] {path}")
            log_event(path, "MODIFIED")
            send_alert(path, "修改")
            events_found = True
    return events_found

#plyer模組用來發送桌面通知
def send_alert(path, action):
    notification.notify(
        title="檔案異動警告",
        message=f"{path} 被{action}",
        timeout=10
    )

#主要執行函式
def run_once(files_to_watch):
    baseline = get_baseline()
    current = scan_files(files_to_watch)
    if not baseline:
        print("找不到基準線,建立中...")
        print("建立完成。")
    else:
        compare(baseline, current)
        print("掃描完成,目前無變化。")
    for path, sha256 in current.items():
        update_file(path, sha256)
    
#迴圈執行
if __name__ == "__main__":
    init_db() 
    parser = argparse.ArgumentParser(description="AI Workspace Guardian - 檔案完整性監控工具")
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="掃描間隔秒數(預設 5 秒)"
    )
    args = parser.parse_args()
    files_to_watch = load_config()
    print(f"開始監控,每 {args.interval} 秒掃描一次(Ctrl+C 停止)")
    try:
        while True:
            run_once(files_to_watch)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n監控已停止。")
