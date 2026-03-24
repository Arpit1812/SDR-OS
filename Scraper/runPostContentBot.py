"""
LinkedIn posts/content ICP lead extractor.

Navigates directly to:
  https://www.linkedin.com/search/results/content/?keywords=<term>

and scrapes ALL pages until pagination is exhausted.
icp_posts_max_pages is a safety ceiling only — set high (e.g. 9999) to scrape everything.
"""

import csv
import os
import re
import json
from datetime import datetime
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

import pyautogui
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from config.search import search_terms
from config.secrets import username, password
from config.icp import icp_search_terms
from config.icp_posts import (
    icp_posts_search_terms,
    icp_posts_max_pages,
    icp_posts_scroll_rounds,
    icp_posts_retry_limit,
    icp_posts_sleep_ms,
    icp_posts_detail_open_mode,
    icp_posts_leads_file_name,
    icp_posts_snippet_max_length,
)
from modules.open_chrome import driver, wait
from modules.clickers_and_finders import (
    scroll_to_view,
    text_input_by_ID,
    try_linkText,
    try_xp,
)
from modules.helpers import make_directories, print_lg, manual_login_retry, truncate_for_csv, sleep


RETRYABLE_EXCEPTIONS = (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException,
)

# ---------------------------------------------------------------------------
# Selector tiers — ordered most-specific to broadest so we get the tightest
# match first but always have a fallback.
# ---------------------------------------------------------------------------

# Card containers
CARD_XPATHS = [
    # Newer LinkedIn search layouts render cards as <div role="listitem"> (not <li>).
    "//main//*[@role='listitem' and (@componentkey or @data-view-name or @data-view-tracking-scope)]",
    "//main//*[@role='listitem']",
    "//li[contains(@class,'reusable-search__result-container')]",
    "//li[contains(@class,'search-results__result-item')]",
    "//li[@data-view-name='search-entity-result-universal-template']",
    "//div[contains(@class,'occludable-update')]",
    "//div[contains(@class,'entity-result')]",
    "//main//ul/li[.//*[contains(@class,'actor')]]",
    "//main//ul/li[.//time]",
    "//main//ul/li[.//a[contains(@href,'/posts/') or contains(@href,'/activity-') or contains(@href,'/feed/update/')]]",
]

# Post canonical URL anchors
POST_URL_XPATHS = [
    ".//a[contains(@href,'/posts/')]",
    ".//a[contains(@href,'/activity-')]",
    ".//a[contains(@href,'/feed/update/')]",
    ".//a[contains(@href,'linkedin.com/') and contains(@href,'activity')]",
    ".//a[contains(@href,'linkedin.com/')]",
    ".//a[@href]",
]

# Author /in/ profile anchors
AUTHOR_XPATHS = [
    ".//a[contains(@href,'linkedin.com/in/')]",
    ".//a[contains(@href,'/in/')]",
]

# Text snippet inside a card
SNIPPET_XPATHS = [
    ".//*[contains(@class,'update-components-text')]",
    ".//*[contains(@class,'break-words')]",
    ".//*[contains(@class,'entity-result__summary')]",
    ".//*[contains(@class,'feed-shared-text')]",
    ".//*[contains(@class,'commentary')]",
]

# Full post text on a detail page
DETAIL_TEXT_XPATHS = [
    "//div[contains(@class,'feed-shared-update-v2__description-wrapper')]",
    "//div[contains(@class,'update-components-text')]",
    "//div[contains(@class,'feed-shared-text')]",
    "//article",
    "//main",
]

# Pagination next-page controls
NEXT_PAGE_XPATHS = [
    "//button[contains(@aria-label,'Next') and not(@disabled)]",
    "//button[contains(@class,'artdeco-pagination__button--next') and not(@disabled)]",
    "//a[contains(@aria-label,'Next') and not(@aria-disabled='true')]",
]

GLOBAL_POST_LINK_XPATH = (
    "//main//a[contains(@href,'/feed/update/') "
    "or contains(@href,'/posts/') "
    "or contains(@href,'/activity-')]"
)

TRACKING_CARD_XPATHS = [
    "//*[@data-view-tracking-scope[contains(.,'FeedUpdateServedEvent')]]",
    "//*[@data-view-tracking-scope]",
]

# Tracking params to strip from URLs
_STRIP_PARAMS = {
    "trk", "trackingId", "lipi", "refId", "actorCompanyId",
    "utm_source", "utm_medium", "utm_campaign",
}


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def validate_posts_config() -> None:
    if not isinstance(icp_posts_max_pages, int) or icp_posts_max_pages < 1:
        raise ValueError("icp_posts_max_pages must be int >= 1.")
    if not isinstance(icp_posts_scroll_rounds, int) or icp_posts_scroll_rounds < 1:
        raise ValueError("icp_posts_scroll_rounds must be int >= 1.")
    if not isinstance(icp_posts_retry_limit, int) or icp_posts_retry_limit < 1:
        raise ValueError("icp_posts_retry_limit must be int >= 1.")
    if not isinstance(icp_posts_sleep_ms, int) or icp_posts_sleep_ms < 100:
        raise ValueError("icp_posts_sleep_ms must be int >= 100.")
    if icp_posts_detail_open_mode not in ("off", "same_tab", "new_tab"):
        raise ValueError("icp_posts_detail_open_mode must be: off | same_tab | new_tab.")
    if not isinstance(icp_posts_snippet_max_length, int) or icp_posts_snippet_max_length < 50:
        raise ValueError("icp_posts_snippet_max_length must be int >= 50.")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def effective_search_terms() -> list[str]:
    if isinstance(icp_posts_search_terms, list) and icp_posts_search_terms:
        return icp_posts_search_terms
    if isinstance(icp_search_terms, list) and icp_search_terms:
        return icp_search_terms
    return search_terms


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def parse_linkedin_post_age(text: str) -> tuple[str, str]:
    """
    Extract and normalize LinkedIn post age strings from card text.
    Returns: (raw_age, iso_date) where iso_date is YYYY-MM-DD or "".
    Supports formats like: "1w", "2d", "3mo", "1y", and also "* ago" strings.
    """
    s = normalize_space(text or "")
    if not s:
        return "", ""

    now = datetime.now()

    # "10 minutes ago", "1 week ago", etc.
    m = re.search(r"\b(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago\b", s, flags=re.IGNORECASE)
    if m:
        val = int(m.group(1))
        unit = m.group(2).lower()
        delta_days = 0
        if unit == "day":
            delta_days = val
        elif unit == "week":
            delta_days = 7 * val
        elif unit == "month":
            delta_days = 30 * val
        elif unit == "year":
            delta_days = 365 * val
        elif unit in ("hour", "minute", "second"):
            delta_days = 0
        raw = f"{val} {unit}{'' if val == 1 else 's'} ago"
        dt = (now - timedelta(days=delta_days)).date().isoformat()
        return raw, dt

    # LinkedIn shorthand: 3w, 2d, 5h, 30m, 4mo, 1y.
    m = re.search(r"\b(\d+)\s*(mo|[smhdwy])\b", s, flags=re.IGNORECASE)
    if not m:
        return "", ""

    val = int(m.group(1))
    unit = m.group(2).lower()
    raw = f"{val}{unit}"
    delta_days = 0
    if unit == "d":
        delta_days = val
    elif unit == "w":
        delta_days = 7 * val
    elif unit == "mo":
        delta_days = 30 * val
    elif unit == "y":
        delta_days = 365 * val
    elif unit in ("h", "m", "s"):
        delta_days = 0
    dt = (now - timedelta(days=delta_days)).date().isoformat()
    return raw, dt


