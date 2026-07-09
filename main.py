import json
import time
import os
import argparse
import winsound
from scanner import scan_files, get_files_in_folder
import datetime
from database import init_db, log_event, get_baseline, update_file, delete_file, get_events_since
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

    watch_folder = config.get("watch_folder", "").strip()
    excluded_dirs = set(config.get("exclude_dirs", []))
    watch_files = config.get("watch_files", [])

    folder_id = watch_folder if watch_folder else os.getcwd()

    return watch_folder, excluded_dirs, watch_files, folder_id


#比對新舊基準線
def compare(folder, old, new):
    all_paths = set(old.keys()) | set(new.keys())
    events_found = False
    for path in all_paths:
        if path not in old:
            print(f"{Colors.GREEN}[CREATED] {path}{Colors.RESET}")
            log_event(folder, path, "CREATED")
            events_found = True
        elif path not in new:
            print(f"{Colors.RED}[DELETED] {path}{Colors.RESET}")
            log_event(folder, path, "DELETED")
            send_alert(path, "刪除")
            winsound.Beep(1000, 500)
            delete_file(folder, path)
            events_found = True
        elif old[path] != new[path]:
            print(f"{Colors.YELLOW}[MODIFIED] {path}{Colors.RESET}")
            log_event(folder, path, "MODIFIED")
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
def run_once(watch_folder, excluded_dirs, watch_files, folder):
    if watch_folder:
        files_to_watch = get_files_in_folder(watch_folder, excluded_dirs)
    else:
        files_to_watch = watch_files

    baseline = get_baseline(folder)
    current = scan_files(files_to_watch)

    # 關鍵檢查:如果一個檔案都沒掃到,基準線永遠無法建立,
    # 之後每一輪都會誤判成「找不到基準線」。這裡直接示警,
    # 而不是照樣印「建立完成」誤導使用者。
    if not files_to_watch:
        print(f"{Colors.RED}[警告] 監控清單是空的,請檢查 config.json 的"
              f" watch_folder / watch_files 設定是否正確。{Colors.RESET}")
        return
    if not current:
        print(f"{Colors.RED}[警告] 掃描到 0 個檔案(watch_folder="
              f"'{watch_folder}'),請確認資料夾路徑存在且裡面真的有檔案。"
              f"基準線不會被建立。{Colors.RESET}")
        return

    if not baseline:
        print(f"找不到基準線,建立中...(本次掃到 {len(current)} 個檔案)")
        print("建立完成。")
    else:
        events_found = compare(folder, baseline, current)
        if not events_found:
            print("掃描完成,目前無變化。")

    for path, sha256 in current.items():
        update_file(folder, path, sha256)

#迴圈執行
if __name__ == "__main__":
    init_db()
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parser = argparse.ArgumentParser(description="FileGuard - 檔案完整性監控工具")
    parser.add_argument("--interval", type=int, default=5, help="掃描間隔秒數(預設 5 秒)")
    args = parser.parse_args()

    watch_folder, excluded_dirs, watch_files, folder = load_config()

    print(f"開始監控,每 {args.interval} 秒掃描一次(Ctrl+C 停止)")

    try:
        while True:
            run_once(watch_folder, excluded_dirs, watch_files, folder)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n監控已停止。")
        print("\n=== 本次執行歷史事件 ===")
        events = get_events_since(folder, start_time)
        if not events:
            print("(本次執行期間無事件)")
        else:
            for timestamp, path, event_type in events:
                print(f"{timestamp} | {event_type} | {path}")