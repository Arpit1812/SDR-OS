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


# Imports
import os
import csv
import re
import time
import pyautogui
import json

# Set CSV field size limit to prevent field size errors
csv.field_size_limit(1000000)  # Set to 1MB instead of default 131KB

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException, WebDriverException

from config.personals import *
from config.questions import *
from config.search import *
from config.secrets import use_AI, username, password, ai_provider
from config.settings import *
from config.icp import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config

if use_AI:
    from modules.ai.openaiConnections import ai_create_openai_client, ai_extract_skills, ai_answer_question, ai_close_openai_client
    from modules.ai.deepseekConnections import deepseek_create_client, deepseek_extract_skills, deepseek_answer_question
    from modules.ai.geminiConnections import gemini_create_client, gemini_extract_skills, gemini_answer_question

from typing import Literal

try:
    icp_require_company_size_in_score_mode
except NameError:
    try:
        icp_require_company_size_in_score_mode = icp_require_company_size_in_scro_mode
    except NameError:
        icp_require_company_size_in_score_mode = False

try:
    icp_require_industry_in_score_mode
except NameError:
    icp_require_industry_in_score_mode = False

try:
    icp_title_pre_filter
except NameError:
    icp_title_pre_filter = False


pyautogui.FAILSAFE = False
# if use_resume_generator:    from resume_generator import is_logged_in_GPT, login_GPT, open_resume_chat, create_custom_resume


#< Global Variables and logics

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = first_name + " " + middle_name + " " + last_name if middle_name else first_name + " " + last_name

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
jobs_scanned_count = 0
icp_matched_count = 0
icp_saved_count = 0
dailyEasyApplyLimitReached = False

is_apply_mode = lead_extraction_mode in ["apply_only", "hybrid"]
is_extractor_mode = lead_extraction_mode in ["extractor_only", "hybrid"]
icp_leads_run_file_name = icp_leads_file_name
project_root_dir = os.path.dirname(os.path.abspath(__file__))

# Use ICP-specific search terms in extractor/hybrid mode when configured.
effective_search_terms = search_terms
if is_extractor_mode and isinstance(icp_search_terms, list) and len(icp_search_terms) > 0:
    effective_search_terms = icp_search_terms
using_icp_search_terms = effective_search_terms == icp_search_terms and is_extractor_mode and len(icp_search_terms) > 0

# Use ICP-specific search location in extractor/hybrid mode when configured.
effective_search_location = search_location
if is_extractor_mode and isinstance(icp_search_location, str) and icp_search_location.strip():
    effective_search_location = icp_search_location
using_icp_search_location = effective_search_location == icp_search_location and is_extractor_mode and bool(icp_search_location.strip())

# Use ICP-specific filter overrides in extractor/hybrid mode.
effective_sort_by = sort_by
if is_extractor_mode and isinstance(icp_sort_by, str):
    effective_sort_by = icp_sort_by

effective_date_posted = date_posted
if is_extractor_mode and isinstance(icp_date_posted, str):
    effective_date_posted = icp_date_posted

effective_salary = salary
if is_extractor_mode and isinstance(icp_salary, str):
    effective_salary = icp_salary

effective_easy_apply_only = easy_apply_only
if is_extractor_mode:
    effective_easy_apply_only = icp_easy_apply_only

effective_experience_level = experience_level
if is_extractor_mode and isinstance(icp_experience_level, list) and len(icp_experience_level) > 0:
    effective_experience_level = icp_experience_level

effective_job_type = job_type
if is_extractor_mode and isinstance(icp_job_type, list) and len(icp_job_type) > 0:
    effective_job_type = icp_job_type

effective_on_site = on_site
if is_extractor_mode and isinstance(icp_on_site, list) and len(icp_on_site) > 0:
    effective_on_site = icp_on_site

def convert_csv_to_json(csv_path: str, json_path: str):
    '''
    Convert ICP CSV leads to JSON for SDR integration
    '''
    try:
        import csv
        data = []

        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print_lg(f"Converted leads CSV → JSON: {json_path}")

    except Exception as e:
        print_lg("Failed to convert CSV to JSON!", e)


def build_run_scoped_icp_leads_file_name() -> str:
    '''
    Build a unique ICP leads CSV path for the current execution run.
    Example:
    all excels/icp_leads__20260304_153012.csv
    '''
    file_path = icp_leads_file_name
    if not os.path.isabs(file_path):
        file_path = os.path.join(project_root_dir, file_path)

    file_dir = os.path.dirname(file_path)
    file_base = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(file_base)
    if not ext:
        ext = ".csv"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_file_name = f"{name_without_ext}__{timestamp}{ext}"
    return os.path.join(file_dir, run_file_name) if file_dir else run_file_name

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

aiClient = None
##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
about_company_for_ai = None # TODO extract about company for AI
##<

#>


