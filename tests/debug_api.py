import requests

url = "https://statisticsinfo.tycg.gov.tw/TaoyuanSTYB/RestfulAPI/GetStaticData.aspx"
params = {
    "tid": "0001",
    "cid": "0001",
    "sid": "000001",
    "begin": "2024",
    "end": "2025",
    "type": "JSON"
}

print(f"Testing URL: {url}")
print(f"Params: {params}")

try:
    response = requests.get(url, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Response Length: {len(response.text)}")
    print("\nResponse Content (First 500 chars):")
    print(response.text[:500])
    
    try:
        json_data = response.json()
        print(f"\nJSON Parsed Successfully: {len(json_data)} items")
    except Exception as e:
        print(f"\nJSON Parse Error: {e}")

except Exception as e:
    print(f"Request Error: {e}")
