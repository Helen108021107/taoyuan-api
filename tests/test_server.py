import asyncio
import json
from mcp.server.fastmcp import FastMCP
from server import mcp

async def test_server():
    print("=" * 60)
    print("MCP Server 功能測試")
    print("=" * 60)
    
    # 測試 1: 搜尋統計資料
    print("\n[測試 1] 搜尋 '人口' 相關資料...")
    try:
        result = await mcp.call_tool("search_statistics", arguments={"keyword": "人口"})
        data = json.loads(result[0].text)
        
        if "data" in data:
            print(f"   ✓ 搜尋成功，找到 {len(data['data'])} 筆 (顯示前 20 筆)")
            print(f"   範例: {data['data'][0]['資料名稱']}")
        else:
            print(f"   ✓ 搜尋成功，找到 {len(data)} 筆")
            print(f"   範例: {data[0]['資料名稱']}")
            
    except Exception as e:
        print(f"   ✗ 搜尋失敗: {e}")

    # 測試 2: 獲取統計數據 (預設年份)
    print("\n[測試 2] 獲取 '現住人口數' 數據 (預設 2024-2025)...")
    # 假設 tid=0001, cid=0002, sid=000005 是現住人口數 (從搜尋結果得知)
    # 這裡我們直接用已知的有效 ID 測試
    tid, cid, sid = "0001", "0002", "000005" 
    
    try:
        result = await mcp.call_tool("get_statistics_data", arguments={"tid": tid, "cid": cid, "sid": sid})
        data = json.loads(result[0].text)
        
        if isinstance(data, list) and len(data) > 0:
            print(f"   ✓ 獲取成功，共 {len(data)} 筆數據")
            print(f"   範例數據: {str(data[0])[:100]}...")
        else:
            print(f"   ⚠️ 回傳資料為空或格式不如預期: {str(data)[:100]}")
            
    except Exception as e:
        print(f"   ✗ 獲取失敗: {e}")

    # 測試 3: 獲取統計數據 (指定年份)
    print("\n[測試 3] 獲取 '現住人口數' 數據 (指定 2023-2024)...")
    try:
        result = await mcp.call_tool("get_statistics_data", arguments={
            "tid": tid, 
            "cid": cid, 
            "sid": sid,
            "begin_year": "2023",
            "end_year": "2024"
        })
        data = json.loads(result[0].text)
        
        if isinstance(data, list) and len(data) > 0:
            print(f"   ✓ 獲取成功，共 {len(data)} 筆數據")
            # 檢查年份是否正確 (假設回傳資料有年份欄位，通常是 'time_name' 或類似)
            print(f"   範例數據: {str(data[0])[:100]}...")
        else:
            print(f"   ⚠️ 回傳資料為空或格式不如預期")
            
    except Exception as e:
        print(f"   ✗ 獲取失敗: {e}")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_server())
