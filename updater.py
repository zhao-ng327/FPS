import os
import sys
import json
import shutil
import zipfile
import urllib.request
import urllib.error

OWNER = "zhao-ng327"
REPO = "FPS-YOLO"
TARGET_DIR = "FPS-YOLO"  # 目標解壓縮與專案目錄

def makeRequest(url, token, accept="application/vnd.github+json"):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "AutoUpdater",
        "Accept": accept,
    }
    return urllib.request.Request(url, headers=headers)

def main():
    print("=" * 45)
    print("        專案更新與自動部署工具")
    print("=" * 45 + "\n")

    token = input("請輸入你的 GitHub Personal Access Token: ").strip()
    if not token:
        print("[錯誤] Token 不能為空！")
        return

    apiUrl = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
    print("\n正在連接 GitHub 驗證並查詢最新版本...")

    try:
        req = makeRequest(apiUrl, token)
        with urllib.request.urlopen(req) as response:
            releases = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[錯誤] API 請求失敗: HTTP {e.code} - {e.reason}")
        return
    except Exception as e:
        print(f"[錯誤] 連線異常: {e}")
        return

    print(f"成功獲取 Release 清單，共找到 {len(releases)} 個 Release。")

    latestMain = None

    for r in releases:
        tag = r.get("tag_name", "")
        tagLower = tag.lower()
        if tagLower.startswith("main-ver"):
            latestMain = r
            break

    # 建立目標資料夾 FPS-YOLO
    os.makedirs(TARGET_DIR, exist_ok=True)

    # 處理 Main (原始碼 zip)
    if not latestMain:
        print("[錯誤] 找不到任何以 'Main-ver' 開頭的 Release！")
        return

    mainTag = latestMain["tag_name"]
    print(f"\n>>> 發現最新 Main: {mainTag}")
    zipUrl = f"https://api.github.com/repos/{OWNER}/{REPO}/zipball/{mainTag}"
    zipPath = "main_temp.zip"
    tempDir = "main_temp_extract"

    print(f"正在下載 Main 原始碼至 {TARGET_DIR}...")
    try:
        req = makeRequest(zipUrl, token)
        with urllib.request.urlopen(req) as resp, open(zipPath, "wb") as f:
            shutil.copyfileobj(resp, f)

        print(f"正在解壓縮 Main 並攤平至 {TARGET_DIR} 資料夾...")
        if os.path.exists(tempDir):
            shutil.rmtree(tempDir)
        with zipfile.ZipFile(zipPath, "r") as zf:
            zf.extractall(tempDir)

        # GitHub zip 內層會包一層 root 資料夾，將其內容直接移至 FPS-YOLO
        innerRoot = os.path.join(tempDir, os.listdir(tempDir)[0])
        for item in os.listdir(innerRoot):
            src = os.path.join(innerRoot, item)
            dst = os.path.join(TARGET_DIR, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        print(f"Main 程式碼已成功佈署至 {TARGET_DIR}！")
    finally:
        if os.path.exists(zipPath):
            os.remove(zipPath)
        if os.path.exists(tempDir):
            shutil.rmtree(tempDir)

    # 建立 License.txt 並寫入 token
    licensePath = os.path.join(TARGET_DIR, "License.txt")
    with open(licensePath, "w", encoding="utf-8") as f:
        f.write(token)
    print(f"已建立 Authorization License 於 {licensePath}")

    print(f"\n更新完成，檔案皆已存入 {TARGET_DIR} 目錄！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[執行例外中斷] {e}")
    input("\n請按 Enter 鍵結束...")