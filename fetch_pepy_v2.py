import urllib.request
import re
import json
import sys

url = "https://pepy.tech/projects/epi-recorder"
print(f"Fetching {url}...", file=sys.stderr)

try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
    
    print(f"Page fetched. Length: {len(html)}", file=sys.stderr)
    
    # Look for Next.js hydration data
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if match:
        print("Found __NEXT_DATA__!", file=sys.stderr)
        data = json.loads(match.group(1))
        # Dump the entire JSON structure to stdout
        print(json.dumps(data, indent=2))
    else:
        print("No __NEXT_DATA__ found.", file=sys.stderr)
        # Search for any other interesting data
        downloads = re.findall(r'(\d{1,3}(?:,\d{3})*) downloads', html)
        print(f"Regex found downloads: {downloads}", file=sys.stderr)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
