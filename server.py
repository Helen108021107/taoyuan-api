import pandas as pd
import requests
import json
import os
import sys
import numpy as np
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any

# Conditional imports for Dual Mode
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

import urllib3

# 1. 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FULL_CSV = os.path.join(BASE_DIR, "data", "statistics_full.csv")
ORIG_CSV = os.path.join(BASE_DIR, "data", "statistics.csv")
DATA_FILE = FULL_CSV if os.path.exists(FULL_CSV) else ORIG_CSV

df = pd.DataFrame()

# 載入資料庫 (Global)
try:
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['tid'] = df['tid'].astype(str).str.zfill(4)
        df['cid'] = df['cid'].astype(str).str.zfill(4)
        df['sid'] = df['sid'].astype(str).str.zfill(6)
        sys.stderr.write(f"Loaded {len(df)} records from {DATA_FILE}\n")
    else:
        sys.stderr.write(f"Warning: Data file not found at {DATA_FILE}\n")
except Exception as e:
    sys.stderr.write(f"Error loading data: {e}\n")

# --- Core Logic Functions (Independent of MCP/FastAPI) ---

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def get_default_period():
    """計算預設最近 5 年 (不含當年，因為資料通常有滯後性)"""
    now_year = datetime.now().year
    end_year = now_year
    begin_year = end_year - 4 # 例如 2025 -> 2021~2025 (5年)
    return str(begin_year), str(end_year)   

def _fetch_data_internal(tid: str, cid: str, sid: str, begin: Optional[str], end: Optional[str]):
    # 若無指定日期，則使用預設區間
    if not begin or not end:
        def_begin, def_end = get_default_period()
        begin = begin or def_begin
        end = end or def_end

    url = "https://statisticsinfo.tycg.gov.tw/TaoyuanSTYB/RestfulAPI/GetStaticData.aspx"
    params = {"tid": tid, "cid": cid, "sid": sid, "begin": begin, "end": end, "type": "JSON"}
    try:
        response = requests.get(url, params=params, headers=get_headers(), timeout=30, verify=False)
        if response.status_code != 200: return None
        text = response.text.strip()
        if not text: return None
        data = response.json()
        return data
    except:
        return None

def _search_statistics_internal(keyword: str) -> str:
    if df.empty: return "Error: Database not loaded."
    mask = df['資料名稱'].astype(str).str.contains(keyword, case=False, na=False) | \
           df['所屬類別'].astype(str).str.contains(keyword, case=False, na=False)
    results = df[mask].copy()
    if len(results) == 0: return "No results found."
    columns = ['所屬資料庫', '所屬類別', '資料名稱', 'tid', 'cid', 'sid']
    display_cols = [c for c in columns if c in results.columns]
    return json.dumps(results[display_cols].head(20).to_dict(orient='records'), ensure_ascii=False, indent=2)

def _get_statistics_data_internal(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None) -> str:
    # 1. 取得完整資料
    data = _fetch_data_internal(tid, cid, sid, begin, end)
    
    if data is None:
        return "Error: Unable to fetch data or empty response."
    
    # 2. 檢查資料類型與大小
    if isinstance(data, list):
        count = len(data)
        
        # 設定安全閥值：如果超過 50 筆，就不要全部回傳
        if count > 50:
            preview = data[:5] # 只取前 5 筆
            
            non_ascii_msg = f"⚠️ 資料量過大 (共 {count} 筆)，為避免對話崩潰，僅顯示前 5 筆預覽。"
            safe_response = {
                "status": "success",
                "message": non_ascii_msg,
                "instruction": "請使用 'analyze_statistics_report' 工具來進行完整數據的統計分析，不要直接讀取原始資料。",
                "preview_data": preview
            }
            return json.dumps(safe_response, ensure_ascii=False, indent=2)

    # 3. 如果資料量很小，就正常回傳全部
    return json.dumps(data, ensure_ascii=False, indent=2)