def get_post_date_from_card(card) -> str:
    """
    Return YYYY-MM-DD when possible, else "".
    """
    try:
        # Prefer <time> aria-label if present.
        for t in card.find_elements(By.XPATH, ".//time"):
            aria = (t.get_attribute("aria-label") or "").strip()
            raw_age, iso = parse_linkedin_post_age(aria or t.text or "")
            if iso:
                return iso
        # Any element with an "ago" aria-label.
        for el in card.find_elements(By.XPATH, ".//*[@aria-label]"):
            aria = (el.get_attribute("aria-label") or "").strip()
            if "ago" in aria.lower():
                _, iso = parse_linkedin_post_age(aria)
                if iso:
                    return iso
    except Exception:
        pass

    try:
        raw_age, iso = parse_linkedin_post_age(getattr(card, "text", "") or "")
        return iso
    except Exception:
        return ""

def canonicalize_url(raw: str) -> str:
    if not raw:
        return ""
    try:
        p    = urlparse(raw.strip())
        qs   = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k not in _STRIP_PARAMS])
        path = p.path.rstrip("/") or "/"
        return urlunparse((p.scheme, p.netloc.lower(), path, "", qs, ""))
    except Exception:
        return raw.strip()


def absolutize_linkedin_href(href: str) -> str:
    h = (href or "").strip()
    if not h:
        return ""
    if h.startswith("//"):
        return "https:" + h
    if h.startswith("/"):
        return "https://www.linkedin.com" + h
    return h


def activity_url_from_blob(blob: str) -> str:
    """
    Best-effort extraction of a post/activity URL from arbitrary HTML/JSON blobs.
    """
    if not blob:
        return ""
    for pattern in (
        r"urn:li:activity:(\d{8,})",
        r"activity:(\d{8,})",
        r"updateEntityUrn=urn:li:activity:(\d{8,})",
    ):
        m = re.search(pattern, blob, flags=re.IGNORECASE)
        if m:
            return f"https://www.linkedin.com/feed/update/urn:li:activity:{m.group(1)}"
    return ""


def maybe_capture_post_url_by_opening(card) -> str:
    """
    Some search result cards don't expose a post URL in the DOM until opened.
    Best-effort: click the snippet area, then harvest the current URL or any
    post link in an opened dialog.
    """
    orig_url = driver.current_url or ""
    try:
        targets = []
        for xp in SNIPPET_XPATHS + [
            ".//*[contains(@class,'feed-shared-text')]",
            ".//*[contains(@class,'update-components-text')]",
            ".//*[contains(@class,'break-words')]",
            ".//span[contains(.,'… more') or contains(.,'... more') or contains(.,'…more') or contains(.,'...more')]",
        ]:
            try:
                els = card.find_elements(By.XPATH, xp)
                if els:
                    targets.append(els[0])
            except Exception:
                continue
        if not targets:
            targets = [card]

        scroll_to_view(driver, targets[0])
        try:
            driver.execute_script("arguments[0].click();", targets[0])
        except Exception:
            try:
                targets[0].click()
            except Exception:
                return ""

        _sleep()

        cur = driver.current_url or ""
        if cur and cur != orig_url and _looks_like_post_url(cur):
            url = canonicalize_url(cur)
            try:
                driver.back()
                _wait_body()
            except Exception:
                pass
            return url

        try:
            dialog = driver.find_element(By.XPATH, "//*[@role='dialog']")
            for a in dialog.find_elements(By.XPATH, ".//a[@href]"):
                href = absolutize_linkedin_href(a.get_attribute("href") or "")
                if href and _looks_like_post_url(href):
                    return canonicalize_url(href)
            html = (dialog.get_attribute("outerHTML") or "")[:25000]
            url = activity_url_from_blob(html)
            if url:
                return canonicalize_url(url)
        except Exception:
            pass

    finally:
        try:
            driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}));")
        except Exception:
            pass
    return ""


def _clipboard_set(text: str) -> None:
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text or "")
        root.update()
        root.destroy()
    except Exception:
        # Fallback: Windows clipboard via PowerShell.
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $args[0]", text or ""],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            pass


def _clipboard_get() -> str:
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return (text or "").strip()
    except Exception:
        # Fallback: Windows clipboard via PowerShell.
        try:
            import subprocess
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                return (res.stdout or "").strip()
        except Exception:
            pass
        return ""


def _find_visible_menu():
    try:
        menus = driver.find_elements(
            By.XPATH,
            "//*[@role='menu' or @role='dialog' or contains(@class,'artdeco-dropdown__content') or contains(@class,'artdeco-dropdown__content-inner')]",
        )
        for m in reversed(menus):
            try:
                if m.is_displayed():
                    return m
            except Exception:
                continue
    except Exception:
        pass
    return None


def _find_visible_copy_link_node():
    try:
        nodes = driver.find_elements(
            By.XPATH,
            "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy link')]",
        )
        for n in reversed(nodes):
            try:
                if n.is_displayed():
                    return n
            except Exception:
                continue
    except Exception:
        pass
    return None


