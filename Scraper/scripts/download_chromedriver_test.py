import os
import requests
import zipfile
import tempfile
import shutil

major = 144
try:
    ver_url = f"https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{major}"
    print('Fetching version from', ver_url)
    r = requests.get(ver_url, timeout=20)
    r.raise_for_status()
    version = r.text.strip()
    print('Resolved version:', version)
    zip_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
    print('Downloading from', zip_url)
    r = requests.get(zip_url, timeout=60, stream=True)
    r.raise_for_status()
    tmpdir = os.path.join(tempfile.gettempdir(), 'auto_job_chromedriver_test', version)
    if os.path.exists(tmpdir): shutil.rmtree(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)
    zip_path = os.path.join(tmpdir, 'chromedriver.zip')
    with open(zip_path, 'wb') as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(tmpdir)
    found = False
    for root, dirs, files in os.walk(tmpdir):
        if 'chromedriver.exe' in files:
            print('Found chromedriver at', os.path.join(root, 'chromedriver.exe'))
            found = True
    if not found:
        print('chromedriver.exe not found in archive')
except Exception as e:
    print('Error:', e)