import server
import pandas as pd
import sys

# Mock data
# 模擬一個包含「桃園市」總計列的資料
mock_data = [
    {"District": "桃園市", "Value": 1000}, # Total
    {"District": "District A", "Value": 200},
    {"District": "District B", "Value": 300},
    {"District": "District C", "Value": 500},
]

print("Testing with mock data (Taoyuan City = 1000, A=200, B=300, C=500)...")

# Patch internal fetch
server._fetch_data_internal = lambda tid, cid, sid, b, e: mock_data

# Run analysis
report = server.analyze_statistics_report("tid", "cid", "sid")

print("\n--- Report Output ---")
print(report)

print("\n--- Verification ---")
# Check for key indicators in the text
if "數值總計: 1,000" in report:
    print("PASS: Sum includes Total row correctly (or explicitly taken from it).")
else:
    print("FAIL: Sum is incorrect.")

if "平均水準: 333.33" in report:
    print("PASS: Mean is calculated excluding Total row ( (200+300+500)/3 = 333.33 ).")
else:
    print("FAIL: Mean is incorrect (likely included Total row).")

if "最高為 District C" in report:
    print("PASS: Max row excludes Total row.")
else:
    print("FAIL: Max row is incorrect (likely picked Taoyuan City).")