def _find_visible_link_copied_toast():
    try:
        nodes = driver.find_elements(By.XPATH, "//*[@id='artdeco-toasts']//*[self::*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copied')]] | //*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copied to clipboard')] | //*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'link copied')]")
        for n in reversed(nodes):
            try:
                if not n.is_displayed():
                    continue
                # Prefer toast/alert-like containers.
                role = (n.get_attribute("role") or "").strip().lower()
                cls = (n.get_attribute("class") or "").strip().lower()
                aria_live = (n.get_attribute("aria-live") or "").strip().lower()
                if role in ("alert", "status") or aria_live or "toast" in cls:
                    return n
            except Exception:
                continue
        # Fallback: return the last visible matching node.
        for n in reversed(nodes):
            try:
                if n.is_displayed():
                    return n
            except Exception:
                continue
    except Exception:
        pass
    return None


def _dismiss_link_copied_toast() -> None:
    toast = _find_visible_link_copied_toast()
    if not toast:
        return
    # Try common dismiss buttons.
    for xp in (
        ".//button[contains(@aria-label,'Dismiss') or contains(@aria-label,'dismiss')]",
        ".//button[contains(@aria-label,'Close') or contains(@aria-label,'close')]",
        ".//button[contains(@class,'artdeco-toast-item__dismiss')]",
        ".//button[.//li-icon[contains(@type,'close')]]",
    ):
        try:
            btns = toast.find_elements(By.XPATH, xp)
            if btns:
                try:
                    driver.execute_script("arguments[0].click();", btns[0])
                except Exception:
                    btns[0].click()
                _sleep()
                return
        except Exception:
            continue
    # Fallback: escape.
    try:
        driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}));")
    except Exception:
        pass


def _extract_view_post_url_from_toast() -> str:
    toast = _find_visible_link_copied_toast()
    if not toast:
        return ""
    try:
        links = toast.find_elements(By.XPATH, ".//a[@href]")
        for a in links:
            label = normalize_space(a.text or a.get_attribute("aria-label") or "")
            href = absolutize_linkedin_href(a.get_attribute("href") or "")
            if not href:
                continue
            if "view post" in label.lower() or _looks_like_post_url(href):
                return canonicalize_url(href)
    except Exception:
        pass
    return ""


def maybe_capture_post_url_by_copy_link_menu(card) -> str:
    """
    Fallback: use the card's "..." menu -> "Copy link to post", then read clipboard.
    """
    sentinel = f"__li_clipboard_sentinel_{datetime.now().timestamp()}__"
    _clipboard_set(sentinel)

    try:
        menu_btn = None
        candidates = []
        try:
            card_rect = getattr(card, "rect", None) or {}
            card_x = float(card_rect.get("x", 0) or 0)
            card_y = float(card_rect.get("y", 0) or 0)
        except Exception:
            card_x = card_y = 0.0

        # Prefer explicit overflow/ellipsis buttons near the top-right of the card.
        try:
            buttons = card.find_elements(By.XPATH, ".//button")
        except Exception:
            buttons = []

        # Strong signal: LinkedIn often labels the "..." button like:
        # "Open control menu for post by <name>"
        for b in buttons:
            try:
                aria = (b.get_attribute("aria-label") or "").strip().lower()
                if "control menu" in aria and "post" in aria:
                    menu_btn = b
                    break
            except Exception:
                continue

        for b in buttons:
            try:
                aria = (b.get_attribute("aria-label") or "").strip()
                cls = (b.get_attribute("class") or "").strip().lower()
                haspopup = (b.get_attribute("aria-haspopup") or "").strip().lower()
                txt = normalize_space(getattr(b, "text", "") or "")[:40]
                rect = getattr(b, "rect", None) or {}
                bx = float(rect.get("x", 0) or 0)
                by = float(rect.get("y", 0) or 0)
                x_off = bx - card_x
                y_off = by - card_y

                # Detect "..." icon inside button.
                ellipsis_icon = False
                try:
                    if b.find_elements(By.XPATH, ".//li-icon[contains(@type,'ellipsis') or contains(@type,'overflow')]"):
                        ellipsis_icon = True
                    elif b.find_elements(By.XPATH, ".//*[name()='svg' and (contains(@data-test-icon,'overflow') or contains(@data-test-icon,'ellipsis'))]"):
                        ellipsis_icon = True
                except Exception:
                    ellipsis_icon = False

                label_match = any(s in aria.lower() for s in ("control menu", "more", "actions", "options", "overflow", "ellipsis"))
                class_match = any(s in cls for s in ("control-menu", "dropdown__trigger", "artdeco-dropdown", "overflow"))
                topish = y_off >= -5 and y_off <= 160

                if (ellipsis_icon or label_match or class_match) and (haspopup == "menu" or ellipsis_icon or label_match) and topish:
                    # Score: top-most, then right-most.
                    score = (y_off, -x_off)
                    candidates.append((score, b, aria, txt))
            except Exception:
                continue

        if not menu_btn and candidates:
            candidates.sort(key=lambda t: t[0])
            menu_btn = candidates[0][1]
        else:
            # Fallback selectors (kept narrow to avoid reaction bars).
            for xp in (
                ".//button[@aria-haspopup='menu'][1]",
                ".//button[contains(@aria-label,'control menu') or contains(@aria-label,'Control menu')][1]",
                ".//button[contains(@aria-label,'More') or contains(@aria-label,'more')][1]",
                ".//button[contains(@class,'artdeco-dropdown__trigger')][1]",
            ):
                try:
                    els = card.find_elements(By.XPATH, xp)
                    if els:
                        menu_btn = els[0]
                        break
                except Exception:
                    continue

        if not menu_btn:
            try:
                sample = []
                for b in buttons[:12]:
                    aria = normalize_space((b.get_attribute("aria-label") or ""))[:40]
                    txt = normalize_space(getattr(b, "text", "") or "")[:20]
                    if aria or txt:
                        sample.append(f"{aria or txt}")
                if sample:
                    print_lg(f"DEBUG: no overflow menu button found; button labels sample={sample}")
            except Exception:
                pass
            return ""

        scroll_to_view(driver, menu_btn)
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(driver).move_to_element(menu_btn).pause(0.1).click(menu_btn).perform()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", menu_btn)
            except Exception:
                try:
                    menu_btn.click()
                except Exception:
                    return ""

        _sleep()
        try:
            # Ensure some overflow UI is open before searching items.
            wait.until(lambda d: (
                d.find_elements(By.XPATH, "//*[@role='menu']") or
                d.find_elements(By.XPATH, "//*[@role='dialog']") or
                d.find_elements(By.XPATH, "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy link')]")
            ))
        except Exception:
            # Retry once with a JS click if the first click hit the wrong target.
            try:
                driver.execute_script("arguments[0].click();", menu_btn)
                _sleep()
            except Exception:
                pass

        # Prefer a panel referenced by aria-controls if available.
        menu = None
        try:
            ctl = (menu_btn.get_attribute("aria-controls") or "").strip()
            if ctl:
                el = driver.find_element(By.ID, ctl)
                if el and el.is_displayed():
                    menu = el
        except Exception:
            menu = None
        if not menu:
            menu = _find_visible_menu()

        # Find a "Copy link" menuitem inside this menu (case-insensitive).
        item = None
        try:
            if menu:
                spans = menu.find_elements(
                    By.XPATH,
                    ".//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy link')]",
                )
                if spans:
                    item = spans[0]
        except Exception:
            item = None

        # As a fallback, grab any visible "copy link" node on the page.
        if not item:
            item = _find_visible_copy_link_node()

        if not item:
            try:
                menu_text = normalize_space(" ".join([normalize_space(e.text) for e in driver.find_elements(By.XPATH, "//*[@role='menu']//span")]) or "")
                if menu_text:
                    print_lg(f"DEBUG: overflow menu opened but no 'Copy link' item found; menu_text='{menu_text[:200]}'")
            except Exception:
                pass
            try:
                print_lg("DEBUG: menu button clicked but no visible 'copy link' item appeared.")
            except Exception:
                pass
            return ""

        # Click the whole menuitem (more reliable than clicking the span).
        try:
            menuitem = item.find_element(By.XPATH, "ancestor::*[@role='menuitem'][1]")
        except Exception:
            try:
                menuitem = item.find_element(By.XPATH, "ancestor::button[1]")
            except Exception:
                menuitem = None

        try:
            if menuitem is not None:
                driver.execute_script("arguments[0].click();", menuitem)
            else:
                driver.execute_script("arguments[0].click();", item)
        except Exception:
            try:
                if menuitem is not None:
                    menuitem.click()
                else:
                    item.click()
            except Exception:
                return ""

        _sleep()

        # If LinkedIn shows a toast with "View post", prefer that (no clipboard dependency).
        try:
            wait.until(lambda d: _find_visible_link_copied_toast() is not None)
        except Exception:
            pass
        view_url = ""
        try:
            view_url = _extract_view_post_url_from_toast()
        except Exception:
            view_url = ""
        if view_url:
            print_lg(f"DEBUG: extracted post URL from toast: {view_url}")
            return canonicalize_url(view_url)

        # Poll clipboard for a change; sometimes it takes a moment.
        copied = ""
        for _ in range(10):
            copied = _clipboard_get()
            if copied and copied != sentinel:
                break
            _sleep()

        if copied and copied != sentinel:
            copied = absolutize_linkedin_href(copied)
            if _looks_like_post_url(copied):
                print_lg(f"DEBUG: extracted post URL from clipboard: {copied}")
                return canonicalize_url(copied)
            # If LinkedIn copies a short redirect URL, still keep it.
            if "lnkd.in/" in (copied or "").lower():
                print_lg(f"DEBUG: extracted lnkd.in URL from clipboard: {copied}")
                return copied
        else:
            # Fallback: toast often contains a "View post" link with the permalink.
            try:
                view_url = _extract_view_post_url_from_toast()
                if view_url:
                    print_lg(f"DEBUG: extracted post URL from toast (clipboard unchanged): {view_url}")
                    return canonicalize_url(view_url)
            except Exception:
                pass
            try:
                print_lg(f"DEBUG: clipboard unchanged after 'Copy link' click (value='{(copied or '')[:120]}').")
            except Exception:
                pass
    finally:
        try:
            _dismiss_link_copied_toast()
        except Exception:
            pass
        try:
            driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}));")
        except Exception:
            pass
    return ""


