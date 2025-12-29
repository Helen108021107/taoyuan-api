import requests
import json
import urllib3

# 1. 關閉 SSL 安全警告 (這是關鍵，因為桃園政府憑證在 Python 內預設不被信任)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 您提供的目標網址
target_url = "https://statisticsinfo.tycg.gov.tw/TaoyuanSTYB/RestfulAPI/GetStaticData.aspx"
params = {
    "tid": "0005",      # 資料庫：桃園市重要統計速報
    "cid": "0002",      # 類別：(您嘗試測試的類別)
    "sid": "000003",    # 項目
    "begin": "2024",
    "end": "2024",
    "type": "JSON"
}

print(f"正在測試連線: {target_url}")
print(f"參數: {params}")
print("-" * 30)

try:
    # 2. 發送請求 (加上 verify=False 是為了繞過政府網站 SSL 錯誤)
    # 3. 加上 User-Agent 偽裝成瀏覽器，防止被防火牆擋
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(target_url, params=params, verify=False, headers=headers, timeout=10)
    
    print(f"HTTP 狀態碼: {response.status_code}")
    print(f"最終網址: {response.url}")
    print("-" * 30)
    
    if response.status_code == 200:
        content = response.text.strip()
        print(f"原始回傳長度: {len(content)} 字元")
        
        if len(content) == 0:
            print("❌ 結果：伺服器回傳空字串。")
            print("推測原因：該 tid/cid 組合下沒有資料，或者年份區間無數據。")
        else:
            try:
                data = response.json()
                print("✅ 結果：成功抓取 JSON！")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print("⚠️ 結果：回傳了資料，但不是 JSON 格式。")
                print(f"內容預覽: {content[:200]}...")
    else:
        print("❌ 結果：連線失敗。")

except Exception as e:
    print(f"❌ 發生錯誤: {e}")