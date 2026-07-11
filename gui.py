import os
import sys
import winsound
import requests
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from plyer import notification
from scanner import scan_files, get_files_in_folder


ctk.set_appearance_mode("light")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import init_db, log_event, get_baseline, update_file, delete_file, clear_files_for_folder

# ===== Color Palette =====

# Brand
PRIMARY = "#0F766E"
PRIMARY_HOVER = "#115E59"
PRIMARY_ACTIVE = "#134E4A"

NAVY = "#0F172A"
TEAL_LIGHT = "#CCFBF1"
BLUE_ACCENT = "#2563EB"

# Background
BG = "#F8FAFC"
CARD = "#FFFFFF"

# Text
TEXT = "#0F172A"
TEXT_LIGHT = "#64748B"
TITLE = "#0F172A"

# Border
BORDER = "#CBD5E1"

# Status
SUCCESS = "#10B981"
WARNING = "#F59E0B"
ERROR = "#DC2626"

def send_discord_webhook(webhook_url, path, action):
    if not webhook_url:
        return
    try:
        requests.post(
            webhook_url,
            json={"content": f"🚨 **檔案異動警告**\n`{path}` 被{action}"},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        print(f"[警告] Webhook 發送失敗: {e}")


def compare(folder, old, new):
    all_paths = set(old.keys()) | set(new.keys())
    events_found = False
    webhook_url = webhook_var.get().strip()
    sound_notify_enabled = sound_notify_var.get()

    for path in all_paths:
        if path not in old:
            log_event(folder, path, "CREATED")
            event_listbox.insert(0, f"[CREATED] {path}")
            events_found = True
        elif path not in new:
            log_event(folder, path, "DELETED")
            delete_file(folder, path)
            if sound_notify_enabled:
                winsound.Beep(1000, 500)
                notification.notify(
                    title="檔案異動警告",
                    message=f"{path} 被刪除",
                    timeout=10
                )
            send_discord_webhook(webhook_url, path, "刪除")
            event_listbox.insert(0, f"[DELETED] {path}")
            events_found = True
        elif old[path] != new[path]:
            log_event(folder, path, "MODIFIED")
            if sound_notify_enabled:
                notification.notify(
                    title="檔案異動警告",
                    message=f"{path} 被修改",
                    timeout=10
                )
            send_discord_webhook(webhook_url, path, "修改")
            event_listbox.insert(0, f"[MODIFIED] {path}")
            events_found = True
    return events_found

def scan_once():
    folder = folder_path.get()
    excluded_dirs = {name.strip() for name in exclude_var.get().split(",") if name.strip()}
    excluded_patterns = [p.strip() for p in pattern_var.get().split(",") if p.strip()]
    files_to_watch = get_files_in_folder(folder, excluded_dirs, excluded_patterns)
    baseline = get_baseline(folder)
    current = scan_files(files_to_watch)

    if not baseline:
        status_label.configure(text="● 建立基準線中...", text_color=WARNING)
    else:
        compare(folder, baseline, current)
        status_label.configure(text="● 監控中", text_color=SUCCESS)

    for path, sha256 in current.items():
        update_file(folder, path, sha256)

def scheduled_scan():
    global scan_job
    scan_once()
    interval_ms = interval_var.get() * 1000
    scan_job = root.after(interval_ms, scheduled_scan)

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_path.set(folder)
        start_btn.configure(state="normal")

def start_monitoring():
    folder = folder_path.get()
    # 不再自動清空基準線:只有資料庫中完全沒有該資料夾的紀錄時
    # (例如第一次監控這個資料夾,或使用者手動重置),才會重建基準線。
    # 這樣「開始監控」可以重複按、程式可以重開,只要 guardian.db 還在,
    # 基準線就會延續,不會每次都被清掉重建。
    status_label.configure(text="● 監控中", text_color=SUCCESS)
    start_btn.configure(state="disabled")
    stop_btn.configure(state="normal")
    choose_btn.configure(state="disabled")
    interval_entry.configure(state="disabled")
    exclude_entry.configure(state="disabled")
    pattern_entry.configure(state="disabled")
    webhook_entry.configure(state="disabled")
    sound_notify_checkbox.configure(state="disabled")
    scheduled_scan()

def reset_baseline():
    folder = folder_path.get()
    if folder and folder != "尚未選擇資料夾":
        clear_files_for_folder(folder)
        status_label.configure(text="● 基準線已重置,下次掃描將重建", text_color=WARNING)
        event_listbox.insert(0, f"[系統] 已手動重置「{folder}」的基準線")

def stop_monitoring():
    global scan_job
    if scan_job is not None:
        root.after_cancel(scan_job)
        scan_job = None
    status_label.configure(text="● 已停止", text_color=ERROR)
    start_btn.configure(state="normal")
    stop_btn.configure(state="disabled")
    choose_btn.configure(state="normal")
    interval_entry.configure(state="normal")
    exclude_entry.configure(state="normal")
    pattern_entry.configure(state="normal")
    webhook_entry.configure(state="disabled")
    sound_notify_checkbox.configure(state="normal")


init_db()
scan_job = None

root = ctk.CTk()
root.title("FileGuard")
root.geometry("450x600")
root.configure(fg_color=BG)
root.iconbitmap("fileguard_icon.ico")

header = ctk.CTkFrame(
    root,
    fg_color=NAVY,
    corner_radius=0,
    height=55
)

header.pack(
    fill="x"
)
header.pack_propagate(False)

title_label = ctk.CTkLabel(
    header,
    text="🛡  FileGuard",
    text_color="white",
    font=("Segoe UI", 22, "bold")
)

title_label.pack(
    anchor="w",
    padx=20,
    pady=(12, 0)
)

pattern_var = tk.StringVar()
pattern_var.set("*.swp, *.swo, *~, .DS_Store, Thumbs.db")

pattern_frame = ctk.CTkFrame(root, fg_color="transparent")
pattern_frame.pack(pady=5)

pattern_label = ctk.CTkLabel(
    pattern_frame, text="排除檔案樣式:",
    text_color=TEXT_LIGHT, font=("Segoe UI", 12)
)
pattern_label.pack(side="left")

pattern_entry = ctk.CTkEntry(
    pattern_frame, textvariable=pattern_var, width=220,
    fg_color=CARD, border_color=BORDER, text_color=TEXT, corner_radius=8
)
pattern_entry.pack(side="left", padx=5)


webhook_var = tk.StringVar()

webhook_frame = ctk.CTkFrame(root, fg_color="transparent")
webhook_frame.pack(pady=5)

webhook_label = ctk.CTkLabel(
    webhook_frame, text="Discord Webhook:",
    text_color=TEXT_LIGHT, font=("Segoe UI", 12)
)
webhook_label.pack(side="left")

webhook_entry = ctk.CTkEntry(
    webhook_frame, textvariable=webhook_var, width=220,
    placeholder_text="選填,貼上你的 Webhook 網址",
    fg_color=CARD, border_color=BORDER, text_color=TEXT, corner_radius=8
)
webhook_entry.pack(side="left", padx=5)

sound_notify_var = tk.BooleanVar()
sound_notify_var.set(True)  # 預設開啟

sound_notify_checkbox = ctk.CTkCheckBox(
    root, text="啟用系統通知與提示音",
    variable=sound_notify_var,
    text_color=TEXT, font=("Segoe UI", 12),
    fg_color=PRIMARY, hover_color=PRIMARY_HOVER
)
sound_notify_checkbox.pack(pady=5)


folder_path = tk.StringVar()
folder_path.set("尚未選擇資料夾")

choose_btn = ctk.CTkButton(
    root, text="選擇監控資料夾", command=choose_folder,
    corner_radius=10, height=38,
    fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color="white",
    font=("Segoe UI", 12)
)
choose_btn.pack(pady=10)

label = ctk.CTkLabel(
    root, textvariable=folder_path, wraplength=350,
    text_color=TEXT, font=("Segoe UI", 12)
)
label.pack(pady=10)

btn_frame = ctk.CTkFrame(root, fg_color="transparent")
btn_frame.pack(pady=5)



start_btn = ctk.CTkButton(
    btn_frame, text="開始監控", command=start_monitoring, state="disabled",
    corner_radius=10, height=36,
    fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color="white",
    font=("Segoe UI", 12)
)
start_btn.pack(side="left", padx=5)

stop_btn = ctk.CTkButton(
    btn_frame, text="停止監控", command=stop_monitoring, state="disabled",
    corner_radius=10, height=36,
    fg_color="white", hover_color="#EEF4FF",
    border_width=1, border_color=PRIMARY, text_color=PRIMARY,
    font=("Segoe UI", 12)
)
stop_btn.pack(side="left", padx=5)

reset_btn = ctk.CTkButton(
    btn_frame, text="重置基準線", command=reset_baseline,
    corner_radius=10, height=36,
    fg_color="white", hover_color="#FFF3E0",
    border_width=1, border_color=WARNING, text_color=WARNING,
    font=("Segoe UI", 12)
)
reset_btn.pack(side="left", padx=5)

interval_var = tk.IntVar()
interval_var.set(5)

interval_frame = ctk.CTkFrame(root, fg_color="transparent")
interval_frame.pack(pady=5)

interval_label = ctk.CTkLabel(
    interval_frame, text="掃描間隔(秒):",
    text_color=TEXT_LIGHT, font=("Segoe UI", 12)
)
interval_label.pack(side="left")

interval_entry = ctk.CTkEntry(
    interval_frame, textvariable=interval_var, width=55,
    fg_color=CARD, border_color=BORDER, text_color=TEXT, corner_radius=8
)
interval_entry.pack(side="left", padx=5)

exclude_var = tk.StringVar()
exclude_var.set("__pycache__, venv, .git")

exclude_frame = ctk.CTkFrame(root, fg_color="transparent")
exclude_frame.pack(pady=5)

exclude_label = ctk.CTkLabel(
    exclude_frame, text="排除資料夾:",
    text_color=TEXT_LIGHT, font=("Segoe UI", 12)
)
exclude_label.pack(side="left")

exclude_entry = ctk.CTkEntry(
    exclude_frame, textvariable=exclude_var, width=220,
    fg_color=CARD, border_color=BORDER, text_color=TEXT, corner_radius=8
)
exclude_entry.pack(side="left", padx=5)


status_label = ctk.CTkLabel(
    root, text="● 尚未開始",
    font=("Segoe UI", 14, "bold"), text_color=TEXT_LIGHT
)
status_label.pack(pady=10, fill="x")

log_label = ctk.CTkLabel(
    root, text="事件紀錄",
    font=("Segoe UI", 12, "bold"), text_color=TITLE
)
log_label.pack(anchor="w", padx=18, pady=(10, 4))

event_listbox = tk.Listbox(
    root, width=50, height=8,
    bg="#FFFFFF", fg=TEXT,
    selectbackground=PRIMARY, selectforeground="white",
    borderwidth=1, highlightthickness=1, highlightbackground=BORDER,
    relief="solid", font=("Segoe UI", 10)
)
event_listbox.pack(pady=10, padx=15, fill="both", expand=True)

root.mainloop()