def build_run_scoped_file_name(base_file: str) -> str:
    base_file = base_file.replace("\\", "/")
    dir_name  = os.path.dirname(base_file)
    stem, ext = os.path.splitext(os.path.basename(base_file))
    ext       = ext or ".csv"
    stamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(dir_name, f"{stem}__{stamp}{ext}").replace("\\", "/")


def _sleep() -> None:
    sleep(max(0.15, icp_posts_sleep_ms / 1000.0))


def _wait_body() -> None:
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        pass
    _sleep()


# ---------------------------------------------------------------------------
# Module state
# ---------------------------------------------------------------------------

_project_root  = os.path.dirname(os.path.abspath(__file__))
output_file    = os.path.join(_project_root, build_run_scoped_file_name(icp_posts_leads_file_name))
seen_post_urls: set[str] = set()
seen_post_keys: set[str] = set()


# ---------------------------------------------------------------------------
# CSV I/O
# ---------------------------------------------------------------------------

CSV_HEADERS = [
    "Linkedin Url", "Full Name", "Email", "Email Status",
    "Job Title", "Company Name", "Company Website",
    "City", "State", "Country", "Industry", "Keywords", "Employees",
    "Company City", "Company State", "Company Country",
    "Company Linkedin Url", "Company Twitter Url", "Company Facebook Url",
    "Company Phone Numbers", "Buying Intent", "Trigger", "follow-up 1", "Job Link",
    "Post Date",
]


