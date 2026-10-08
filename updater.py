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

def make_request(url, token, accept="application/vnd.github+json"):
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

    api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
    print("\n正在連接 GitHub 驗證並查詢最新版本...")

    try:
        req = make_request(api_url, token)
        with urllib.request.urlopen(req) as response:
            releases = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[錯誤] API 請求失敗: HTTP {e.code} - {e.reason}")
        return
    except Exception as e:
        print(f"[錯誤] 連線異常: {e}")
        return

    print(f"成功獲取 Release 清單，共找到 {len(releases)} 個 Release。")

    latest_main = None
    latest_apex = None

    for r in releases:
        tag = r.get("tag_name", "")
        if not latest_main and tag.startswith("Main-ver."):
            latest_main = r
        if not latest_apex and tag.startswith("Apex-ver."):
            latest_apex = r
        if latest_main and latest_apex:
            break

    # 建立目標資料夾 FPS-YOLO
    os.makedirs(TARGET_DIR, exist_ok=True)

    # 1. 處理 Main (原始碼 zip)
    if not latest_main:
        print("[錯誤] 找不到任何以 'Main-ver.' 開頭的 Release！")
        return

    main_tag = latest_main["tag_name"]
    print(f"\n>>> 發現最新 Main: {main_tag}")
    zip_url = f"https://api.github.com/repos/{OWNER}/{REPO}/zipball/{main_tag}"
    zip_path = "main_temp.zip"
    temp_dir = "main_temp_extract"

    print(f"正在下載 Main 原始碼至 {TARGET_DIR}...")
    try:
        req = make_request(zip_url, token)
        with urllib.request.urlopen(req) as resp, open(zip_path, "wb") as f:
            shutil.copyfileobj(resp, f)

        print(f"正在解壓縮 Main 並攤平至 {TARGET_DIR} 資料夾...")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        # GitHub zip 內層會包一層 root 資料夾，將其內容直接移至 FPS-YOLO
        inner_root = os.path.join(temp_dir, os.listdir(temp_dir)[0])
        for item in os.listdir(inner_root):
            src = os.path.join(inner_root, item)
            dst = os.path.join(TARGET_DIR, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        print(f"Main 程式碼已成功佈署至 {TARGET_DIR}！")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    # 2. 處理 Apex (模型檔)
    print("\n" + "=" * 45)
    if not latest_apex:
        print("[警告] 找不到任何以 'Apex-ver.' 開頭的 Release，跳過模型下載。")
    else:
        apex_tag = latest_apex["tag_name"]
        print(f">>> 發現最新 Apex 模型: {apex_tag}")
        assets = latest_apex.get("assets", [])
        if not assets:
            print(f"[警告] {apex_tag} 沒有附加任何檔案 (Assets)！")
        else:
            # 存放到 FPS-YOLO/Apex/src
            apex_dir = os.path.join(TARGET_DIR, "Apex", "src")
            os.makedirs(apex_dir, exist_ok=True)

            for asset in assets:
                filename = asset["name"]
                asset_url = asset["url"]
                dest_file = os.path.join(apex_dir, filename)
                print(f"正在下載模型: {filename}...")

                req = make_request(asset_url, token, accept="application/octet-stream")
                with urllib.request.urlopen(req) as resp, open(dest_file, "wb") as f:
                    shutil.copyfileobj(resp, f)

                print(f"模型已儲存至: {dest_file}")

    print(f"\n所有項目已更新完成，檔案皆已存入 {TARGET_DIR} 目錄！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[執行例外中斷] {e}")
    input("\n請按 Enter 鍵結束...")