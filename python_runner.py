import sys
import io
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Python Runner (Safe Mode)")
GLOBAL_STATE = {}

# 1. 定義危險關鍵字黑名單
FORBIDDEN_KEYWORDS = [
    "import os", "from os",
    "import sys", "from sys",
    "import shutil", "from shutil",
    "import subprocess",
    "open(",
    "input(",
    "__import__"
]

def check_security(code: str):
    """
    檢查程式碼是否包含危險操作
    """
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in code:
            raise ValueError(f"Security Alert: 禁止使用 '{keyword}' 相關操作！")
    
    if re.search(r"import\s+(os|sys|shutil|subprocess)", code):
        raise ValueError("Security Alert: 禁止匯入系統模組！")

@mcp.tool()
def run_python_cell(code: str) -> str:
    """
    執行 Python 程式碼 (安全限制版)。
    可以進行運算、字串處理、邏輯判斷。
    ❌ 禁止：檔案讀寫、系統指令、刪除檔案。
    """
    
    try:
        check_security(code)
    except ValueError as e:
        return f"🚫 {str(e)}"
    
    output_buffer = io.StringIO()
    original_stdout = sys.stdout
    
    # 🔧 修正：正確處理 __builtins__
    if isinstance(__builtins__, dict):
        safe_builtins = __builtins__.copy()
    else:
        safe_builtins = __builtins__.__dict__.copy()
    
    # 移除危險函式
    safe_builtins.pop('open', None)
    safe_builtins.pop('exit', None)
    safe_builtins.pop('quit', None)
    
    execution_globals = GLOBAL_STATE.copy()
    execution_globals['__builtins__'] = safe_builtins
    
    try:
        sys.stdout = output_buffer
        
        exec(code, execution_globals)
        
        for key, value in execution_globals.items():
            if key != '__builtins__':
                GLOBAL_STATE[key] = value
        
        result = output_buffer.getvalue()
        if not result:
            return "✅ 執行成功 (無輸出內容)"
        return result.strip()
        
    except Exception as e:
        return f"❌ 執行錯誤: {str(e)}"
        
    finally:
        sys.stdout = original_stdout

@mcp.tool()
def clear_memory() -> str:
    GLOBAL_STATE.clear()
    return "記憶體已清除。"

if __name__ == "__main__":
    mcp.run()