def _generate_dashboard_html_internal(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None) -> str:
    data = _fetch_data_internal(tid, cid, sid, begin, end)
    if not data: return "Error: No Data Found from API."
    
    try:
        html_path = os.path.join(BASE_DIR, "index.html")
        if not os.path.exists(html_path):
            return "Error: Dashboard template (index.html) not found."
            
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        injection = f"window.DASHBOARD_DATA = {json.dumps(data, ensure_ascii=False)};"
        
        if "window.DASHBOARD_DATA = null;" in html_content:
            final_html = html_content.replace("window.DASHBOARD_DATA = null;", injection)
        else:
            final_html = html_content.replace('<script src="script.js"></script>', f'<script>{injection}</script><script src="script.js"></script>')

        output_filename = f"dashboard_{tid}_{cid}_{sid}.html"
        output_path = os.path.join(BASE_DIR, output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)
            
        return f"Dashboard generated. Open this file to view: {output_path}"

    except Exception as e:
        return f"Error creating dashboard: {str(e)}"

def _analyze_statistics_report_internal(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None) -> str:
    data = _fetch_data_internal(tid, cid, sid, begin, end)
    
    if not data or not isinstance(data, list) or len(data) == 0:
        return "無法獲取數據，無法進行分析。"

    section_2_info = "" 
    section_3_info = "" 
    section_4_info = "" 
    total_count = len(data)

    try:
        df_temp = pd.DataFrame(data)
        cols = df_temp.columns.tolist()
        label_col = next((c for c in cols if '年' in c or '月' in c or '別' in c or '名稱' in c or '區' in c), cols[0])
        
        numeric_cols = []
        for c in cols:
            if c == label_col: continue
            try:
                df_temp[c] = pd.to_numeric(df_temp[c])
                numeric_cols.append(c)
            except: pass
            
        target_col = numeric_cols[0] if numeric_cols else None

        if target_col:
            is_total = df_temp[label_col].astype(str).str.strip() == '桃園市'
            
            if is_total.any():
                total_row = df_temp[is_total].iloc[0]
                sum_val = total_row[target_col]
                df_calc = df_temp[~is_total].copy()
                total_msg = "(已自動排除「桃園市」總計列)"
            else:
                sum_val = df_temp[target_col].sum()
                df_calc = df_temp.copy()
                total_msg = ""
            
            if df_calc.empty:
                df_calc = df_temp.copy()

            mean_val = df_calc[target_col].mean()
            max_row = df_calc.loc[df_calc[target_col].idxmax()]
            min_row = df_calc.loc[df_calc[target_col].idxmin()]
            
            growth_txt = ""
            if len(df_calc) >= 2 and ('年' in label_col or '月' in label_col):
                start_val = df_calc[target_col].iloc[0]
                end_val = df_calc[target_col].iloc[-1]
                if start_val != 0:
                    growth = ((end_val - start_val) / start_val) * 100
                    growth_txt = f"本期間總體成長率為 {growth:.2f}%"
            
            section_2_info = f"""
            - 資料總筆數: {total_count} 筆 {total_msg}
            - 分析主體欄位: {target_col}
            - 數值總計: {sum_val:,.0f}
            - 平均水準: {mean_val:,.2f}
            - 極值: 最高為 {max_row[label_col]} ({max_row[target_col]})，最低為 {min_row[label_col]} ({min_row[target_col]})
            - {growth_txt}
            """

            if len(df_calc) >= 3:
                x = np.arange(len(df_calc))
                y = df_calc[target_col].values
                slope, intercept = np.polyfit(x, y, 1)
                
                p = np.poly1d([slope, intercept])
                yhat = p(x)
                ybar = np.sum(y)/len(y)
                ssreg = np.sum((yhat-ybar)**2)
                sstot = np.sum((y - ybar)**2)
                r_squared = ssreg / sstot if sstot != 0 else 0
                
                trend_desc = "呈現上升趨勢" if slope > 0 else "呈現下降趨勢"
                
                section_3_info += f"""
                1. 趨勢檢定 (Trend Analysis)：
                   - 統計方法：採用簡單線性迴歸模型 (Simple Linear Regression)。
                   - 分析結果：迴歸斜率 (Slope) 為 {slope:.4f}，決定係數 (R-squared) 為 {r_squared:.4f}。
                   - 解讀：數據整體{trend_desc} (R平方值越接近1代表趨勢越明顯)。
                """
            
            if len(numeric_cols) >= 2:
                corr_matrix = df_calc[numeric_cols].corr(method='pearson')
                corr_target = corr_matrix[target_col].drop(target_col)
                if not corr_target.empty:
                    best_corr_col = corr_target.abs().idxmax()
                    best_corr_val = corr_target[best_corr_col]
                    section_3_info += f"""
                2. 相關係數分析 (Correlation Analysis)：
                   - 統計方法：採用皮爾森積動差相關係數。
                   - 分析結果：'{target_col}' 與 '{best_corr_col}' 之相關係數為 {best_corr_val:.4f}。
                   """

            top10 = df_calc.nlargest(10, target_col)
            top10_str = "\\n".join([f"   - 第{i+1}名: {row[label_col]} (數值: {row[target_col]})" for i, row in top10.iterrows()])
            section_4_info = f"數值最高的熱點區域/時間 (前10名):\\n{top10_str}"

    except Exception as e:
        section_2_info = f"計算錯誤: {str(e)}"

    data_sample = data[:5] if len(data) > 5 else data
    data_sample_str = json.dumps(data_sample, ensure_ascii=False)

    summary = f"""
### 數據統計摘要 (Statistical Summary)

**1. 基本資訊 (Basic Info)**
- 資料來源: {tid}-{cid}-{sid}
- 時間範圍: {begin} ~ {end}
- 總筆數: {total_count}

**2. 現況描述 (Descriptive Stats)**
- 分析主體: {section_2_info.strip()}

**3. 統計檢定 (Statistical Analysis)**
{section_3_info.strip() if section_3_info else "- 無足夠數據進行趨勢/相關性分析。"}

**4. 熱點排行 (Top 10 Hotspots)**
{section_4_info.strip()}

**5. 原始資料範例 (Sample Data - Top 5)**
{data_sample_str}
    """
    
    return summary