def initialize_output_file() -> None:
    make_directories([output_file])
    with open(output_file, mode="a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if f.tell() == 0:
            w.writeheader()
    print_lg(f"Output file ready: {output_file}")


def load_existing_post_urls() -> None:
    if not os.path.exists(output_file):
        return
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                url = canonicalize_url((row.get("Job Link") or "").strip())
                profile = canonicalize_url((row.get("Linkedin Url") or "").strip())
                trigger = normalize_space((row.get("Trigger") or "").strip())
                if url:
                    seen_post_urls.add(url)
                    seen_post_keys.add(f"url::{url}")
                else:
                    if profile or trigger:
                        seen_post_keys.add(f"nou::{profile}::{trigger[:200]}")
        print_lg(f"Loaded {len(seen_post_urls)} already-seen post URLs.")
    except Exception as e:
        print_lg("Warning: could not read existing post URLs.", e)


def dedupe_key(profile_url: str, post_url: str, trigger: str) -> str:
    post_url = canonicalize_url((post_url or "").strip())
    if post_url:
        return f"url::{post_url}"
    profile_url = canonicalize_url((profile_url or "").strip())
    trigger = normalize_space((trigger or "").strip())[:200]
    return f"nou::{profile_url}::{trigger}"


def save_lead_row(
    profile_url: str,
    full_name: str,
    job_title: str,
    keywords: str,
    trigger: str,
    post_url: str,
    post_date: str,
) -> None:
    with open(output_file, mode="a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        w.writerow({
            "Linkedin Url"         : truncate_for_csv(profile_url),
            "Full Name"            : truncate_for_csv(full_name),
            "Email"                : "",
            "Email Status"         : "",
            "Job Title"            : truncate_for_csv(job_title),
            "Company Name"         : "",
            "Company Website"      : "",
            "City"                 : "",
            "State"                : "",
            "Country"              : "",
            "Industry"             : "",
            "Keywords"             : truncate_for_csv(keywords),
            "Employees"            : "",
            "Company City"         : "",
            "Company State"        : "",
            "Company Country"      : "",
            "Company Linkedin Url" : "",
            "Company Twitter Url"  : "",
            "Company Facebook Url" : "",
            "Company Phone Numbers": "",
            "Buying Intent"        : "",
            "Trigger"              : truncate_for_csv(trigger, max_length=icp_posts_snippet_max_length),
            "follow-up 1"          : "",
            "Job Link"             : truncate_for_csv(post_url),
            "Post Date"            : truncate_for_csv(post_date),
        })


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def is_logged_in() -> bool:
    url = driver.current_url or ""
    if "linkedin.com/feed" in url or "linkedin.com/search" in url:
        return True
    if try_linkText(driver, "Sign in"):
        return False
    if try_xp(driver, '//button[@type="submit" and contains(text(),"Sign in")]'):
        return False
    if try_linkText(driver, "Join now"):
        return False
    return True


def login_linkedin() -> None:
    print_lg("Session not authenticated — attempting login.")
    driver.get("https://www.linkedin.com/login")
    if username == "username@example.com" and password == "example_password":
        pyautogui.alert(
            "Default credentials in config/secrets.py. Please log in manually.",
            "Login Required", "OK",
        )
        manual_login_retry(is_logged_in, 2)
        return
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        text_input_by_ID(driver, "username", username, 1)
        text_input_by_ID(driver, "password", password, 1)
        driver.find_element(
            By.XPATH, '//button[@type="submit" and contains(text(),"Sign in")]'
        ).click()
        wait.until(EC.url_contains("linkedin.com"))
        _sleep()
    except Exception:
        manual_login_retry(is_logged_in, 2)


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def content_search_url(query: str) -> str:
    qs = urlencode({"keywords": query, "origin": "GLOBAL_SEARCH_HEADER"})
    return f"https://www.linkedin.com/search/results/content/?{qs}"


def is_content_context() -> bool:
    return "/search/results/content/" in (driver.current_url or "")


def navigate_to_content_search(query: str) -> bool:
    url = content_search_url(query)
    print_lg(f"Navigating → {url}")
    try:
        driver.get(url)
        _wait_body()
        # Give the page a moment to settle and load result elements
        try:
            wait.until(lambda d: (
                d.find_elements(By.XPATH, "//main//ul/li") or
                d.find_elements(By.XPATH, "//main//*[@role='listitem']") or
                d.find_elements(By.XPATH, GLOBAL_POST_LINK_XPATH) or
                d.find_elements(By.XPATH, "//*[@data-view-tracking-scope]") or
                d.find_elements(By.XPATH, "//*[contains(text(),'No results')]") or
                d.find_elements(By.XPATH, "//*[contains(@class,'search-results')]")
            ))
        except Exception:
            pass
        _sleep()
        ok = is_content_context()
        if not ok:
            print_lg(f"WARNING: current URL after nav = {driver.current_url}")
        return ok
    except Exception as e:
        print_lg(f"Navigation error for query '{query}': {e}")
        return False


def ensure_content_context(query: str) -> bool:
    if is_content_context():
        return True
    url = driver.current_url or ""
    if any(s in url for s in ("login", "checkpoint", "authwall", "uas/")):
        print_lg("Auth wall detected — attempting re-login.")
        manual_login_retry(is_logged_in, 2)
    return navigate_to_content_search(query)


# ---------------------------------------------------------------------------
# DOM extraction
# ---------------------------------------------------------------------------

def find_cards() -> list:
    """Return all result card elements using the first selector that yields results."""
    for xpath in CARD_XPATHS:
        try:
            cards = driver.find_elements(By.XPATH, xpath)
            if not cards:
                continue

            filtered = [c for c in cards if card_has_post_marker(c)]
            if filtered:
                print_lg(f"Cards via '{xpath}': {len(filtered)}")
                return filtered

            # If our marker logic is too strict for a new SDUI layout, prefer returning
            # the raw list so the per-card URL extraction logic can still succeed.
            if "role='listitem'" in xpath or "@role='listitem'" in xpath or "//*[@role='listitem']" in xpath:
                print_lg(
                    f"WARNING: cards matched '{xpath}' ({len(cards)}) but 0 passed card_has_post_marker; "
                    "falling back to raw cards."
                )
                try:
                    sample_n = min(3, len(cards))
                    for i in range(sample_n):
                        c = cards[i]
                        a_count = len(c.find_elements(By.XPATH, ".//a[@href]"))
                        t_count = len(c.find_elements(By.XPATH, ".//*[@data-view-tracking-scope]"))
                        time_count = len(c.find_elements(By.XPATH, ".//time"))
                        urn = (c.get_attribute("data-urn") or c.get_attribute("data-activity-urn") or c.get_attribute("data-id") or "")[:120]
                        preview = normalize_space(getattr(c, "text", "") or "")[:100]
                        print_lg(f"DEBUG card[{i}]: anchors={a_count} tracking={t_count} time={time_count} urn='{urn}' preview='{preview}'")
                except Exception:
                    pass
                return cards
        except Exception:
            continue
    # Debug: print a slice of the main element so we can identify the correct selector
    try:
        snippet = driver.find_element(By.TAG_NAME, "main").get_attribute("innerHTML")[:1200]
        print_lg(f"DEBUG <main> snippet:\n{snippet}")
    except Exception:
        pass
    try:
        role_listitems = len(driver.find_elements(By.XPATH, "//main//*[@role='listitem']"))
        tracking_items = len(driver.find_elements(By.XPATH, "//*[@data-view-tracking-scope]"))
        post_links     = len(driver.find_elements(By.XPATH, GLOBAL_POST_LINK_XPATH))
        print_lg(f"DEBUG counts: role=listitem={role_listitems} | tracking={tracking_items} | postlinks={post_links}")
    except Exception:
        pass
    print_lg("WARNING: No cards found on this page.")
    return []


