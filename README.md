# FileGuard

一款輕量級的**檔案完整性監控工具(File Integrity Monitoring, FIM)**,用於偵測指定檔案或資料夾內的未預期異動(新增 / 修改 / 刪除)。設計初衷是為了在使用 AI 輔助開發工具(Claude Code、Cursor 等)時,即時掌握專案關鍵檔案是否被意外修改。

提供 **圖形化介面(GUI,Windows)** 與 **命令列(CLI,跨平台)** 兩種使用方式。

---

## 安裝

### GUI 版本(Windows)

直接下載安裝程式,不需要安裝 Python 或任何相依套件:

1. 前往 [Releases 頁面](../../releases) 下載最新版 `FileGuard_Setup.exe`
2. 雙擊執行,依安裝精靈指示完成安裝
3. 若 Windows 跳出「SmartScreen 已封鎖此應用程式」的藍色警告畫面,這是正常現象(因為安裝程式沒有數位簽章)。點擊「其他資訊」→「仍要執行」即可繼續安裝
4. 安裝完成後,桌面與開始功能表會出現 FileGuard 捷徑

### CLI 版本(跨平台:Windows / Linux / macOS)

需要 Python 3 環境,用 `git clone` 取得原始碼後在虛擬環境中安裝:

```bash
git clone https://github.com/你的帳號/FileGuard.git
cd FileGuard

# 建立並啟用虛擬環境
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 安裝相依套件
pip install -r requirements.txt
```

> **Linux 環境提醒**:部分精簡版發行版(如 WSL)可能沒有內建 `python3-venv`,若 `python3 -m venv venv` 失敗,先執行 `sudo apt update && sudo apt install python3-venv`。另外,若專案放在 Windows 掛載磁碟(如 WSL 的 `/mnt/c/...`)下建立虛擬環境可能因權限問題失敗,建議放在 Linux 原生檔案系統路徑(如 `~/`)下操作。

---

## 功能特色

- **SQLite 持久化儲存**:
  - `events` 表:完整的歷史異動紀錄(可追溯)
  - `files` 表:每個檔案目前的雜湊狀態
  - 支援**多監控目標並存**,不同資料夾的基準線互不干擾
- **多層提醒機制**,每一層都有容錯處理,單一管道失敗不影響監控本身:
  - 系統桌面通知(不打斷操作)
  - 提示音(刪除事件)
  - **Discord Webhook**:可推送到自己的 Discord 頻道,適合背景 / 遠端主機使用情境
- **排除規則**:可自訂排除資料夾(如 `.git`、`venv`)與排除檔案樣式(如 `*.swp`、`Thumbs.db`,避免編輯器暫存檔造成誤報)
- **GUI 版本(Windows)**:
  - 資料夾選取、遞迴掃描子資料夾
  - 可自訂掃描間隔、排除資料夾、排除檔案樣式、Discord Webhook,皆可於畫面上直接設定
  - 可透過核取方塊一鍵關閉系統通知與提示音(不影響事件紀錄與 Discord Webhook 推送)
  - 即時事件清單顯示
  - 支援同時開啟多個視窗,監控不同資料夾
  - 提供正式安裝程式(桌面捷徑、開始功能表、可解除安裝)
- **CLI 版本(跨平台,Windows / Linux 皆已驗證)**:
  - 可調整掃描間隔(`--interval`)
  - 支援監控整個資料夾(遞迴掃描)或個別檔案清單,兩種模式擇一
  - Ctrl+C 優雅中斷,結束時列出本次執行的完整事件歷史
  - 依作業系統自動切換提示音與資料儲存路徑
- 完善的錯誤處理(設定檔遺失、格式錯誤、通知管道失敗等情境皆有對應提示,不會中斷監控)

---

## 專案架構

```
fileguard/
├─ main.py          # CLI 進入點(跨平台)
├─ gui.py            # GUI 進入點(customtkinter,Windows 專用)
├─ hasher.py         # SHA256 雜湊計算
├─ scanner.py        # 多檔案掃描、資料夾遞迴、排除規則
├─ database.py       # SQLite 讀寫(events / files 表,跨平台儲存路徑)
├─ config.json       # CLI 監控設定(僅 CLI 版本使用,GUI 版本設定皆透過畫面操作)
├─ requirements.txt  # 相依套件
└─ .gitignore
```

核心邏輯(`hasher.py`、`scanner.py`、`database.py`)完全與介面無關,CLI 與 GUI 共用同一套底層模組,僅在「如何呈現結果」上有所不同。

---

## 技術棧

| 用途 | 技術 |
|---|---|
| 語言 | Python 3 |
| 雜湊計算 | `hashlib`(串流讀取,避免大檔案佔用過多記憶體) |
| 資料庫 | `sqlite3`,組合主鍵 `(folder, path)` 支援多目標監控 |
| CLI 參數解析 | `argparse` |
| GUI 框架 | `customtkinter`(基於 `tkinter`) |
| 系統通知 | `plyer`(無桌面環境時自動略過並印出警告,不中斷程式) |
| 提示音效 | `winsound`(Windows)/ 終端機響鈴(Linux / macOS) |
| Webhook 通知 | `requests`(POST 至 Discord Webhook) |
| 資料儲存路徑 | `%APPDATA%`(Windows)/ `~/.config`(Linux / macOS) |
| GUI 打包 | PyInstaller + Inno Setup(產生正式安裝程式) |

---

## 授權

僅供個人學習與作品集展示使用。