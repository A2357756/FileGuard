# FileGuard 

一款輕量級的**檔案完整性監控工具(File Integrity Monitoring, FIM)**,用於偵測指定檔案或資料夾內的未預期異動(新增 / 修改 / 刪除)。設計初衷是為了在使用 AI 輔助開發工具(Claude Code、Cursor 等)時,即時掌握專案關鍵檔案是否被意外修改。

提供 **命令列(CLI)** 與 **圖形化介面(GUI)** 兩種使用方式。

---
## 安裝

建議在虛擬環境中安裝,避免污染系統全域 Python 環境:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

---

## 使用方式

### CLI 版本

`config.json` 支援兩種監控資料選擇,兩者同時存在時,以 `watch_folder`(資料夾)優先。

```json
{
    "watch_folder": "C:/Users/SCE/Desktop/test_folder",
    "exclude_dirs": ["__pycache__", "venv", ".git"],
    "watch_files": [
    "test1.txt",
    "C:/Users/SCE/Desktop/test.txt"]
}
```

- `watch_folder`:要監控的資料夾路徑(單一字串,路徑用正斜線 `/`)
- `watch_files`:要監控的檔案，無路徑即預設為本體所在資料夾內
- `exclude_dirs`:掃描時要跳過的子資料夾名稱(陣列,可省略)
- 每輪掃描都會重新走訪資料夾,能偵測到新增的檔案
- 只監控清單中列出的檔案,不會遞迴掃描

**執行:**

1. 編輯 `config.json`,依上述任一模式設定監控目標
2. 執行:
   ```bash
   python main.py                 # 預設每 5 秒掃描一次
   python main.py --interval 10   # 自訂掃描間隔
   ```
3. 按 `Ctrl+C` 停止監控,終端機會列出本次執行期間的完整事件歷史。

### GUI 版本

```bash
python gui.py
```

1. 點擊「選擇監控資料夾」選取要監控的資料夾(會遞迴掃描所有子資料夾)
2. 視需求調整「掃描間隔」與「排除資料夾」(預設排除 `__pycache__`、`venv`、`.git`)
3. 點擊「開始監控」
4. 偵測到異動時,會跳出系統通知,並記錄在畫面下方的事件清單
5. 可同時開啟多個終端機分頁,各自執行 `python gui.py` 監控不同資料夾

---


## 功能特色

- **SHA256 雜湊比對**:透過檔案內容雜湊值判斷變化,而非單純比對修改時間,避免誤判
- **SQLite 持久化儲存**:
  - `events` 表:完整的歷史異動紀錄(可追溯)
  - `files` 表:每個檔案目前的雜湊狀態
  - 支援**多監控目標並存**,不同資料夾的基準線互不干擾
- **GUI 版本額外功能**:
  - 資料夾選取、遞迴掃描子資料夾
  - 可自訂掃描間隔、可自訂排除資料夾清單
  - 即時事件清單顯示
  - 支援同時開啟多個視窗,監控不同資料夾
- **CLI 版本額外功能**:
  - 可調整掃描間隔(`--interval`)
  - 結束時列出本次執行的完整事件歷史
  - 完善的錯誤處理(設定檔遺失、格式錯誤等情境皆有對應的中文提示)

---

## 專案架構

```
FileGuard/
├─ main.py          # CLI 進入點
├─ gui.py            # GUI 進入點(customtkinter)
├─ hasher.py         # SHA256 雜湊計算
├─ scanner.py        # 多檔案掃描
├─ database.py       # SQLite 讀寫(events / files 表)
├─ config.json       # CLI 監控清單設定
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
| 系統通知 | `plyer` |
| 提示音效 | `winsound`(Windows) |

---



## 設計上的取捨與學習紀錄

這個專案從最初預計 3 天完成的 CLI 小工具,逐步擴展為支援 GUI、多資料夾監控的完整專案。過程中幾個值得記錄的設計決策:

- **JSON → SQLite**:初期用 `baseline.json` 存基準線,隨著需要「歷史事件紀錄」與「多目標支援」等需求,改用 SQLite 的兩張表分別處理「當前狀態」與「歷史紀錄」
- **`(folder, path)` 組合主鍵**:當監控範圍(資料夾或排除清單)改變時,若沿用單一 `path` 主鍵會導致基準線與新範圍不匹配,產生大量誤判的 DELETED 事件。改用組合主鍵後,不同監控目標的基準線彼此獨立
- **`while + sleep` vs `root.after()`**:CLI 版本用阻塞式的 `while True: sleep()` 迴圈即可,但 GUI 必須改用 `tkinter` 的事件排程機制(`root.after()`),避免阻塞主事件迴圈導致視窗凍結
- **通知機制取捨**:一開始使用 `messagebox`(強制彈窗),後改為 `plyer` 系統通知(不阻塞、不打斷操作),更符合背景監控的使用情境
- **共用模組重構**:資料夾遞迴掃描邏輯(`get_files_in_folder`)最初只寫在 GUI 版本裡,後來讓 CLI 版本也支援資料夾監控時,將其搬移至 `scanner.py`,讓兩個介面共用同一份邏輯,避免重複程式碼與行為不一致

---

## 授權

僅供個人學習與作品集展示使用。