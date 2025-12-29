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
                # 確保 ID 欄位是字串格式，避免讀取時變成數字 (例如 0001 變成 1)
                self.df['tid'] = self.df['tid'].astype(str).str.zfill(4)
                self.df['cid'] = self.df['cid'].astype(str).str.zfill(4)
                self.df['sid'] = self.df['sid'].astype(str).str.zfill(6)
                print(f"Loaded {len(self.df)} records")
            except Exception as e:
                print(f"Error loading data: {e}")
        else:
            print(f"Data file not found: {data_file}")

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
        
        print(f"Requesting: {url}")
        print(f"Params: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            try:
                data = response.json()
                return json.dumps(data, ensure_ascii=False, indent=2)
            except:
                print(f"Response Text (First 500 chars): {response.text[:500]}")
                return "Error: Invalid JSON response"
                
        except Exception as e:
            return f"Error fetching data: {str(e)}"

def test_logic():
    print("=" * 60)
    print("MCP Server 核心邏輯測試 (修正版)")
    print("=" * 60)
    
    server = MockServer()
    
    # 測試: 獲取 '市境界' 數據 (已知有效 ID)
    print("\n[測試] 獲取 '市境界' 數據 (tid=0001, cid=0001, sid=000001)...")
    
    # 測試預設年份
    print("\n--- 預設年份 (2024-2025) ---")
    data_result = server.get_statistics_data("0001", "0001", "000001")
    try:
        if data_result.startswith("Error"):
            print(f"   ✗ {data_result}")
        else:
            stats_data = json.loads(data_result)
            if isinstance(stats_data, list) and len(stats_data) > 0:
                print(f"   ✓ 獲取成功，共 {len(stats_data)} 筆數據")
                print(f"   範例: {str(stats_data[0])[:100]}...")
            else:
                print(f"   ⚠️ 回傳資料為空: {data_result[:100]}")
    except Exception as e:
        print(f"   ✗ 解析失敗: {e}")

    # 測試指定年份
    print("\n--- 指定年份 (2023-2024) ---")
    data_result = server.get_statistics_data("0001", "0001", "000001", begin_year="2023", end_year="2024")
    try:
        if data_result.startswith("Error"):
            print(f"   ✗ {data_result}")
        else:
            stats_data = json.loads(data_result)
            if isinstance(stats_data, list) and len(stats_data) > 0:
                print(f"   ✓ 獲取成功，共 {len(stats_data)} 筆數據")
            else:
                print(f"   ⚠️ 回傳資料為空")
    except Exception as e:
        print(f"   ✗ 解析失敗: {e}")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    test_logic()
