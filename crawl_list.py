import requests
import pandas as pd
import os
import concurrent.futures
import urllib3
import time

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 原始檔與輸出檔
ORIGINAL_CSV = os.path.join(BASE_DIR, "data", "statistics.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "statistics_full.csv")

BASE_URL = "https://statisticsinfo.tycg.gov.tw/TaoyuanSTYB/RestfulAPI/GetStaticData.aspx"

# 設定掃描範圍
# 根據您的發現，tid=0005 裡面有 cid=0002，所以我們要加強掃描
TIDS = ["0001", "0002", "0003", "0004", "0005"]
CIDS = [f"{i:04d}" for i in range(1, 25)]  # 掃描 0001~0024 類別
SIDS = [f"{i:06d}" for i in range(1, 40)]  # 掃描每個類別的前 40 個項目

def check_url(tid, cid, sid):
    """測試單一組合是否有效"""
    params = {
        "tid": tid, "cid": cid, "sid": sid,
        "begin": "2023", "end": "2024", "type": "JSON"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 設定 timeout 為 2 秒，加快掃描速度
        response = requests.get(BASE_URL, params=params, headers=headers, verify=False, timeout=2)
        
        # 只要不是空的且狀態是 200，就視為有效
        if response.status_code == 200 and len(response.text.strip()) > 5:
            try:
                data = response.json()
                # 排除空陣列 []
                if isinstance(data, list) and len(data) > 0:
                    # 嘗試抓取標題，通常是 JSON Key 的一部分，或是我們只能標記它是「未知項目」
                    first_row = data[0]
                    # 簡易拼湊一個名稱，讓您可以搜尋到
                    name_guess = f"[自動發現] 項目_{tid}_{cid}_{sid}"
                    
                    # 嘗試從資料內容找線索 (有些資料會有 'Item' 欄位)
                    if 'Item' in first_row: name_guess = first_row['Item']
                    
                    print(f"✅ 發現資料: tid={tid} cid={cid} sid={sid} | 預覽: {str(first_row)[:30]}...")
                    
                    return {
                        "所屬資料庫": f"資料庫_{tid}",
                        "tid": tid,
                        "所屬類別": f"類別_{cid}",
                        "cid": cid,
                        "資料名稱": name_guess,
                        "sid": sid,
                        "統計資料檔案格式": response.url
                    }
            except:
                pass
    except:
        pass
    return None

def main():
    print(f"🚀 開始 Antigravity 爬蟲掃描... (目標: {OUTPUT_CSV})")
    print("這將會掃描數千個組合，請稍候...")
    
    new_records = []
    
    # 併發執行掃描
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = []
        for tid in TIDS:
            for cid in CIDS:
                for sid in SIDS:
                    futures.append(executor.submit(check_url, tid, cid, sid))
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                new_records.append(result)

    print(f"\n✅ 掃描完成！共發現 {len(new_records)} 筆有效資料。")

    # 合併舊資料
    all_data = []
    if os.path.exists(ORIGINAL_CSV):
        try:
            old_df = pd.read_csv(ORIGINAL_CSV)
            # 統一欄位型態
            old_df['tid'] = old_df['tid'].astype(str).str.zfill(4)
            old_df['cid'] = old_df['cid'].astype(str).str.zfill(4)
            old_df['sid'] = old_df['sid'].astype(str).str.zfill(6)
            all_data.append(old_df)
            print("已載入原始 CSV 資料。")
        except Exception as e:
            print(f"原始 CSV 讀取失敗: {e}")

    if new_records:
        new_df = pd.DataFrame(new_records)
        all_data.append(new_df)

    if all_data:
        # 合併並移除重複 (優先保留原本有的)
        final_df = pd.concat(all_data)
        # 根據 ID 去除重複
        final_df.drop_duplicates(subset=['tid', 'cid', 'sid'], keep='first', inplace=True)
        
        # 存檔
        final_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        print(f"🎉 完整清單已儲存至: {OUTPUT_CSV}")
        print("現在請重新啟動您的 MCP Server (server.py)，它將會讀取這個新檔案。")
    else:
        print("⚠️ 沒發現任何資料，請檢查網路。")

if __name__ == "__main__":
    main()