import requests
import json
import socket
from mcp.server.fastmcp import FastMCP
import datetime 
import math


# 初始化 MCP Server，名稱取叫 System Tools 以後可以加更多系統功能
mcp = FastMCP("System Tools")

@mcp.tool()
def get_ip_address() -> str:
    """
    查詢本機目前的內網 IP (LAN) 與外網 IP (WAN) 位址。
    外網 IP 使用 whatismyip.akamai.com 查詢。
    
    Returns:
        包含 internal_ip 和 external_ip 的 JSON 字串。
    """
    result = {}

    # 1. 查詢內網 IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 連線到一個外部地址 (不會真的傳送封包) 來決定使用哪個網卡 IP
        s.connect(("8.8.8.8", 80))
        internal_ip = s.getsockname()[0]
        s.close()
        result["internal_ip"] = internal_ip
    except Exception as e:
        result["internal_ip"] = f"Unknown ({str(e)})"

    # 2. 查詢外網 IP (使用 whatismyip.akamai.com)
    try:
        # 添加 User-Agent 模擬瀏覽器行為
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 這是 akamai 提供的節點，回傳純文字 IP，非常乾淨快速
        response = requests.get("http://whatismyip.akamai.com/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            result["external_ip"] = response.text.strip()
            result["provider"] = "whatismyip.akamai.com"
        else:
            result["external_ip"] = f"Unknown (Status: {response.status_code})"
            
    except Exception as e:
        result["external_ip"] = f"Unknown ({str(e)})"

    return json.dumps(result, ensure_ascii=False, indent=2)
    
@mcp.tool()
def get_current_time() -> str:
    """
    獲取現在的系統時間。
    """
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def calculate(expression: str) -> str:
    """
    執行數學運算 (工程計算機)。
    
    支援運算符號: +, -, *, /, ** (次方), % (餘數), // (整除)
    支援函式: sqrt(開根號), abs(絕對值), round(四捨五入), sin, cos, tan, log, pi, e
    
    範例: 
    - "100 * 0.05 + 300"
    - "sqrt(25) * 10"
    - "pi * 5**2" (計算圓面積)
    """
    # 建立一個安全的執行環境，只允許使用 math 庫裡的數學函式
    # 這樣可以防止 AI 透過計算機執行 os.system 等危險指令
    safe_dict = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    safe_dict.update({
        "abs": abs,
        "round": round,
        "min": min,
        "max": max
    })
    
    try:
        # 使用 eval 計算字串表達式
        # {"__builtins__": None} 是為了資安，禁止存取內建危險函式
        result = eval(expression, {"__builtins__": None}, safe_dict)
        return f"{result}"
    except Exception as e:
        return f"計算錯誤: {str(e)}"
        
if __name__ == "__main__":
    mcp.run()