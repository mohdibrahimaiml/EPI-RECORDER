import requests
import re
import json

url = "https://pepy.tech/projects/epi-recorder"
print(f"Fetching {url}...")

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    html = response.text
    print(f"Page fetched. Length: {len(html)}")
    
    # Look for Next.js hydration data
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if match:
        print("Found __NEXT_DATA__!")
        data = json.loads(match.group(1))
        # Navigate to relevant props (structure varies, but usually in props.pageProps)
        print(json.dumps(data, indent=2)[:5000]) # Print first 5k chars to inspect structure
    else:
        print("No __NEXT_DATA__ found. Printing first 2000 chars of HTML to inspect:")
        print(html[:2000])
        
except Exception as e:
    print(f"Error: {e}")