# --- Mode 1: MCP Server Setup ---

def run_mcp_server():
    if not FastMCP:
        print("Error: 'mcp' package not installed. Cannot run in MCP mode.")
        sys.exit(1)

    mcp = FastMCP("Taoyuan Statistics")

    @mcp.tool()
    def search_statistics(keyword: str) -> str:
        return _search_statistics_internal(keyword)

    @mcp.tool()
    def get_statistics_data(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None) -> str:
        return _get_statistics_data_internal(tid, cid, sid, begin, end)

    @mcp.tool()
    def generate_dashboard_html(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None) -> str:
        return _generate_dashboard_html_internal(tid, cid, sid, begin, end)

    @mcp.tool()
    def analyze_statistics_report(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None) -> str:
        return _analyze_statistics_report_internal(tid, cid, sid, begin, end)

    print("Starting MCP Server...", file=sys.stderr)
    mcp.run()

# --- Mode 2: FastAPI Server Setup ---

def run_api_server():
    try:
        from fastapi import FastAPI, Response
        from fastapi.responses import PlainTextResponse
        import uvicorn
    except ImportError:
        print("Error: fastapi or uvicorn not installed. Please run 'pip install fastapi uvicorn'")
        sys.exit(1)

    app = FastAPI(title="Taoyuan Statistics API")

    @app.get("/search_statistics")
    def api_search_statistics(keyword: str):
        result = _search_statistics_internal(keyword)
        # Parse JSON string back to object for proper API JSON response
        try:
            return json.loads(result)
        except:
            return result

    @app.get("/get_statistics_data")
    def api_get_statistics_data(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None):
        result = _get_statistics_data_internal(tid, cid, sid, begin, end)
        try:
            return json.loads(result)
        except:
            return result

    @app.get("/generate_dashboard_html")
    def api_generate_dashboard_html(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None):
        return {"message": _generate_dashboard_html_internal(tid, cid, sid, begin, end)}

    @app.get("/analyze_statistics_report", response_class=PlainTextResponse)
    def api_analyze_statistics_report(tid: str, cid: str, sid: str, begin: Optional[str] = None, end: Optional[str] = None):
        # 重要：回傳純文字，不要被 JSON 再次跳脫
        return _analyze_statistics_report_internal(tid, cid, sid, begin, end)

    # Health check for ngrok
    @app.get("/")
    def read_root():
        return {"status": "ok", "service": "Taoyuan Statistics API"}

    print("Starting FastAPI Server via Uvicorn...", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=8000)

# --- Entry Point ---

if __name__ == "__main__":
    # Check for arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "api":
            run_api_server()
        elif mode == "mcp":
            run_mcp_server()
        else:
            # If arguments are passed but not 'api', it is likely mcp stdio args
            # In standard MCP usage, no args are passed for stdio usually, 
            # but let's default to mcp if it doesn't match 'api'.
            run_mcp_server()
    else:
        # Default behavior for compatibility
        run_mcp_server()