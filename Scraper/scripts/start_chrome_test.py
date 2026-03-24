import os
import tempfile
import shutil
import zipfile
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

MAJOR = 144

def download_chromedriver_for_major(major: int):
    ver_url = f"https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{major}"
    r = requests.get(ver_url, timeout=20)
    r.raise_for_status()
    version = r.text.strip()
    zip_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
    r = requests.get(zip_url, timeout=60, stream=True)
    r.raise_for_status()
    tmpdir = os.path.join(tempfile.gettempdir(), 'auto_job_chromedriver_test', version)
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)
    zip_path = os.path.join(tmpdir, 'chromedriver.zip')
    with open(zip_path, 'wb') as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(tmpdir)
    for root, dirs, files in os.walk(tmpdir):
        if 'chromedriver.exe' in files:
            return os.path.join(root, 'chromedriver.exe')
    return None


def start_chrome_with_driver(driver_path: str):
    options = Options()
    # use a fresh temp profile to avoid profile locking issues
    temp_profile = os.path.join(tempfile.gettempdir(), 'auto_job_profile_test')
    if os.path.exists(temp_profile):
        shutil.rmtree(temp_profile)
    os.makedirs(temp_profile, exist_ok=True)
    options.add_argument(f"--user-data-dir={temp_profile}")
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    # useful to see browser window
    service = Service(executable_path=driver_path)
    print('Starting Chrome with', driver_path)
    drv = None
    try:
        drv = webdriver.Chrome(service=service, options=options)
        print('Started. current_url:', drv.current_url)
        print('capabilities:', drv.capabilities)
        time.sleep(6)
    except Exception as e:
        print('Error while starting Chrome:', type(e).__name__, e)
    finally:
        try:
            if drv:
                drv.quit()
                print('Quit driver cleanly')
        except Exception as e:
            print('Error on quit:', e)

if __name__ == '__main__':
    print('Downloading chromedriver...')
    dp = download_chromedriver_for_major(MAJOR)
    print('Downloaded driver path:', dp)
    if not dp:
        print('Driver not found, aborting')
    else:
        start_chrome_with_driver(dp)
