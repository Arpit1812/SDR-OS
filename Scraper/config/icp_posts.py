"""
ICP posts/content extraction settings.
Dedicated config for the posts bot — does NOT affect config/icp.py (jobs bot).

Search term priority (first non-empty list wins):
  1. icp_posts_search_terms  (this file)
  2. config.icp.icp_search_terms
  3. config.search.search_terms
"""

# ---------------------------------------------------------------------------
# Search terms
# Add your keywords here. Each term opens a separate content search.
# Examples: "looking for a CRM", "we just raised", "hiring SDRs", "pain with outbound"
# ---------------------------------------------------------------------------
icp_posts_search_terms = [
    "Looking for a CTO",
    "looking for the CTO",
    "looking for a Technical Co-Founder",
    "looking for a Tech co-founder",
    "looking for a technical co-founder",
    "Looking for a technical co-founder",
    "just raised",
    "we just raised",
    # "another keyword",
]

# ---------------------------------------------------------------------------
# Runtime controls
# ---------------------------------------------------------------------------

# Safety ceiling on pages per search term.
# The bot stops EARLIER if LinkedIn's pagination is exhausted.
# Set to a large number (e.g. 9999) to scrape every available page.
icp_posts_max_pages = 9999

# Number of downward scroll steps per page to trigger lazy-loaded cards.
# Increase if cards fail to load (3–5 is usually enough).
icp_posts_scroll_rounds = 4

# How many times to retry a failing Selenium action before giving up.
icp_posts_retry_limit = 3

# Milliseconds to wait between scroll steps and page transitions.
# Lower = faster but more likely to miss lazy-loaded content.
# Recommended: 1200–2000 on a normal connection.
icp_posts_sleep_ms = 1500

# ---------------------------------------------------------------------------
# Detail extraction mode
# Controls whether the bot opens each post to grab its full text.
#
#   "off"       — fastest; uses only the text visible in the search result card.
#                 Good enough for most ICP signals.
#   "same_tab"  — opens each post URL in the current tab, extracts the full
#                 post body, then navigates back. Slower; more complete text.
#   "new_tab"   — opens each post in a NEW browser tab, extracts text, closes
#                 tab. Slightly safer than same_tab (search page stays intact).
# ---------------------------------------------------------------------------
icp_posts_detail_open_mode = "off"  # "off" | "same_tab" | "new_tab"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

# Path for the output CSV (relative to project root).
# A run-scoped timestamp is appended automatically, e.g.:
#   all excels/icp_posts_leads__20240315_143022.csv
icp_posts_leads_file_name = "all excels/icp_posts_leads.csv"

# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

# Maximum characters stored in the "Trigger" column (the post text / snippet).
# LinkedIn posts can be very long; 2000 chars is a good balance for CRM imports.
icp_posts_snippet_max_length = 2000