def card_has_post_marker(card) -> bool:
    """
    Guard against generic layout list-items that are not actual post result cards.
    """
    try:
        # Fast path: any activity/post URL anchor.
        for xp in (
            ".//a[contains(@href,'/posts/')]",
            ".//a[contains(@href,'/activity-')]",
            ".//a[contains(@href,'/feed/update/')]",
        ):
            if card.find_elements(By.XPATH, xp):
                return True
    except Exception:
        pass

    # Fallback: activity URN markers.
    for attr in ("data-urn", "data-activity-urn", "data-id", "data-entity-urn"):
        try:
            val = (card.get_attribute(attr) or "").strip().lower()
            if "activity:" in val:
                return True
        except Exception:
            continue

    # SDUI layouts sometimes only include activity info in tracking payloads.
    try:
        scope = (card.get_attribute("data-view-tracking-scope") or "").strip()
        if scope:
            if "FeedUpdateServedEvent" in scope:
                return True
            if parse_activity_url_from_tracking_scope(scope):
                return True
    except Exception:
        pass

    try:
        for child in card.find_elements(By.XPATH, ".//*[@data-urn or @data-activity-urn or @data-id]"):
            urn = (
                child.get_attribute("data-urn")
                or child.get_attribute("data-activity-urn")
                or child.get_attribute("data-id")
                or ""
            ).strip().lower()
            if "activity:" in urn:
                return True
    except Exception:
        pass

    try:
        for child in card.find_elements(By.XPATH, ".//*[@data-view-tracking-scope]"):
            scope = (child.get_attribute("data-view-tracking-scope") or "").strip()
            if not scope:
                continue
            if "FeedUpdateServedEvent" in scope:
                return True
            if parse_activity_url_from_tracking_scope(scope):
                return True
    except Exception:
        pass

    # UI marker fallback: post cards typically contain a social-actions bar.
    # Use it as a weak signal to avoid filtering everything out.
    try:
        if card.find_elements(By.XPATH, ".//*[contains(@class,'social-actions') or contains(@class,'social-details') or contains(@class,'feed-shared-social-action-bar')]"):
            return True
    except Exception:
        pass

    # Last-ditch: scan HTML for an activity URN.
    try:
        html = (card.get_attribute("outerHTML") or "")[:25000]
        if activity_url_from_blob(html):
            return True
    except Exception:
        pass
    return False


def _looks_like_post_url(href: str) -> bool:
    h = (href or "").strip().lower()
    if not h:
        return False
    return (
        "/feed/update/" in h
        or "/posts/" in h
        or "/activity-" in h
        or "urn:li:activity:" in h
        or "updateentityurn=urn:li:activity:" in h
        or "activity:" in h
        or "lnkd.in/" in h
    )


def get_post_url_from_card(card) -> str:
    """
    Three-strategy post URL extraction:
    1. Walk href-bearing anchors using POST_URL_XPATHS.
    2. Look for data-urn / data-id attributes on the card or its children.
    3. Any linkedin.com anchor as a last resort.
    """
    # Strategy 1 — href anchors
    for xpath in POST_URL_XPATHS:
        try:
            for el in card.find_elements(By.XPATH, xpath):
                href = absolutize_linkedin_href(el.get_attribute("href") or "")
                if href and _looks_like_post_url(href):
                    return canonicalize_url(href)
        except Exception:
            continue

    # Strategy 2 — data-urn on the card root
    for attr in ("data-urn", "data-id", "data-activity-urn", "data-entity-urn"):
        try:
            urn = (card.get_attribute(attr) or "").strip()
            if urn and "activity:" in urn:
                activity_id = urn.split("activity:")[-1].rstrip(")")
                return canonicalize_url(
                    f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"
                )
        except Exception:
            continue

    # Strategy 3 — data-urn on child elements
    try:
        for child in card.find_elements(By.XPATH, ".//*[@data-urn or @data-activity-urn or @data-id or @data-entity-urn]"):
            urn = (
                child.get_attribute("data-urn")
                or child.get_attribute("data-activity-urn")
                or child.get_attribute("data-id")
                or child.get_attribute("data-entity-urn")
                or ""
            ).strip()
            if urn and "activity:" in urn:
                activity_id = urn.split("activity:")[-1].rstrip(")")
                return canonicalize_url(f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}")
    except Exception:
        pass

    # Strategy 4 — SDUI tracking payloads (no href / no data-urn)
    try:
        scope = (card.get_attribute("data-view-tracking-scope") or "").strip()
        if scope:
            url = parse_activity_url_from_tracking_scope(scope)
            if url:
                return canonicalize_url(url)
    except Exception:
        pass
    try:
        for child in card.find_elements(By.XPATH, ".//*[@data-view-tracking-scope]"):
            scope = (child.get_attribute("data-view-tracking-scope") or "").strip()
            if not scope:
                continue
            url = parse_activity_url_from_tracking_scope(scope)
            if url:
                return canonicalize_url(url)
    except Exception:
        pass

    # Strategy 5 â€” scan card HTML for an activity URN (works when IDs are only in serialized payloads).
    try:
        html = (card.get_attribute("outerHTML") or "")[:25000]
        url = activity_url_from_blob(html)
        if url:
            return canonicalize_url(url)
    except Exception:
        pass

    return ""


def get_post_links_global() -> list[str]:
    links: list[str] = []
    try:
        anchors = driver.find_elements(By.XPATH, GLOBAL_POST_LINK_XPATH)
        for a in anchors:
            href = canonicalize_url(absolutize_linkedin_href(a.get_attribute("href") or ""))
            if not href:
                continue
            links.append(href)
    except Exception:
        return []
    # preserve order + unique
    return list(dict.fromkeys(links))


