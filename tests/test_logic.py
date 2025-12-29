import pandas as pd
import requests
import json
import os

# 模擬 Server 的核心邏輯
class MockServer:
    def __init__(self):
        self.df = pd.DataFrame()
        self.load_data()

    def load_data(self):
        data_file = "data/statistics.csv"
        if os.path.exists(data_file):
            try:
                self.df = pd.read_csv(data_file)
                print(f"Loaded {len(self.df)} records")
            except Exception as e:
                print(f"Error loading data: {e}")
        else:
            print(f"Data file not found: {data_file}")

    def search_statistics(self, keyword, category=None):
        if self.df.empty:
            return "Error: Database not loaded."
        
        mask = self.df['資料名稱'].str.contains(keyword, case=False, na=False)
        if category:
            mask &= self.df['所屬類別'].str.contains(category, case=False, na=False)
            
        results = self.df[mask].copy()
        columns = ['所屬資料庫', '所屬類別', '資料名稱', 'tid', 'cid', 'sid']
        results = results[columns]
        
        if len(results) > 20:
            return json.dumps({
                "message": f"Found {len(results)} results, showing top 20",
                "data": results.head(20).to_dict(orient='records')
            }, ensure_ascii=False, indent=2)
        
        return json.dumps(results.to_dict(orient='records'), ensure_ascii=False, indent=2)

    def get_statistics_data(self, tid, cid, sid, begin_year="2024", end_year="2025"):
        url = "https://statisticsinfo.tycg.gov.tw/TaoyuanSTYB/RestfulAPI/GetStaticData.aspx"
        params = {
            "tid": tid,
            "cid": cid,
            "sid": sid,
            "begin": begin_year,
            "end": end_year,
            "type": "JSON"
        }
        
        print(f"Requesting URL: {url}")
        print(f"Params: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error fetching data: {str(e)}"

def test_logic():
    print("=" * 60)
    print("MCP Server 核心邏輯測試")
    print("=" * 60)
    
    server = MockServer()
    
    # 測試 1: 搜尋
    print("\n[測試 1] 搜尋 '人口'...")
    result = server.search_statistics("人口")
    data = json.loads(result)
    
    # 處理兩種回傳格式
    if isinstance(data, dict) and "data" in data:
        items = data["data"]
        print(f"   ✓ 搜尋成功，找到 {len(items)} 筆 (顯示前 20)")
    else:
        items = data
        print(f"   ✓ 搜尋成功，找到 {len(items)} 筆")
        
    if len(items) > 0:
        first_item = items[0]
        print(f"   範例: {first_item['資料名稱']}")
        print(f"   ID: tid={first_item['tid']}, cid={first_item['cid']}, sid={first_item['sid']}")
        
        # 測試 2: 獲取數據 (使用搜尋到的第一個結果)
        print("\n[測試 2] 獲取數據 (預設年份)...")
        tid = str(first_item['tid']).zfill(4) # 確保格式正確
        cid = str(first_item['cid']).zfill(4)
        sid = str(first_item['sid']).zfill(6)
        
        data_result = server.get_statistics_data(tid, cid, sid)
        try:
            stats_data = json.loads(data_result)
            if isinstance(stats_data, list) and len(stats_data) > 0:
                print(f"   ✓ 獲取成功，共 {len(stats_data)} 筆數據")
                print(f"   範例數據: {str(stats_data[0])[:100]}...")
            else:
                print(f"   ⚠️ 回傳資料為空: {str(stats_data)[:100]}")
        except:
            print(f"   ✗ 解析失敗: {data_result[:100]}")

        # 測試 3: 獲取數據 (指定年份)
        print("\n[測試 3] 獲取數據 (指定 2023-2024)...")
        data_result = server.get_statistics_data(tid, cid, sid, begin_year="2023", end_year="2024")
        try:
            stats_data = json.loads(data_result)
            if isinstance(stats_data, list) and len(stats_data) > 0:
                print(f"   ✓ 獲取成功，共 {len(stats_data)} 筆數據")
            else:
                print(f"   ⚠️ 回傳資料為空")
        except:
            print(f"   ✗ 解析失敗")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    test_logic()
