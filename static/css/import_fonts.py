import os
import requests

# ✅ Verified working URL from Google Fonts GitHub
url = "https://fonts.gstatic.com/s/satisfy/v17/rP2Hp2yn6lkG50LoOZ3K.woff2"
output_dir = "static/fonts"
output_path = os.path.join(output_dir, "Satisfy-Regular.woff2")

os.makedirs(output_dir, exist_ok=True)
print("Downloading Satisfy font...")

r = requests.get(url)
if r.ok:
    with open(output_path, "wb") as f:
        f.write(r.content)
    print("Font saved to:", output_path)
else:
    print("Failed to download font:", r.status_code)