def parse_activity_url_from_tracking_scope(scope: str) -> str:
    """
    Extract activity ID from LinkedIn SDUI tracking payloads.
    Supports direct URN strings and byte-array encoded JSON payloads.
    """
    if not scope:
        return ""

    # Direct/plain occurrences.
    for pattern in (
        r"urn:li:activity:(\d{8,})",
        r"activity[:%3A]+(\d{8,})",
    ):
        m = re.search(pattern, scope, flags=re.IGNORECASE)
        if m:
            return f"https://www.linkedin.com/feed/update/urn:li:activity:{m.group(1)}"

    # Decode byte arrays in payload (e.g. "data":[123,34,...]).
    try:
        arrays = re.findall(r'"data"\s*:\s*\[([0-9,\s]+)\]', scope)
        for arr in arrays:
            nums = [int(n.strip()) for n in arr.split(",") if n.strip().isdigit()]
            if not nums:
                continue
            decoded = "".join(chr(n) for n in nums if 0 <= n <= 255)
            m = re.search(r"urn:li:activity:(\d{8,})", decoded, flags=re.IGNORECASE)
            if m:
                return f"https://www.linkedin.com/feed/update/urn:li:activity:{m.group(1)}"
            m = re.search(r'"activityUrn"\s*:\s*"urn:li:activity:(\d{8,})"', decoded, flags=re.IGNORECASE)
            if m:
                return f"https://www.linkedin.com/feed/update/urn:li:activity:{m.group(1)}"
    except Exception:
        pass
    return ""


def get_tracking_cards() -> list:
    for xp in TRACKING_CARD_XPATHS:
        try:
            cards = driver.find_elements(By.XPATH, xp)
            if cards:
                print_lg(f"Tracking cards via '{xp}': {len(cards)}")
                return cards
        except Exception:
            continue
    return []


def read_tracking_card(card) -> dict:
    """
    SDUI fallback reader: derive URL from tracking scope or descendant links.
    """
    post_url = get_post_url_from_card(card)
    if not post_url:
        try:
            scope = card.get_attribute("data-view-tracking-scope") or ""
            post_url = canonicalize_url(parse_activity_url_from_tracking_scope(scope))
        except Exception:
            post_url = ""

    profile_url, full_name, job_title = get_author_from_card(card)
    snippet = get_snippet_from_card(card)
    return {
        "post_url": post_url,
        "profile_url": profile_url,
        "full_name": full_name,
        "job_title": job_title,
        "snippet": snippet,
        "post_date": "",
    }


def get_author_from_card(card) -> tuple[str, str, str]:
    """Returns (profile_url, full_name, job_title)."""
    profile_url = full_name = job_title = ""
    for xpath in AUTHOR_XPATHS:
        try:
            els = card.find_elements(By.XPATH, xpath)
            if not els:
                continue
            href = (els[0].get_attribute("href") or "").strip()
            if href:
                profile_url = canonicalize_url(href)
                full_name   = normalize_space(
                    els[0].text or els[0].get_attribute("aria-label") or ""
                )
            if len(els) > 1:
                job_title = normalize_space(els[1].text or "")
            break
        except Exception:
            continue
    return profile_url, full_name, job_title


def get_snippet_from_card(card) -> str:
    for xpath in SNIPPET_XPATHS:
        try:
            els = card.find_elements(By.XPATH, xpath)
            if els:
                text = normalize_space(els[0].text)
                if text:
                    return text
        except Exception:
            continue
    try:
        return normalize_space(card.text)
    except Exception:
        return ""


def read_card(card) -> dict:
    profile_url, full_name, job_title = get_author_from_card(card)
    return {
        "post_url"   : get_post_url_from_card(card),
        "profile_url": profile_url,
        "full_name"  : full_name,
        "job_title"  : job_title,
        "snippet"    : get_snippet_from_card(card),
        "post_date"  : get_post_date_from_card(card),
    }


def extract_detail_text() -> str:
    for xpath in DETAIL_TEXT_XPATHS:
        try:
            els = driver.find_elements(By.XPATH, xpath)
            if els:
                text = normalize_space(els[0].text)
                if text:
                    return text
        except Exception:
            continue
    return ""


def enrich_snippet(post_url: str, list_snippet: str) -> str:
    if icp_posts_detail_open_mode == "off" or not post_url:
        return list_snippet

    orig = driver.current_window_handle

    if icp_posts_detail_open_mode == "new_tab":
        try:
            driver.execute_script("window.open(arguments[0], '_blank');", post_url)
            _sleep()
            driver.switch_to.window(driver.window_handles[-1])
            _wait_body()
            text = extract_detail_text()
            driver.close()
            driver.switch_to.window(orig)
            return text or list_snippet
        except Exception as e:
            print_lg(f"Detail (new_tab) error: {e}")
            try:
                if len(driver.window_handles) > 1:
                    driver.close()
                driver.switch_to.window(orig)
            except Exception:
                pass
            return list_snippet

    if icp_posts_detail_open_mode == "same_tab":
        try:
            driver.get(post_url)
            _wait_body()
            text = extract_detail_text()
            driver.back()
            _wait_body()
            return text or list_snippet
        except Exception as e:
            print_lg(f"Detail (same_tab) error: {e}")
            try:
                driver.back()
            except Exception:
                pass
            return list_snippet

    return list_snippet


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def goto_next_page() -> bool:
    for xpath in NEXT_PAGE_XPATHS:
        try:
            btn = driver.find_element(By.XPATH, xpath)
            scroll_to_view(driver, btn)
            btn.click()
            _wait_body()
            return True
        except Exception:
            continue
    return False


def scroll_load() -> None:
    """Scroll down to trigger lazy-loading of post cards."""
    for _ in range(icp_posts_scroll_rounds):
        try:
            # Many LinkedIn search pages virtualize results inside a scrollable column.
            containers = driver.find_elements(
                By.XPATH,
                "//main//*[@data-testid='lazy-column' or @data-component-type='LazyColumn' or contains(@class,'scaffold-finite-scroll')]",
            )
            if containers:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 900;", containers[0])
            else:
                driver.execute_script("window.scrollBy(0, 800);")
        except Exception:
            driver.execute_script("window.scrollBy(0, 800);")
        _sleep()


# ---------------------------------------------------------------------------
# Per-term scraping loop
# ---------------------------------------------------------------------------