#< Login Functions
def is_logged_in_LN() -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    '''
    if driver.current_url == "https://www.linkedin.com/feed/": return True
    if try_linkText(driver, "Sign in"): return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  return False
    if try_linkText(driver, "Join now"): return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN() -> None:
    '''
    Function to login for LinkedIn
    * Tries to login using given `username` and `password` from `secrets.py`
    * If failed, tries to login using saved LinkedIn profile button if available
    * If both failed, asks user to login manually
    '''
    # Find the username and password fields and fill them with user credentials
    driver.get("https://www.linkedin.com/login")
    if username == "username@example.com" and password == "example_password":
        pyautogui.alert("User did not configure username and password in secrets.py, hence can't login automatically! Please login manually!", "Login Manually","Okay")
        print_lg("User did not configure username and password in secrets.py, hence can't login automatically! Please login manually!")
        manual_login_retry(is_logged_in_LN, 2)
        return
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", username, 1)
        except Exception as e:
            print_lg("Couldn't find username field.")
            # print_lg(e)
        try:
            text_input_by_ID(driver, "password", password, 1)
        except Exception as e:
            print_lg("Couldn't find password field.")
            # print_lg(e)
        # Find the login submit button and click it
        driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            # print_lg(e1, e2)
            print_lg("Couldn't Login!")

    try:
        # Wait until successful redirect, indicating successful login
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/")) # wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space(.)="Start a post"]')))
        return print_lg("Login successful!")
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        # print_lg(e)
        manual_login_retry(is_logged_in_LN, 2)
#>



def get_applied_job_ids() -> set[str]:
    '''
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    '''
    job_ids: set[str] = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids


def get_existing_lead_job_ids() -> set[str]:
    '''
    Function to get a set of existing lead Job IDs from ICP leads CSV.
    '''
    job_ids: set[str] = set()
    try:
        with open(icp_leads_run_file_name, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("Job ID"):
                    job_ids.add(row["Job ID"])
    except FileNotFoundError:
        print_lg(f"The CSV file '{icp_leads_run_file_name}' does not exist.")
    except Exception as e:
        print_lg("Failed reading existing ICP leads file.", e)
    return job_ids


def contains_any(text: str, keywords: list[str]) -> tuple[bool, list[str]]:
    '''
    Returns match state and matched keywords in a text.
    '''
    text_low = " ".join(text.lower().split())
    matches = []
    expanded_terms: list[tuple[str, str]] = []
    for keyword in keywords:
        kw = keyword.strip().lower()
        if not kw:
            continue
        expanded_terms.append((keyword, kw))
        if kw == "cto":
            expanded_terms.append((keyword, "chief technology officer"))
            expanded_terms.append((keyword, "CTO - Cofounder"))
            expanded_terms.append((keyword, "CTO & Cofounder"))
            expanded_terms.append((keyword, "chief technical officer"))

    for original_keyword, kw in expanded_terms:
        # Match full keyword/phrase boundaries to avoid false positives
        # like "cto" matching inside "director".
        phrase_pattern = re.escape(kw).replace(r"\ ", r"[\s\-_\/]+")
        pattern = rf'(?<!\w){phrase_pattern}(?!\w)'
        if re.search(pattern, text_low, re.IGNORECASE):
            matches.append(original_keyword)
    # Deduplicate while preserving order.
    matches = list(dict.fromkeys(matches))
    return len(matches) > 0, matches


def extract_company_context() -> tuple[str, str, str]:
    '''
    Extracts company context text and attempts to derive company size and industry.
    Returns (company_context_text, company_size_raw, company_industry_raw)
    '''
    company_context = ""
    company_size_raw = "Unknown"
    company_industry_raw = "Unknown"

    try:
        company_box = try_find_by_classes(driver, ["jobs-company__box", "jobs-details__main-content"])
        if company_box:
            company_context = company_box.text
    except Exception:
        pass

    if not company_context:
        try:
            company_context = driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            company_context = ""

    size_match = re.search(r'(\d[\d,]*)\s*-\s*(\d[\d,]*)\s+employees?', company_context, re.IGNORECASE)
    if size_match:
        company_size_raw = f'{size_match.group(1).replace(",", "")}-{size_match.group(2).replace(",", "")}'

    lines = [line.strip() for line in company_context.split("\n") if line.strip()]
    for line in lines:
        line_low = line.lower()
        if "employee" in line_low:
            continue
        if any(keyword.lower() in line_low for keyword in icp_industry_keywords):
            company_industry_raw = line
            break

    return company_context, company_size_raw, company_industry_raw


def evaluate_icp_lead(
    title: str,
    description: str,
    company_context: str,
    company_size_raw: str,
    company_industry_raw: str
) -> tuple[bool, int, list[str], list[str], list[str]]:
    '''
    Evaluates whether a job posting matches configured ICP.
    Returns: (is_match, score, match_reasons, reject_reasons)
    '''
    score = 0
    match_reasons: list[str] = []
    reject_reasons: list[str] = []

    title_has_role, role_title_matches = contains_any(title, icp_role_keywords)
    desc_has_role, role_desc_matches = contains_any(description, icp_role_keywords)
    industry_match, industry_matches = contains_any(
        f"{company_industry_raw} {company_context} {description}",
        icp_industry_keywords
    )
    non_technical_match, non_technical_matches = contains_any(
        f"{title} {description} {company_context}",
        icp_non_technical_signals
    )
    technical_exclusion_match, technical_exclusions = contains_any(
        f"{title} {description} {company_context}",
        icp_technical_exclusion_signals
    )
    company_size_match = company_size_raw in icp_company_size_targets

    if title_has_role:
        score += 35
        match_reasons.append(f"Role keyword in title: {', '.join(role_title_matches)}")
    if desc_has_role:
        score += 20
        match_reasons.append(f"Role keyword in description: {', '.join(role_desc_matches)}")
    if company_size_match:
        score += 20
        match_reasons.append(f"Company size matched: {company_size_raw}")
    if industry_match:
        score += 15
        match_reasons.append(f"Industry keyword matched: {', '.join(industry_matches)}")
    if non_technical_match:
        score += 15
        match_reasons.append(f"Non-technical founder signal: {', '.join(non_technical_matches)}")
    if technical_exclusion_match:
        score -= 25
        reject_reasons.append(f"Technical exclusion signal: {', '.join(technical_exclusions)}")

    if not (title_has_role or desc_has_role):
        reject_reasons.append("No role keyword matched")
    if not company_size_match:
        reject_reasons.append(f"Company size not matched ({company_size_raw})")
    if not industry_match:
        reject_reasons.append("Industry keyword not matched")
    if not non_technical_match:
        reject_reasons.append("No non-technical founder signal found")

    size_requirement = company_size_match if len(icp_company_size_targets) > 0 else True
    industry_requirement = industry_match if len(icp_industry_keywords) > 0 else True

    if icp_match_mode == "strict":
        is_match = (
            (title_has_role or desc_has_role)
            and size_requirement
            and industry_requirement
            and non_technical_match
            and not technical_exclusion_match
        )
    else:
        score_size_requirement = size_requirement if icp_require_company_size_in_score_mode else True
        score_industry_requirement = industry_requirement if icp_require_industry_in_score_mode else True
        is_match = (
            score >= icp_score_threshold
            and (title_has_role or desc_has_role)
            and score_size_requirement
            and score_industry_requirement
            and not technical_exclusion_match
        )

    matched_keywords = list(dict.fromkeys(
        role_title_matches + role_desc_matches + industry_matches + non_technical_matches
    ))
    return is_match, score, match_reasons, reject_reasons, matched_keywords


def parse_location_parts(location_text: str) -> tuple[str, str, str]:
    '''
    Parses location text into city/state/country parts.
    Returns empty strings when missing.
    '''
    if not location_text:
        return "", "", ""
    parts = [p.strip() for p in location_text.split(",") if p.strip()]
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], ""
    if len(parts) == 1:
        return parts[0], "", ""
    return "", "", ""


def extract_contact_enrichment(company_context: str, description: str) -> tuple[str, str, str, str, str]:
    '''
    Extracts website, company LinkedIn, Twitter, Facebook and phone from visible text/page links.
    Returns empty strings when unavailable.
    '''
    combined_text = f"{company_context}\n{description}"
    company_website = ""
    company_linkedin_url = ""
    company_twitter_url = ""
    company_facebook_url = ""
    company_phone_numbers = ""

    try:
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for anchor in anchors:
            href = (anchor.get_attribute("href") or "").strip()
            if not href:
                continue
            href_low = href.lower()
            if not company_linkedin_url and "linkedin.com/company/" in href_low:
                company_linkedin_url = href
            elif not company_twitter_url and ("twitter.com/" in href_low or "x.com/" in href_low):
                company_twitter_url = href
            elif not company_facebook_url and "facebook.com/" in href_low:
                company_facebook_url = href
            elif (
                not company_website
                and href_low.startswith("http")
                and "linkedin.com" not in href_low
                and "twitter.com" not in href_low
                and "x.com" not in href_low
                and "facebook.com" not in href_low
            ):
                company_website = href
    except Exception:
        pass

    if not company_phone_numbers:
        phone_matches = re.findall(r'(\+?\d[\d\-\s\(\)]{7,}\d)', combined_text)
        if phone_matches:
            cleaned = [re.sub(r'\s+', ' ', p).strip() for p in phone_matches]
            company_phone_numbers = " | ".join(list(dict.fromkeys(cleaned)))

    return company_website, company_linkedin_url, company_twitter_url, company_facebook_url, company_phone_numbers


def save_icp_lead(
    search_term: str,
    job_id: str,
    title: str,
    company: str,
    company_size_raw: str,
    company_industry_raw: str,
    work_location: str,
    job_link: str,
    hr_name: str,
    hr_link: str,
    icp_score: int,
    match_reasons: list[str],
    matched_keywords: list[str],
    description: str,
    company_context: str,
) -> None:
    '''
    Saves matched ICP lead data into CSV.
    '''
    fieldnames = [
        'Linkedin Url', 'Full Name', 'Email', 'Email Status', 'Job Title', 'Company Name',
        'Company Website', 'City', 'State', 'Country', 'Industry', 'Keywords', 'Employees',
        'Company City', 'Company State', 'Company Country', 'Company Linkedin Url',
        'Company Twitter Url', 'Company Facebook Url', 'Company Phone Numbers',
        'Buying Intent', 'Trigger', 'follow-up 1', 'Job Link'
    ]

    try:
        with open(icp_leads_run_file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0:
                writer.writeheader()
            city, state, country = parse_location_parts(work_location)
            company_city, company_state, company_country = "", "", ""
            company_website, company_linkedin_url, company_twitter_url, company_facebook_url, company_phone_numbers = extract_contact_enrichment(
                company_context=company_context,
                description=description
            )
            buying_intent = "High" if icp_score < 85 else "Very High"
            trigger = ", ".join(matched_keywords[:3]) if matched_keywords else ""
            writer.writerow({
                'Linkedin Url': truncate_for_csv(hr_link if hr_link != "Unknown" else ""),
                'Full Name': truncate_for_csv(hr_name if hr_name != "Unknown" else ""),
                'Email': "",
                'Email Status': "",
                'Job Title': truncate_for_csv(title),
                'Company Name': truncate_for_csv(company),
                'Company Website': truncate_for_csv(company_website),
                'City': truncate_for_csv(city),
                'State': truncate_for_csv(state),
                'Country': truncate_for_csv(country),
                'Industry': truncate_for_csv(company_industry_raw if company_industry_raw != "Unknown" else ""),
                'Keywords': truncate_for_csv(", ".join(matched_keywords)),
                'Employees': truncate_for_csv(company_size_raw if company_size_raw != "Unknown" else ""),
                'Company City': truncate_for_csv(company_city),
                'Company State': truncate_for_csv(company_state),
                'Company Country': truncate_for_csv(company_country),
                'Company Linkedin Url': truncate_for_csv(company_linkedin_url),
                'Company Twitter Url': truncate_for_csv(company_twitter_url),
                'Company Facebook Url': truncate_for_csv(company_facebook_url),
                'Company Phone Numbers': truncate_for_csv(company_phone_numbers),
                'Buying Intent': buying_intent,
                'Trigger': truncate_for_csv(trigger),
                'follow-up 1': "",
                'Job Link': truncate_for_csv(job_link),
            })
    except Exception as e:
        print_lg("Failed to save ICP lead.", e)


def initialize_icp_leads_file() -> None:
    '''
    Ensures run-scoped ICP leads CSV exists with header even if no rows match.
    '''
    fieldnames = [
        'Linkedin Url', 'Full Name', 'Email', 'Email Status', 'Job Title', 'Company Name',
        'Company Website', 'City', 'State', 'Country', 'Industry', 'Keywords', 'Employees',
        'Company City', 'Company State', 'Company Country', 'Company Linkedin Url',
        'Company Twitter Url', 'Company Facebook Url', 'Company Phone Numbers',
        'Buying Intent', 'Trigger', 'follow-up 1', 'Job Link'
    ]
    try:
        with open(icp_leads_run_file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0:
                writer.writeheader()
    except Exception as e:
        print_lg("Failed to initialize ICP leads file.", e)



def set_search_location() -> None:
    '''
    Function to set search location
    '''
    if effective_search_location.strip():
        try:
            print_lg(f'Setting search location as: "{effective_search_location.strip()}"')
            search_location_ele = try_xp(driver, ".//input[@aria-label='City, state, or zip code'and not(@disabled)]", False) #  and not(@aria-hidden='true')]")
            text_input(actions, search_location_ele, effective_search_location, "Search Location")
        except ElementNotInteractableException:
            try_xp(driver, ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']")
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(effective_search_location.strip()).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception as e:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg("Failed to update search location, continuing with default location!", e)


def apply_filters() -> None:
    '''
    Function to apply job search filters
    '''
    set_search_location()

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="All filters"]'))).click()
        buffer(recommended_wait)

        wait_span_click(driver, effective_sort_by)
        wait_span_click(driver, effective_date_posted)
        buffer(recommended_wait)

        multi_sel_noWait(driver, effective_experience_level) 
        multi_sel_noWait(driver, companies, actions)
        if effective_experience_level or companies: buffer(recommended_wait)

        multi_sel_noWait(driver, effective_job_type)
        multi_sel_noWait(driver, effective_on_site)
        if effective_job_type or effective_on_site: buffer(recommended_wait)

        if effective_easy_apply_only: boolean_button_click(driver, actions, "Easy Apply")
        
        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry: buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles: buffer(recommended_wait)

        if under_10_applicants: boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network: boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer: boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, effective_salary)
        buffer(recommended_wait)
        
        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments: buffer(recommended_wait)

        show_results_button: WebElement = driver.find_element(By.XPATH, '//button[contains(translate(@aria-label, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "apply current filters to show")]')
        show_results_button.click()

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == pyautogui.confirm("These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.", "Please check your results", ["Turn off Pause after search", "Look's good, Continue"]):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!")
        pyautogui.confirm(f"Faced error while applying filters. Please make sure correct filters are selected, click on show results and click on any button of this dialog, I know it sucks. Can't turn off Pause after search when error occurs! ERROR: {e}", ["Doesn't look good, but Continue XD", "Look's good, Continue"])
        # print_lg(e)



def get_page_info() -> tuple[WebElement | None, int | None]:
    '''
    Function to get pagination element and current page number
    '''
    try:
        pagination_element = try_find_by_classes(driver, ["jobs-search-pagination__pages", "artdeco-pagination", "artdeco-pagination__pages"])
        scroll_to_view(driver, pagination_element)
        current_page = int(pagination_element.find_element(By.XPATH, "//button[contains(@class, 'active')]").text)
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
        print_lg(e)
    return pagination_element, current_page



def get_job_main_details(job: WebElement, blacklisted_companies: set, rejected_jobs: set) -> tuple[str, str, str, str, str, bool]:
    '''
    # Function to get job main details.
    Returns a tuple of (job_id, title, company, work_location, work_style, skip)
    * job_id: Job ID
    * title: Job title
    * company: Company name
    * work_location: Work location of this job
    * work_style: Work style of this job (Remote, On-site, Hybrid)
    * skip: A boolean flag to skip this job
    '''
    skip = False
    try:
        job_details_button = job.find_element(By.TAG_NAME, 'a')  # job.find_element(By.CLASS_NAME, "job-card-list__title")  # Problem in India
    except NoSuchElementException:
        print_lg("Skipping job card because title link element <a> was not found.")
        return ("Unknown", "Unknown", "Unknown", "Unknown", "Unknown", True)
    scroll_to_view(driver, job_details_button, True)
    job_id = job.get_dom_attribute('data-occludable-job-id')
    title = job_details_button.text
    title = title[:title.find("\n")]
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
    index = other_details.find(' · ')
    company = other_details[:index]
    work_location = other_details[index+3:]
    work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
    work_location = work_location[:work_location.rfind('(')].strip()

    # In extractor mode, skip opening job details for obvious non-ICP titles.
    if is_extractor_mode and icp_title_pre_filter:
        title_match, _ = contains_any(title, icp_role_keywords)
        if not title_match:
            print_lg(f'Skipping non-ICP title "{title}" job. Job ID: {job_id}!')
            skip = True
            return (job_id, title, company, work_location, work_style, skip)
    
    # Skip if previously rejected due to blacklist or already applied
    if company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id in rejected_jobs: 
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True
    try:
        if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except: pass
    try:
        if not skip:
            job_details_button.click()
    except ElementClickInterceptedException as e:
        print_lg(f'Intercepted click for "{title} | {company}" job. Retrying safely. Job ID: {job_id}!')
        try:
            scroll_to_view(driver, job_details_button, True)
            driver.execute_script("arguments[0].click();", job_details_button)
        except Exception as retry_error:
            print_lg(f'Failed to open job details after retry, skipping this job. Job ID: {job_id}!', retry_error)
            skip = True
    except Exception as e:
        print_lg(f'Failed to click "{title} | {company}" job on details button. Skipping this job. Job ID: {job_id}!', e)
        skip = True
    buffer(click_gap)
    return (job_id,title,company,work_location,work_style,skip)


# Function to check for Blacklisted words in About Company
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company_org = about_company_org.text
    about_company = about_company_org.lower()
    skip_checking = False
    for word in about_company_good_words:
        if word.lower() in about_company:
            print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
            skip_checking = True
            break
    if not skip_checking:
        for word in about_company_bad_words: 
            if word.lower() in about_company: 
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card



# Function to extract years of experience required from About Job
def extract_years_of_experience(text: str) -> int:
    # Extract all patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    if len(matches) == 0: 
        print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
        return 0
    return max([int(match) for match in matches if int(match) <= 12])



def get_job_description(
    apply_filters_for_application: bool = True
) -> tuple[
    str | Literal['Unknown'],
    int | Literal['Unknown'],
    bool,
    str | None,
    str | None
    ]:
    '''
    # Job Description
    Function to extract job description from About the Job.
    ### Returns:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    '''
    skip = False
    skipReason = None
    skipMessage = None
    jobDescription = "Unknown"
    experience_required = "Unknown"

    try:
        ##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
        jobDescription = "Unknown"
        ##<
        experience_required = "Unknown"
        found_masters = 0
        jobDescription = find_by_class(driver, "jobs-box__html-content").text
        jobDescriptionLow = jobDescription.lower()
        if apply_filters_for_application:
            for word in bad_words:
                if word.lower() in jobDescriptionLow:
                    skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                    skipReason = "Found a Bad Word in About Job"
                    skip = True
                    break
            if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
                skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
                skipReason = "Asking for Security clearance"
                skip = True
            if not skip:
                if did_masters and 'master' in jobDescriptionLow:
                    print_lg(f'Found the word "master" in \n{jobDescription}')
                    found_masters = 2
                experience_required = extract_years_of_experience(jobDescription)
                if current_experience > -1 and experience_required > current_experience + found_masters:
                    skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                    skipReason = "Required experience is high"
                    skip = True
        else:
            experience_required = extract_years_of_experience(jobDescription)
    except Exception as e:
        if jobDescription == "Unknown":    print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)
    finally:
        return jobDescription, experience_required, skip, skipReason, skipMessage
        


# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(default_resume_path)
    except: return False, "Previous resume"

# Function to answer common questions for Easy Apply
def answer_common_questions(label: str, answer: str) -> str:
    if 'sponsorship' in label or 'visa' in label: answer = require_visa
    return answer


# Function to answer the questions for Easy Apply
def answer_questions(modal: WebElement, questions_list: set, work_location: str, job_description: str | None = None ) -> set:
    # Get all questions from the page
     
    all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
    # all_questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    # all_list_questions = modal.find_elements(By.XPATH, ".//div[@data-test-text-entity-list-form-component]")
    # all_single_line_questions = modal.find_elements(By.XPATH, ".//div[@data-test-single-line-text-form-component]")
    # all_questions = all_questions + all_list_questions + all_single_line_questions

    for Question in all_questions:
        # Check if it's a select Question
        select = try_xp(Question, ".//select", False)
        if select:
            label_org = "Unknown"
            try:
                label = Question.find_element(By.TAG_NAME, "label")
                label_org = label.find_element(By.TAG_NAME, "span").text
            except: pass
            answer = 'Yes'
            label = label_org.lower()
            select = Select(select)
            selected_option = select.first_selected_option.text
            optionsText = []
            options = '"List of phone country codes"'
            if label != "phone country code":
                optionsText = [option.text for option in select.options]
                options = "".join([f' "{option}",' for option in optionsText])
            prev_answer = selected_option
            if overwrite_previous_answers or selected_option == "Select an option":
                ##> ------ WINDY_WINDWARD Email:karthik.sarode23@gmail.com - Added fuzzy logic to answer location based questions ------
                if 'email' in label or 'phone' in label: 
                    answer = prev_answer
                elif 'gender' in label or 'sex' in label: 
                    answer = gender
                elif 'disability' in label: 
                    answer = disability_status
                elif 'proficiency' in label: 
                    answer = 'Professional'
                # Add location handling
                elif any(loc_word in label for loc_word in ['location', 'city', 'state', 'country']):
                    if 'country' in label:
                        answer = country 
                    elif 'state' in label:
                        answer = state
                    elif 'city' in label:
                        answer = current_city if current_city else work_location
                    else:
                        answer = work_location
                else: 
                    answer = answer_common_questions(label,answer)
                try: 
                    select.select_by_visible_text(answer)
                except NoSuchElementException as e:
                    # Define similar phrases for common answers
                    possible_answer_phrases = []
                    if answer == 'Decline':
                        possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"]
                    elif 'yes' in answer.lower():
                        possible_answer_phrases = ["Yes", "Agree", "I do", "I have"]
                    elif 'no' in answer.lower():
                        possible_answer_phrases = ["No", "Disagree", "I don't", "I do not"]
                    else:
                        # Try partial matching for any answer
                        possible_answer_phrases = [answer]
                        # Add lowercase and uppercase variants
                        possible_answer_phrases.append(answer.lower())
                        possible_answer_phrases.append(answer.upper())
                        # Try without special characters
                        possible_answer_phrases.append(''.join(c for c in answer if c.isalnum()))
                    ##<
                    foundOption = False
                    for phrase in possible_answer_phrases:
                        for option in optionsText:
                            # Check if phrase is in option or option is in phrase (bidirectional matching)
                            if phrase.lower() in option.lower() or option.lower() in phrase.lower():
                                select.select_by_visible_text(option)
                                answer = option
                                foundOption = True
                                break
                    if not foundOption:
                        #TODO: Use AI to answer the question need to be implemented logic to extract the options for the question
                        print_lg(f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!')
                        select.select_by_index(randint(1, len(select.options)-1))
                        answer = select.first_selected_option.text
                        randomly_answered_questions.add((f'{label_org} [ {options} ]',"select"))
            questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
            continue
        
        # Check if it's a radio Question
        radio = try_xp(Question, './/fieldset[@data-test-form-builder-radio-button-form-component="true"]', False)
        if radio:
            prev_answer = None
            label = try_xp(radio, './/span[@data-test-form-builder-radio-button-form-component__title]', False)
            try: label = find_by_class(label, "visually-hidden", 2.0)
            except: pass
            label_org = label.text if label else "Unknown"
            answer = 'Yes'
            label = label_org.lower()

            label_org += ' [ '
            options = radio.find_elements(By.TAG_NAME, 'input')
            options_labels = []
            
            for option in options:
                id = option.get_attribute("id")
                option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                options_labels.append( f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>' ) # Saving option as "label <value>"
                if option.is_selected(): prev_answer = options_labels[-1]
                label_org += f' {options_labels[-1]},'

            if overwrite_previous_answers or prev_answer is None:
                if 'citizenship' in label or 'employment eligibility' in label: answer = us_citizenship
                elif 'veteran' in label or 'protected' in label: answer = veteran_status
                elif 'disability' in label or 'handicapped' in label: 
                    answer = disability_status
                else: answer = answer_common_questions(label,answer)
                foundOption = try_xp(radio, f".//label[normalize-space()='{answer}']", False)
                if foundOption: 
                    actions.move_to_element(foundOption).click().perform()
                else:    
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    ele = options[0]
                    answer = options_labels[0]
                    for phrase in possible_answer_phrases:
                        for i, option_label in enumerate(options_labels):
                            if phrase in option_label:
                                foundOption = options[i]
                                ele = foundOption
                                answer = f'Decline ({option_label})' if len(possible_answer_phrases) > 1 else option_label
                                break
                        if foundOption: break
                    # if answer == 'Decline':
                    #     answer = options_labels[0]
                    #     for phrase in ["Prefer not", "not want", "not wish"]:
                    #         foundOption = try_xp(radio, f".//label[normalize-space()='{phrase}']", False)
                    #         if foundOption:
                    #             answer = f'Decline ({phrase})'
                    #             ele = foundOption
                    #             break
                    actions.move_to_element(ele).click().perform()
                    if not foundOption: randomly_answered_questions.add((f'{label_org} ]',"radio"))
            else: answer = prev_answer
            questions_list.add((label_org+" ]", answer, "radio", prev_answer))
            continue
        
        # Check if it's a text question
        text = try_xp(Question, ".//input[@type='text']", False)
        if text: 
            do_actions = False
            label = try_xp(Question, ".//label[@for]", False)
            try: label = label.find_element(By.CLASS_NAME,'visually-hidden')
            except: pass
            label_org = label.text if label else "Unknown"
            answer = "" # years_of_experience
            label = label_org.lower()

            prev_answer = text.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'experience' in label or 'years' in label: answer = years_of_experience
                elif 'phone' in label or 'mobile' in label: answer = phone_number
                elif 'street' in label: answer = street
                elif 'city' in label or 'location' in label or 'address' in label:
                    answer = current_city if current_city else work_location
                    do_actions = True
                elif 'signature' in label: answer = full_name # 'signature' in label or 'legal name' in label or 'your name' in label or 'full name' in label: answer = full_name     # What if question is 'name of the city or university you attend, name of referral etc?'
                elif 'name' in label:
                    if 'full' in label: answer = full_name
                    elif 'first' in label and 'last' not in label: answer = first_name
                    elif 'middle' in label and 'last' not in label: answer = middle_name
                    elif 'last' in label and 'first' not in label: answer = last_name
                    elif 'employer' in label: answer = recent_employer
                    else: answer = full_name
                elif 'notice' in label:
                    if 'month' in label:
                        answer = notice_period_months
                    elif 'week' in label:
                        answer = notice_period_weeks
                    else: answer = notice_period
                elif 'salary' in label or 'compensation' in label or 'ctc' in label or 'pay' in label: 
                    if 'current' in label or 'present' in label:
                        if 'month' in label:
                            answer = current_ctc_monthly
                        elif 'lakh' in label:
                            answer = current_ctc_lakhs
                        else:
                            answer = current_ctc
                    else:
                        if 'month' in label:
                            answer = desired_salary_monthly
                        elif 'lakh' in label:
                            answer = desired_salary_lakhs
                        else:
                            answer = desired_salary
                elif 'linkedin' in label: answer = linkedIn
                elif 'website' in label or 'blog' in label or 'portfolio' in label or 'link' in label: answer = website
                elif 'scale of 1-10' in label: answer = confidence_level
                elif 'headline' in label: answer = linkedin_headline
                elif ('hear' in label or 'come across' in label) and 'this' in label and ('job' in label or 'position' in label): answer = "https://github.com/GodsScion/Auto_job_applier_linkedIn"
                elif 'state' in label or 'province' in label: answer = state
                elif 'zip' in label or 'postal' in label or 'code' in label: answer = zipcode
                elif 'country' in label: answer = country
                else: answer = answer_common_questions(label,answer)
                ##> ------ Yang Li : MARKYangL - Feature ------
                if answer == "":
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(aiClient, label_org, question_type="text", job_description=job_description, user_information_all=user_information_all)
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "text"))
                            answer = years_of_experience
                    else:
                        randomly_answered_questions.add((label_org, "text"))
                        answer = years_of_experience
                ##<
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
            continue

        # Check if it's a textarea question
        text_area = try_xp(Question, ".//textarea", False)
        if text_area:
            label = try_xp(Question, ".//label[@for]", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = ""
            prev_answer = text_area.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'summary' in label: answer = linkedin_summary
                elif 'cover' in label: answer = cover_letter
                if answer == "":
                ##> ------ Yang Li : MARKYangL - Feature ------
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(aiClient, label_org, question_type="textarea", job_description=job_description, user_information_all=user_information_all)
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "textarea"))
                            answer = ""
                    else:
                        randomly_answered_questions.add((label_org, "textarea"))
            text_area.clear()
            text_area.send_keys(answer)
            if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
            ##<
            continue

        # Check if it's a checkbox question
        checkbox = try_xp(Question, ".//input[@type='checkbox']", False)
        if checkbox:
            label = try_xp(Question, ".//span[@class='visually-hidden']", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = try_xp(Question, ".//label[@for]", False)  # Sometimes multiple checkboxes are given for 1 question, Not accounted for that yet
            answer = answer.text if answer else "Unknown"
            prev_answer = checkbox.is_selected()
            checked = prev_answer
            if not prev_answer:
                try:
                    actions.move_to_element(checkbox).click().perform()
                    checked = True
                except Exception as e: 
                    print_lg("Checkbox click failed!", e)
                    pass
            questions_list.add((f'{label} ([X] {answer})', checked, "checkbox", prev_answer))
            continue


    # Select todays date
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    # Collect important skills
    # if 'do you have' in label and 'experience' in label and ' in ' in label -> Get word (skill) after ' in ' from label
    # if 'how many years of experience do you have in ' in label -> Get word (skill) after ' in '

    return questions_list




def external_apply(pagination_element: WebElement, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    '''
    Function to open new tab and save external job application links
    '''
    global tabs_count, dailyEasyApplyLimitReached
    if effective_easy_apply_only:
        try:
            if "exceeded the daily application limit" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text: dailyEasyApplyLimitReached = True
        except: pass
        print_lg("Easy apply failed I guess!")
        if pagination_element != None: return True, application_link, tabs_count
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]"))).click() # './/button[contains(span, "Apply") and not(span[contains(@class, "disabled")])]'
        wait_span_click(driver, "Continue", 1, True, False)
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        failed_job(job_id, job_link, resume, date_listed, "Probably didn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count



def follow_company(modal: WebDriver = driver) -> None:
    '''
    Function to follow or un-follow easy applied companies based om `follow_companies`
    '''
    try:
        follow_checkbox_input = try_xp(modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False)
        if follow_checkbox_input and follow_checkbox_input.is_selected() != follow_companies:
            try_xp(modal, ".//label[@for='follow-company-checkbox']")
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)
    


#< Failed attempts logging
def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Function to update failed jobs list in excel
    '''
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Job Link':truncate_for_csv(job_link), 'Resume Tried':truncate_for_csv(resume), 'Date listed':truncate_for_csv(date_listed), 'Date Tried':datetime.now(), 'Assumed Reason':truncate_for_csv(error), 'Stack Trace':truncate_for_csv(exception), 'External Job link':truncate_for_csv(application_link), 'Screenshot Name':truncate_for_csv(screenshot_name)})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert("Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    '''
    Function to to take screenshot for debugging
    - Returns screenshot name as String
    '''
    screenshot_name = "{} - {} - {}.png".format( job_id, failedAt, str(datetime.now()) )
    path = logs_folder_path+"/screenshots/"+screenshot_name.replace(":",".")
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//","/"))
    return screenshot_name
#>



def submitted_jobs(job_id: str, title: str, company: str, work_location: str, work_style: str, description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
                   skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], hr_link: str | Literal['Unknown'], resume: str, 
                   reposted: bool, date_listed: datetime | Literal['Unknown'], date_applied:  datetime | Literal['Pending'], job_link: str, application_link: str, 
                   questions_list: set | None, connect_request: Literal['In Development']) -> None:
    '''
    Function to create or update the Applied jobs CSV file, once the application is submitted successfully
    '''
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':truncate_for_csv(job_id), 'Title':truncate_for_csv(title), 'Company':truncate_for_csv(company), 'Work Location':truncate_for_csv(work_location), 'Work Style':truncate_for_csv(work_style), 
                            'About Job':truncate_for_csv(description), 'Experience required': truncate_for_csv(experience_required), 'Skills required':truncate_for_csv(skills), 
                                'HR Name':truncate_for_csv(hr_name), 'HR Link':truncate_for_csv(hr_link), 'Resume':truncate_for_csv(resume), 'Re-posted':truncate_for_csv(reposted), 
                                'Date Posted':truncate_for_csv(date_listed), 'Date Applied':truncate_for_csv(date_applied), 'Job Link':truncate_for_csv(job_link), 
                                'External Job link':truncate_for_csv(application_link), 'Questions Found':truncate_for_csv(questions_list), 'Connect Request':truncate_for_csv(connect_request)})
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        pyautogui.alert("Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")



# Function to discard the job application
def discard_job() -> None:
    actions.send_keys(Keys.ESCAPE).perform()
    wait_span_click(driver, 'Discard', 2)






# Function to apply to jobs
def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids() if is_apply_mode else set()
    existing_lead_job_ids = get_existing_lead_job_ids() if is_extractor_mode and icp_dedupe_by_job_id else set()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume
    global jobs_scanned_count, icp_matched_count, icp_saved_count
    current_city = current_city.strip()

    if randomize_search_order:  shuffle(search_terms)
    for searchTerm in search_terms:
        driver.get(f"https://www.linkedin.com/jobs/search/?keywords={searchTerm}")
        print_lg("\n________________________________________________________________________________________________________________________\n")
        print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n\n')

        apply_filters()

        current_count = 0
        try:
            while current_count < switch_number:
                # Wait until job listings are loaded
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))

                pagination_element, current_page = get_page_info()

                # Find all job listings in current page
                buffer(3)
                job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")  

            
                for job in job_listings:
                    try:
                        import json as _json
                        from datetime import datetime as _dt
                        _stats = {
                            "total_runs": "Live Run",
                            "jobs_scanned": jobs_scanned_count,
                            "icp_leads_matched": icp_matched_count,
                            "icp_leads_saved": icp_saved_count,
                            "icp_leads_file": str(icp_leads_run_file_name),
                            "easy_applied": easy_applied_count,
                            "external_jobs": external_jobs_count,
                            "total_applied_or_collected": easy_applied_count + external_jobs_count,
                            "failed_jobs": failed_count,
                            "irrelevant_skipped": skip_count,
                            "timestamp": _dt.now().isoformat()
                        }
                        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_stats.json"), "w", encoding="utf-8") as _f:
                            _json.dump(_stats, _f, indent=2)
                    except Exception:
                        pass

                    if keep_screen_awake: pyautogui.press('shiftright')
                    if current_count >= switch_number: break
                    print_lg("\n-@-\n")
                    jobs_scanned_count += 1

                    job_id,title,company,work_location,work_style,skip = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                    
                    if skip: continue
                    # Redundant fail safe check for applied jobs!
                    if is_apply_mode:
                        try:
                            if job_id in applied_jobs or find_by_class(driver, "jobs-s-apply__application-link", 2):
                                print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
                                continue
                        except Exception as e:
                            print_lg(f'Trying to Apply to "{title} | {company}" job. Job ID: {job_id}')

                    job_link = "https://www.linkedin.com/jobs/view/"+job_id
                    application_link = "Easy Applied"
                    date_applied = "Pending"
                    hr_link = "Unknown"
                    hr_name = "Unknown"
                    connect_request = "In Development" # Still in development
                    date_listed = "Unknown"
                    skills = "Needs an AI" # Still in development
                    resume = "Pending"
                    reposted = False
                    questions_list = None
                    screenshot_name = "Not Available"

                    jobs_top_card = None
                    if is_apply_mode:
                        try:
                            rejected_jobs, blacklisted_companies, jobs_top_card = check_blacklist(rejected_jobs,job_id,company,blacklisted_companies)
                        except ValueError as e:
                            print_lg(e, 'Skipping this job!\n')
                            failed_job(job_id, job_link, resume, date_listed, "Found Blacklisted words in About Company", e, "Skipped", screenshot_name)
                            skip_count += 1
                            continue
                        except Exception as e:
                            print_lg("Failed to scroll to About Company!")
                    else:
                        try:
                            jobs_top_card = try_find_by_classes(driver, [
                                "job-details-jobs-unified-top-card__primary-description-container",
                                "job-details-jobs-unified-top-card__primary-description",
                                "jobs-unified-top-card__primary-description",
                                "jobs-details__main-content"
                            ])
                        except Exception:
                            jobs_top_card = None



                    # Hiring Manager info
                    try:
                        hr_info_card = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, "hirer-card__hirer-information")))
                        hr_link = hr_info_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        hr_name = hr_info_card.find_element(By.TAG_NAME, "span").text
                        # if connect_hr:
                        #     driver.switch_to.new_window('tab')
                        #     driver.get(hr_link)
                        #     wait_span_click("More")
                        #     wait_span_click("Connect")
                        #     wait_span_click("Add a note")
                        #     message_box = driver.find_element(By.XPATH, "//textarea")
                        #     message_box.send_keys(connect_request_message)
                        #     if close_tabs: driver.close()
                        #     driver.switch_to.window(linkedIn_tab) 
                        # def message_hr(hr_info_card):
                        #     if not hr_info_card: return False
                        #     hr_info_card.find_element(By.XPATH, ".//span[normalize-space()='Message']").click()
                        #     message_box = driver.find_element(By.XPATH, "//div[@aria-label='Write a message…']")
                        #     message_box.send_keys()
                        #     try_xp(driver, "//button[normalize-space()='Send']")        
                    except Exception as e:
                        print_lg(f'HR info was not given for "{title}" with Job ID: {job_id}!')
                        # print_lg(e)


                    # Calculation of date posted
                    try:
                        # try: time_posted_text = find_by_class(driver, "jobs-unified-top-card__posted-date", 2).text
                        # except: 
                        time_posted_text = jobs_top_card.find_element(By.XPATH, './/span[contains(normalize-space(), " ago")]').text
                        print("Time Posted: " + time_posted_text)
                        if time_posted_text.__contains__("Reposted"):
                            reposted = True
                            time_posted_text = time_posted_text.replace("Reposted", "")
                        date_listed = calculate_date_posted(time_posted_text.strip())
                    except Exception as e:
                        print_lg("Failed to calculate the date posted!",e)


                    description, experience_required, skip, reason, message = get_job_description(apply_filters_for_application=is_apply_mode)
                    if is_apply_mode and skip:
                        print_lg(message)
                        failed_job(job_id, job_link, resume, date_listed, reason, message, "Skipped", screenshot_name)
                        rejected_jobs.add(job_id)
                        skip_count += 1
                        continue

                    company_context, company_size_raw, company_industry_raw = extract_company_context()
                    if is_extractor_mode:
                        lead_match, icp_score, match_reasons, reject_reasons, matched_keywords = evaluate_icp_lead(
                            title=title,
                            description=description if isinstance(description, str) else "",
                            company_context=company_context,
                            company_size_raw=company_size_raw,
                            company_industry_raw=company_industry_raw
                        )
                        if lead_match:
                            icp_matched_count += 1
                            if (not icp_dedupe_by_job_id) or (job_id not in existing_lead_job_ids):
                                save_icp_lead(
                                    search_term=searchTerm,
                                    job_id=job_id,
                                    title=title,
                                    company=company,
                                    company_size_raw=company_size_raw,
                                    company_industry_raw=company_industry_raw,
                                    work_location=work_location,
                                    job_link=job_link,
                                    hr_name=hr_name,
                                    hr_link=hr_link,
                                    icp_score=icp_score,
                                    match_reasons=match_reasons,
                                    matched_keywords=matched_keywords,
                                    description=description if isinstance(description, str) else "",
                                    company_context=company_context,
                                )
                                existing_lead_job_ids.add(job_id)
                                icp_saved_count += 1
                                print_lg(f'ICP lead saved for "{title} | {company}" with score {icp_score}. Job ID: {job_id}')
                            else:
                                print_lg(f'ICP lead already exists, skipped duplicate Job ID: {job_id}')
                        else:
                            print_lg(f'ICP not matched for Job ID {job_id}. Score: {icp_score}. Reason(s): {" | ".join(reject_reasons)}')

                    if not is_apply_mode:
                        continue

                    
                    if use_AI and description != "Unknown":
                        ##> ------ Yang Li : MARKYangL - Feature ------
                        try:
                            if ai_provider.lower() == "openai":
                                skills = ai_extract_skills(aiClient, description)
                            elif ai_provider.lower() == "deepseek":
                                skills = deepseek_extract_skills(aiClient, description)
                            elif ai_provider.lower() == "gemini":
                                skills = gemini_extract_skills(aiClient, description)
                            else:
                                skills = "In Development"
                            print_lg(f"Extracted skills using {ai_provider} AI")
                        except Exception as e:
                            print_lg("Failed to extract skills:", e)
                            skills = "Error extracting skills"
                        ##<

                    uploaded = False
                    # Case 1: Easy Apply Button
                    if try_xp(driver, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'Easy')]"):
                        try: 
                            try:
                                errored = ""
                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                wait_span_click(modal, "Next", 1)
                                # if description != "Unknown":
                                #     resume = create_custom_resume(description)
                                resume = "Previous resume"
                                next_button = True
                                questions_list = set()
                                next_counter = 0
                                while next_button:
                                    next_counter += 1
                                    if next_counter >= 15: 
                                        if pause_at_failed_question:
                                            screenshot(driver, job_id, "Needed manual intervention for failed question")
                                            pyautogui.alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed", "Continue")
                                            next_counter = 1
                                            continue
                                        if questions_list: print_lg("Stuck for one or some of the following questions...", questions_list)
                                        screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                        errored = "stuck"
                                        raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")
                                    questions_list = answer_questions(modal, questions_list, work_location, job_description=description)
                                    if useNewResume and not uploaded: uploaded, resume = upload_resume(modal, default_resume_path)
                                    try: next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Review"]') 
                                    except NoSuchElementException:  next_button = modal.find_element(By.XPATH, './/button[contains(span, "Next")]')
                                    try: next_button.click()
                                    except ElementClickInterceptedException: break    # Happens when it tries to click Next button in About Company photos section
                                    buffer(click_gap)

                            except NoSuchElementException: errored = "nose"
                            finally:
                                if questions_list and errored != "stuck": 
                                    print_lg("Answered the following questions...", questions_list)
                                    print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                                wait_span_click(driver, "Review", 1, scrollTop=True)
                                cur_pause_before_submit = pause_before_submit
                                if errored != "stuck" and cur_pause_before_submit:
                                    decision = pyautogui.confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                                    if decision == "Discard Application": raise Exception("Job application discarded by user!")
                                    pause_before_submit = False if "Disable Pause" == decision else True
                                    # try_xp(modal, ".//span[normalize-space(.)='Review']")
                                follow_company(modal)
                                if wait_span_click(driver, "Submit application", 2, scrollTop=True): 
                                    date_applied = datetime.now()
                                    if not wait_span_click(driver, "Done", 2): actions.send_keys(Keys.ESCAPE).perform()
                                elif errored != "stuck" and cur_pause_before_submit and "Yes" in pyautogui.confirm("You submitted the application, didn't you 😒?", "Failed to find Submit Application!", ["Yes", "No"]):
                                    date_applied = datetime.now()
                                    wait_span_click(driver, "Done", 2)
                                else:
                                    print_lg("Since, Submit Application failed, discarding the job application...")
                                    # if screenshot_name == "Not Available":  screenshot_name = screenshot(driver, job_id, "Failed to click Submit application")
                                    # else:   screenshot_name = [screenshot_name, screenshot(driver, job_id, "Failed to click Submit application")]
                                    if errored == "nose": raise Exception("Failed to click Submit application 😑")


                        except Exception as e:
                            print_lg("Failed to Easy apply!")
                            # print_lg(e)
                            critical_error_log("Somewhere in Easy Apply process",e)
                            failed_job(job_id, job_link, resume, date_listed, "Problem in Easy Applying", e, application_link, screenshot_name)
                            failed_count += 1
                            discard_job()
                            continue
                    else:
                        # Case 2: Apply externally
                        skip, application_link, tabs_count = external_apply(pagination_element, job_id, job_link, resume, date_listed, application_link, screenshot_name)
                        if dailyEasyApplyLimitReached:
                            print_lg("\n###############  Daily application limit for Easy Apply is reached!  ###############\n")
                            return
                        if skip: continue

                    submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)
                    if uploaded:   useNewResume = False

                    print_lg(f'Successfully saved "{title} | {company}" job. Job ID: {job_id} info')
                    current_count += 1
                    if application_link == "Easy Applied": easy_applied_count += 1
                    else:   external_jobs_count += 1
                    applied_jobs.add(job_id)



                # Switching to next page
                if pagination_element == None:
                    print_lg("Couldn't find pagination element, probably at the end page of results!")
                    break
                try:
                    pagination_element.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']").click()
                    print_lg(f"\n>-> Now on Page {current_page+1} \n")
                except NoSuchElementException:
                    print_lg(f"\n>-> Didn't find Page {current_page+1}. Probably at the end page of results!\n")
                    break

        except (NoSuchWindowException, WebDriverException) as e:
            print_lg("Browser window closed or session is invalid. Ending application process.", e)
            raise e # Re-raise to be caught by main
        except Exception as e:
            print_lg("Failed to find Job listings!")
            critical_error_log("In Applier", e)
            try:
                print_lg(driver.page_source, pretty=True)
            except Exception as page_source_error:
                print_lg(f"Failed to get page source, browser might have crashed. {page_source_error}")
            # print_lg(e)

        
def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    print_lg("\n########################################################################################################################\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(f"Lead extraction mode: {lead_extraction_mode} | ICP match mode: {icp_match_mode} | ICP threshold: {icp_score_threshold}")
    print_lg(f"ICP leads output file: {icp_leads_run_file_name}")
    print_lg(f"Using search terms source: {'config/icp.py -> icp_search_terms' if using_icp_search_terms else 'config/search.py -> search_terms'}")
    print_lg(f"Using search location source: {'config/icp.py -> icp_search_location' if using_icp_search_location else 'config/search.py -> search_location'}")
    print_lg(f"Current filters: date_posted='{effective_date_posted}', sort_by='{effective_sort_by}', salary='{effective_salary}', easy_apply_only='{effective_easy_apply_only}', experience_level='{effective_experience_level}', job_type='{effective_job_type}', on_site='{effective_on_site}'")
    apply_to_jobs(effective_search_terms)
    print_lg("########################################################################################################################\n")
    if not dailyEasyApplyLimitReached:
        print_lg("Sleeping for 10 min...")
        sleep(300)
        print_lg("Few more min... Gonna start with in next 5 min...")
        sleep(300)
    buffer(3)
    return total_runs + 1



chatGPT_tab = False
linkedIn_tab = False

def main() -> None:
    total_runs = 1
    try:
        global linkedIn_tab, tabs_count, useNewResume, aiClient, icp_leads_run_file_name
        global effective_date_posted, effective_sort_by
        alert_title = "Error Occurred. Closing Browser!"
        validate_config()

        icp_leads_run_file_name = build_run_scoped_icp_leads_file_name()
        make_directories([icp_leads_run_file_name])
        initialize_icp_leads_file()
        print_lg(f"ICP leads for this run will be saved at: {icp_leads_run_file_name}")
        
        if not os.path.exists(default_resume_path):
            print_lg(f"Warning: Default resume '{default_resume_path}' is missing.")
            useNewResume = False
        
        # Login to LinkedIn
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()
        
        linkedIn_tab = driver.current_window_handle

        # # Login to ChatGPT in a new tab for resume customization
        # if use_resume_generator:
        #     try:
        #         driver.switch_to.new_window('tab')
        #         driver.get("https://chat.openai.com/")
        #         if not is_logged_in_GPT(): login_GPT()
        #         open_resume_chat()
        #         global chatGPT_tab
        #         chatGPT_tab = driver.current_window_handle
        #     except Exception as e:
        #         print_lg("Opening OpenAI chatGPT tab failed!")
        if use_AI:
            if ai_provider == "openai":
                aiClient = ai_create_openai_client()
            ##> ------ Yang Li : MARKYangL - Feature ------
            # Create DeepSeek client
            elif ai_provider == "deepseek":
                aiClient = deepseek_create_client()
            elif ai_provider == "gemini":
                aiClient = gemini_create_client()
            ##<

            try:
                about_company_for_ai = " ".join([word for word in (first_name+" "+last_name).split() if len(word) > 3])
                print_lg(f"Extracted about company info for AI: '{about_company_for_ai}'")
            except Exception as e:
                print_lg("Failed to extract about company info!", e)
        
        # Start applying to jobs
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)
        while(run_non_stop):
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                if effective_date_posted in date_options:
                    effective_date_posted = date_options[date_options.index(effective_date_posted)+1 if date_options.index(effective_date_posted)+1 > len(date_options) else -1] if stop_date_cycle_at_24hr else date_options[0 if date_options.index(effective_date_posted)+1 >= len(date_options) else date_options.index(effective_date_posted)+1]
            if alternate_sortby:
                effective_sort_by = "Most recent" if effective_sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)
                effective_sort_by = "Most recent" if effective_sort_by == "Most relevant" else "Most relevant"
            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached:
                break
        

    except (NoSuchWindowException, WebDriverException) as e:
        print_lg("Browser window closed or session is invalid. Exiting.", e)
    except Exception as e:
        critical_error_log("In Applier Main", e)
    finally:
        summary = "Total runs: {}\nJobs scanned: {}\nICP leads matched: {}\nICP leads saved: {}\nJobs Easy Applied: {}\nExternal job links collected: {}\nTotal applied or collected: {}\nFailed jobs: {}\nIrrelevant jobs skipped: {}\n".format(total_runs, jobs_scanned_count, icp_matched_count, icp_saved_count, easy_applied_count, external_jobs_count, easy_applied_count + external_jobs_count, failed_count, skip_count)
        convert_csv_to_json(icp_leads_run_file_name, "leads.json")
        print_lg(summary)
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        print_lg("Jobs scanned:                   {}".format(jobs_scanned_count))
        print_lg("ICP leads matched:              {}".format(icp_matched_count))
        print_lg("ICP leads saved:                {}".format(icp_saved_count))
        print_lg("ICP leads file:                 {}".format(icp_leads_run_file_name))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg("Total applied or collected:     {}".format(easy_applied_count + external_jobs_count))
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))
        if randomly_answered_questions: print_lg("\n\nQuestions randomly answered:\n  {}  \n\n".format(";\n".join(str(question) for question in randomly_answered_questions)))

        # Save run stats to JSON for the Lead-contact dashboard
        import json as _json
        from datetime import datetime as _dt
        stats = {
            "total_runs": total_runs,
            "jobs_scanned": jobs_scanned_count,
            "icp_leads_matched": icp_matched_count,
            "icp_leads_saved": icp_saved_count,
            "icp_leads_file": str(icp_leads_run_file_name),
            "easy_applied": easy_applied_count,
            "external_jobs": external_jobs_count,
            "total_applied_or_collected": easy_applied_count + external_jobs_count,
            "failed_jobs": failed_count,
            "irrelevant_skipped": skip_count,
            "timestamp": _dt.now().isoformat(),
        }
        try:
            stats_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_stats.json")
            with open(stats_path, "w", encoding="utf-8") as sf:
                _json.dump(stats, sf, indent=2)
            print_lg(f"Run stats saved to {stats_path}")
        except Exception as se:
            print_lg(f"Warning: Could not save run_stats.json: {se}")

        print_lg("Closing the browser...")
        if tabs_count >= 10:
            print_lg("NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!")
        ##> ------ Yang Li : MARKYangL - Feature ------
        if use_AI and aiClient:
            try:
                if ai_provider.lower() == "openai":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "deepseek":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "gemini":
                    pass # Gemini client does not need to be closed
                print_lg(f"Closed {ai_provider} AI client.")
            except Exception as e:
                print_lg("Failed to close AI client:", e)
        ##<
        try:
            if driver:
                driver.quit()
        except WebDriverException as e:
            print_lg("Browser already closed.", e)
        except Exception as e: 
            critical_error_log("When quitting...", e)


if __name__ == "__main__":
    main()
