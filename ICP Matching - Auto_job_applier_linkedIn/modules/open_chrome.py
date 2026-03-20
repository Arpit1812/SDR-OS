'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

version:    26.01.20.5.08
'''

from modules.helpers import get_default_temp_profile, make_directories
from config.settings import run_in_background, stealth_mode, disable_extensions, safe_mode, file_name, failed_file_name, logs_folder_path, generated_resume_path, always_use_guest_profile
from config.questions import default_resume_path
from config.icp import icp_leads_file_name
import os
import requests
import io
import zipfile
import tempfile
import shutil
import subprocess

# Import Service when using selenium fallback
from selenium.webdriver.chrome.service import Service

if stealth_mode:
    import undetected_chromedriver as uc
else: 
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    # from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from modules.helpers import find_default_profile_directory, critical_error_log, print_lg
from selenium.common.exceptions import SessionNotCreatedException

def createChromeSession(isRetry: bool = False):
    project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icp_leads_path = icp_leads_file_name if os.path.isabs(icp_leads_file_name) else os.path.join(project_root_dir, icp_leads_file_name)
    make_directories([file_name, failed_file_name, icp_leads_path, logs_folder_path+"/screenshots", default_resume_path, generated_resume_path+"/temp"])

    # Try to detect installed Chrome and pre-download a matching ChromeDriver so we avoid
    # undetected_chromedriver auto-download mismatches and long hangups.
    driver_path = None
    try:
        major = get_installed_chrome_major()
        if major:
            print_lg(f"Detected local Chrome major version: {major}. Attempting to download matching ChromeDriver first (if missing)...")
            driver_path = download_chromedriver_for_major(major)
            if driver_path:
                print_lg(f"Pre-downloaded ChromeDriver for major {major}: {driver_path}")
    except Exception as e:
        print_lg("Could not auto-detect or download ChromeDriver upfront:", e)

    # Set up WebDriver with Chrome Profile
    options = uc.ChromeOptions() if stealth_mode else Options()
    if run_in_background:   options.add_argument("--headless")
    if disable_extensions:  options.add_argument("--disable-extensions")

    print_lg("IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM! Or it's highly likely that application will just open browser and not do anything!")
    profile_dir = find_default_profile_directory()
    # If requested, force guest profile regardless of existing Chrome processes or detected profiles
    if isRetry or always_use_guest_profile:
        temp_profile = get_default_temp_profile()
        print_lg(f"Using temporary Chrome profile (forced guest): {temp_profile}")
        options.add_argument(f"--user-data-dir={temp_profile}")
    elif profile_dir and not safe_mode:
        # Defensive: profile_dir should be a path; if it already contains the CLI flag, strip it
        if isinstance(profile_dir, str) and profile_dir.startswith("--user-data-dir="):
            profile_dir = profile_dir.split("=", 1)[1]
        print_lg(f"Using Chrome profile directory: {profile_dir}")
        options.add_argument(f"--user-data-dir={profile_dir}")
    else:
        temp_profile = get_default_temp_profile()
        print_lg(f"Using temporary Chrome profile: {temp_profile}")
        options.add_argument(f"--user-data-dir={temp_profile}")

    if stealth_mode:
        print_lg("Downloading Chrome Driver... This may take some time. Undetected mode requires download every run!")
        try:
            # If we pre-downloaded a matching driver, prefer starting with regular Selenium Service (more reliable)
            if driver_path:
                try:
                    from selenium import webdriver
                    service = Service(executable_path=driver_path)
                    driver = webdriver.Chrome(service=service, options=options)
                    print_lg("Started Chrome using pre-downloaded matching chromedriver via Selenium Service.")
                except Exception as e_start:
                    print_lg("Starting with pre-downloaded chromedriver failed, will try undetected_chromedriver as fallback.", e_start)
                    try:
                        # Try uc with explicit driver path if supported
                        try:
                            driver = uc.Chrome(options=options, driver_executable_path=driver_path)
                        except TypeError:
                            print_lg("undetected_chromedriver does not support explicit driver path on this version; falling back to uc default behavior.")
                            driver = uc.Chrome(options=options)
                    except Exception as e_uc:
                        # If uc also fails, surface the original error below
                        raise
            else:
                # No pre-downloaded driver, fall back to uc default behavior
                driver = uc.Chrome(options=options)
        except SessionNotCreatedException as e:
            msg = str(e)
            print_lg("Chrome session creation failed (undetected mode).")
            print_lg("Details: " + msg)
            # If Chrome crashed due to profile being used (DevToolsActivePort/"crashed"), prompt user to close or allow automated kill
            crashed_signals = ("DevToolsActivePort", "crashed", "Chrome failed to start")
            if any(sig in msg for sig in crashed_signals):
                print_lg("Chrome crash detected during startup. This often happens if Chrome is already running with the same profile.")
                try:
                    import pyautogui
                    # Ask user what to do
                    choice = pyautogui.confirm('Chrome failed to start with the selected profile. Close all Chrome windows and retry?\n\nChoose "Close Chrome & Retry" to terminate running Chrome processes automatically and retry starting the bot with your profile.\nChoose "Use Guest Profile" to continue with a temporary profile instead.\nChoose "Cancel" to stop starting the browser.', buttons=["Close Chrome & Retry","Use Guest Profile","Cancel"])
                except Exception:
                    choice = None
                # If user chose to close Chrome, kill processes and retry
                if choice == "Close Chrome & Retry":
                    print_lg("User requested to close Chrome and retry. Killing chrome.exe processes...")
                    try:
                        subprocess.run(["taskkill","/F","/IM","chrome.exe"], check=False)
                        time.sleep(1)
                    except Exception as ke:
                        print_lg("Failed to kill chrome processes:", ke)
                    # Retry starting with pre-downloaded driver if available
                    try:
                        if driver_path:
                            from selenium import webdriver
                            service = Service(executable_path=driver_path)
                            driver = webdriver.Chrome(service=service, options=options)
                            print_lg("Restart succeeded after killing Chrome processes.")
                        else:
                            driver = uc.Chrome(options=options)
                        # If we reached here, driver started successfully
                    except Exception as retry_exc:
                        print_lg("Restart after killing Chrome failed:", retry_exc)
                        raise
                elif choice == "Use Guest Profile":
                    # Switch to using a temp profile and continue
                    temp_profile = get_default_temp_profile()
                    print_lg(f"User chose to use guest profile. Switching to temp profile: {temp_profile}")
                    options.add_argument(f"--user-data-dir={temp_profile}")
                    try:
                        driver = uc.Chrome(options=options) if stealth_mode else webdriver.Chrome(options=options)
                    except Exception as guest_exc:
                        print_lg("Failed to start with guest profile:", guest_exc)
                        raise
                else:
                    # No choice (headless or failed prompt) or Cancel — surface the original error
                    if "This version of ChromeDriver only supports Chrome version" in msg or "cannot connect to chrome" in msg:
                        print_lg("Suggested actions: 1) Update Chrome to the latest version; 2) Run 'setup/windows-setup.bat' to install a matching ChromeDriver; 3) Or set 'stealth_mode = False' in 'config/settings.py' to use local chromedriver.")
                    raise
            else:
                if "This version of ChromeDriver only supports Chrome version" in msg or "cannot connect to chrome" in msg:
                    print_lg("Suggested actions: 1) Update Chrome to the latest version; 2) Run 'setup/windows-setup.bat' to install a matching ChromeDriver; 3) Or set 'stealth_mode = False' in 'config/settings.py' to use local chromedriver.")
                # Try a fallback to regular selenium Chrome (in case we have downloaded a matching chromedriver)
                try:
                    print_lg("Attempting fallback: start Chrome using regular selenium webdriver...")
                    # Import webdriver locally in case undetected mode was used and global webdriver isn't defined
                    try:
                        from selenium import webdriver
                    except Exception as ie:
                        print_lg("Could not import selenium.webdriver for fallback.", ie)
                        raise
                    if driver_path:
                        service = Service(executable_path=driver_path)
                        driver = webdriver.Chrome(service=service, options=options)
                    else:
                        driver = webdriver.Chrome(options=options)
                    print_lg("Fallback succeeded: Started Chrome with regular selenium webdriver.")
                except SessionNotCreatedException as e2:
                    print_lg("Fallback failed.", e2)
                    raise
                except Exception as e2:
                    print_lg("Fallback attempt raised an unexpected error.", e2)
                    raise
    else:
        try:
            if driver_path:
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)
        except SessionNotCreatedException as e:
            msg = str(e)
            print_lg("Failed to start Chrome via Selenium.")
            print_lg("Details: " + msg)
            if "This version of ChromeDriver only supports Chrome version" in msg:
                print_lg("Suggested actions: Update Chrome or the chromedriver binary so their major versions match (or run 'setup/windows-setup.bat').")
            raise
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)
    return options, driver, actions, wait

def get_installed_chrome_major() -> int | None:
    """Return the major version integer of the installed Chrome, or None on failure.

    Uses PowerShell's File VersionInfo to read ProductVersion which works even when Chrome
    is already running (calling chrome.exe --version can return "Opening in existing browser session").
    """
    try:
        cmd = ["powershell", "-Command", "(Get-Item 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe').VersionInfo.ProductVersion"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        out = proc.stdout.strip()
        import re
        m = re.search(r"(\d+)\.", out)
        if m:
            return int(m.group(1))
    except Exception:
        try:
            cmd = ["powershell", "-Command", "(Get-Item 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe').VersionInfo.ProductVersion"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            out = proc.stdout.strip()
            import re
            m = re.search(r"(\d+)\.", out)
            if m:
                return int(m.group(1))
        except Exception:
            return None
    return None


def download_chromedriver_for_major(major: int) -> str | None:
    """Download chromedriver matching the given major version and return path to chromedriver.exe or None."""
    try:
        ver_url = f"https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{major}"
        print_lg(f"Fetching matching ChromeDriver version from: {ver_url}")
        r = requests.get(ver_url, timeout=20)
        r.raise_for_status()
        version = r.text.strip()
        zip_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
        print_lg(f"Downloading ChromeDriver from: {zip_url}")
        r = requests.get(zip_url, timeout=60, stream=True)
        r.raise_for_status()
        tmpdir = os.path.join(tempfile.gettempdir(), "auto_job_chromedriver", version)
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir, exist_ok=True)
        zip_path = os.path.join(tmpdir, "chromedriver.zip")
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(tmpdir)
        for root, dirs, files in os.walk(tmpdir):
            if 'chromedriver.exe' in files:
                return os.path.join(root, 'chromedriver.exe')
    except Exception as e:
        print_lg("Failed to download chromedriver:", e)
    return None


try:
    options, driver, actions, wait = None, None, None, None
    options, driver, actions, wait = createChromeSession()
except SessionNotCreatedException as e:
    critical_error_log("Failed to create Chrome Session, retrying with guest profile", e)
    try:
        options, driver, actions, wait = createChromeSession(True)
    except SessionNotCreatedException as e2:
        print_lg("Retry with guest profile also failed.")
        # Try to auto-download matching chromedriver for the installed Chrome
        major = get_installed_chrome_major()
        if major:
            print_lg(f"Detected Chrome major version: {major}. Attempting to download matching ChromeDriver...")
            driver_path = download_chromedriver_for_major(major)
            if driver_path:
                print_lg(f"Downloaded chromedriver at {driver_path}, trying to start Chrome with it")
                try:
                    from selenium import webdriver
                    service = Service(executable_path=driver_path)
                    driver = webdriver.Chrome(service=service, options=options)
                    wait = WebDriverWait(driver, 5)
                    actions = ActionChains(driver)
                except Exception as e3:
                    critical_error_log("Failed to start Chrome with downloaded chromedriver", e3)
                    raise
            else:
                raise
        else:
            raise
except Exception as e:
    msg = 'Seems like Google Chrome is out dated. Update browser and try again! \n\n\nIf issue persists, try Safe Mode. Set, safe_mode = True in config.py \n\nPlease check GitHub discussions/support for solutions https://github.com/GodsScion/Auto_job_applier_linkedIn \n                                   OR \nReach out in discord ( https://discord.gg/fFp7uUzWCY )'
    if isinstance(e,TimeoutError): msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"
    print_lg(msg)
    critical_error_log("In Opening Chrome", e)
    from pyautogui import alert
    alert(msg, "Error in opening chrome")
    try: driver.quit()
    except NameError: exit()
    