def scrape_term(term: str) -> dict:
    stats = {"scanned": 0, "saved": 0, "skipped": 0, "failed": 0, "pages": 0}

    if not navigate_to_content_search(term):
        print_lg(f'SKIP "{term}": navigation failed.')
        stats["failed"] += 1
        return stats

    page_num = 0

    while page_num < icp_posts_max_pages:

        if not ensure_content_context(term):
            print_lg(f'ABORT "{term}": lost content context.')
            stats["failed"] += 1
            break

        scroll_load()
        cards = find_cards()
        page_num      += 1
        stats["pages"] += 1

        if not cards:
            # Fallback 1: direct post links from current results viewport.
            global_links = get_post_links_global()
            if global_links:
                print_lg(f"  Page {page_num}: using global-link fallback ({len(global_links)} links).")
                for link in global_links:
                    stats["scanned"] += 1
                    canon = canonicalize_url(link)
                    if not canon:
                        stats["skipped"] += 1
                        continue
                    if f"url::{canon}" in seen_post_keys:
                        stats["skipped"] += 1
                        continue
                    save_lead_row(
                        profile_url="",
                        full_name="",
                        job_title="",
                        keywords=term,
                        trigger="",
                        post_url=link,
                        post_date="",
                    )
                    seen_post_urls.add(canon)
                    seen_post_keys.add(f"url::{canon}")
                    stats["saved"] += 1
                if not goto_next_page():
                    break
                continue

            # Fallback 2: SDUI tracking cards.
            tracking_cards = get_tracking_cards()
            if tracking_cards:
                print_lg(f"  Page {page_num}: using tracking-card fallback ({len(tracking_cards)} cards).")
                for idx in range(len(tracking_cards)):
                    try:
                        fresh_tracking = get_tracking_cards()
                        if idx >= len(fresh_tracking):
                            break
                        tcard = fresh_tracking[idx]
                        stats["scanned"] += 1
                        raw = read_tracking_card(tcard)
                        post_url = canonicalize_url(raw["post_url"])
                        if not post_url:
                            stats["skipped"] += 1
                            continue
                        if f"url::{post_url}" in seen_post_keys:
                            stats["skipped"] += 1
                            continue
                        snippet = enrich_snippet(post_url, raw["snippet"])
                        save_lead_row(
                            profile_url=raw["profile_url"],
                            full_name=raw["full_name"],
                            job_title=raw["job_title"],
                            keywords=term,
                            trigger=snippet,
                            post_url=post_url,
                            post_date=raw.get("post_date", "") or "",
                        )
                        seen_post_urls.add(post_url)
                        seen_post_keys.add(f"url::{post_url}")
                        stats["saved"] += 1
                    except Exception as e:
                        stats["failed"] += 1
                        print_lg(f"    Tracking card {idx} error: {e}")
                        continue
                if not goto_next_page():
                    break
                continue

            print_lg(f'  Page {page_num}: no cards and no fallback links.')
            if not goto_next_page():
                break
            continue

        print_lg(f'  Page {page_num}: {len(cards)} card(s) found.')

        for idx in range(len(cards)):
            try:
                fresh = find_cards()
                if idx >= len(fresh):
                    break
                card = fresh[idx]
                stats["scanned"] += 1

                raw      = read_card(card)
                post_url = raw["post_url"]

                snippet = enrich_snippet(post_url, raw["snippet"])

                if not post_url:
                    # Try opening the card to capture the post URL (some SDUI cards hide it).
                    try:
                        post_url = maybe_capture_post_url_by_opening(card)
                    except Exception:
                        post_url = ""

                if not post_url:
                    # Try the "..." -> "Copy link to post" menu and read the clipboard.
                    try:
                        post_url = maybe_capture_post_url_by_copy_link_menu(card)
                    except Exception:
                        post_url = ""
                    if not post_url:
                        print_lg(f"      DEBUG: copy-link menu did not yield a URL for card {idx}.")
                    else:
                        print_lg(f"      DEBUG: copy-link yielded post_url='{post_url[:120]}'")

                # Dedupe: use post URL when available, otherwise profile + snippet.
                key = dedupe_key(raw["profile_url"], post_url, snippet)
                if key in seen_post_keys:
                    stats["skipped"] += 1
                    continue

                if not post_url:
                    print_lg(
                        f"    Card {idx}: no URL, saving without it. Text preview: "
                        f"{normalize_space(card.text)[:120]}"
                    )
                    try:
                        hrefs: list[str] = []
                        for a in card.find_elements(By.XPATH, ".//a[@href]"):
                            h = absolutize_linkedin_href(a.get_attribute("href") or "")
                            if h:
                                hrefs.append(h[:140])
                            if len(hrefs) >= 6:
                                break
                        html = (card.get_attribute("outerHTML") or "")[:25000]
                        from_html = activity_url_from_blob(html)
                        if hrefs or from_html:
                            print_lg(f"      DEBUG no-URL hrefs={hrefs} html_activity={from_html}")
                    except Exception:
                        pass

                save_lead_row(
                    profile_url = raw["profile_url"],
                    full_name   = raw["full_name"],
                    job_title   = raw["job_title"],
                    keywords    = term,
                    trigger     = snippet,
                    post_url    = post_url or "",
                    post_date   = raw.get("post_date", "") or "",
                )

                seen_post_keys.add(key)
                if post_url:
                    seen_post_urls.add(canonicalize_url(post_url))
                stats["saved"] += 1
                print_lg(f"    Saved: {raw['full_name'] or '(no name)'} | {(post_url or '(no post url)')[:80]}")

            except (StaleElementReferenceException, ElementClickInterceptedException,
                    NoSuchElementException) as e:
                stats["failed"] += 1
                print_lg(f"    Card {idx} recoverable error: {e}")
            except Exception as e:
                stats["failed"] += 1
                print_lg(f"    Card {idx} unexpected error: {e}")

        if not goto_next_page():
            print_lg(f'  Pagination exhausted at page {page_num} for "{term}".')
            break

    print_lg(
        f'[TERM DONE] "{term}" | pages={stats["pages"]} scanned={stats["scanned"]} '
        f'saved={stats["saved"]} skipped={stats["skipped"]} failed={stats["failed"]}'
    )
    return stats


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    totals = {"scanned": 0, "saved": 0, "skipped": 0, "failed": 0, "pages": 0}
    try:
        validate_posts_config()
        initialize_output_file()
        load_existing_post_urls()

        terms = effective_search_terms()
        print_lg(f"Terms ({len(terms)}): {terms}")
        print_lg(f"Max pages ceiling: {icp_posts_max_pages}")
        print_lg(f"Detail mode: {icp_posts_detail_open_mode}")

        driver.get("https://www.linkedin.com/feed/")
        _wait_body()
        if not is_logged_in():
            login_linkedin()

        for term in terms:
            t = scrape_term(term)
            for k in totals:
                totals[k] += t[k]

        print_lg(
            f"[FINAL] pages={totals['pages']} scanned={totals['scanned']} "
            f"saved={totals['saved']} skipped={totals['skipped']} failed={totals['failed']}"
        )
        print_lg(f"CSV: {output_file}")

    except Exception as e:
        print_lg("Fatal error.", e)
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
