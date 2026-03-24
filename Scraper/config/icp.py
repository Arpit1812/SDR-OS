'''
ICP lead extraction settings.
This file controls whether the bot applies to jobs, extracts leads, or does both.
'''

# Bot operation mode:
# - "apply_only": Existing behavior, only apply/collect application links.
# - "extractor_only": Only extract ICP leads from job postings.
# - "hybrid": Extract ICP leads and continue normal apply flow.
lead_extraction_mode = "extractor_only"        # "apply_only", "extractor_only", "hybrid"

# Matching mode:
# - "strict": Hard filters must pass.
# - "score": Weighted scoring with threshold.
icp_match_mode = "score"               # "strict", "score"

# Minimum score for score mode (0-100)
icp_score_threshold = 70               # Integer 0 to 100

# CSV file path for ICP leads output
icp_leads_file_name = "all excels/icp_leads.csv"

# Search location override for ICP extraction.
# If empty "", bot will use `search_location` from `config/search.py`.
# Examples:
# "United States"
# "California, United States"
# "New York, NY, United States"
# "Berlin, Germany"
icp_search_location = ""

# ICP-specific job filter overrides.
# If left empty ("" or [] where applicable), values fall back to `config/search.py`.
icp_sort_by = ""                       # "Most recent", "Most relevant" or ""
icp_date_posted = "Any time"          # "Any time", "Past month", "Past week", "Past 24 hours" or ""
icp_salary = ""                        # "$40,000+", "$60,000+", "$80,000+", "$100,000+", "$120,000+", "$140,000+", "$160,000+", "$180,000+", "$200,000+" or ""
icp_easy_apply_only = False            # True or False
icp_experience_level = []              # "Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"
icp_job_type = []                      # "Full-time", "Part-time", "Contract", "Temporary", "Volunteer", "Internship", "Other"
icp_on_site = [
    "Hybrid",
    "Remote",
]               # "On-site", "Remote", "Hybrid"

# Dedicated search terms for ICP extraction.
# If empty, bot will fall back to `search_terms` from `config/search.py`.
icp_search_terms = [
    "AI Engineer",
    "ML Engineer",
    "Gen AI",
    "AI/ML Engineer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
]

# Target role keywords (job title + description)
icp_role_keywords = [
    "AI Engineer",
    "ML Engineer",
    "Gen AI",
    "AI/ML Engineer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
]

# Company size buckets to match (normalized format)
icp_company_size_targets = [
    "11-30",
]

# Industry/company context keywords
icp_industry_keywords = [
    "software",
    "software development",
    "saas",
    "technology",
    "AI/ML",
    "Gen AI",
    "AI models",
    "LLM",
    "NLP",
]

# Signals that suggest non-technical founder/team
icp_non_technical_signals = [
    "non-technical founder",
    "non technical founder",
    "business founder",
    "looking for technical partner",
    "need technical leadership",
    "build our first engineering team",
]

# Signals that suggest technical leadership already exists
icp_technical_exclusion_signals = [
    "cto in place",
    "vp engineering",
    "head of engineering already",
    "senior engineering team",
    "our engineering leadership",
]

# Prevent duplicate lead writes for same LinkedIn job ID
icp_dedupe_by_job_id = True            # True or False

# Score-mode constraint toggles:
# If True, these constraints are required in score mode.
# If False, they only contribute to score/reasons.
icp_require_company_size_in_score_mode = False
icp_require_industry_in_score_mode = False

# Backward-compatibility alias for older typo-ed key usage.
icp_require_company_size_in_scro_mode = icp_require_company_size_in_score_mode

# Skip non-ICP titles early in extractor/hybrid mode before opening job details.
# This reduces noise when LinkedIn returns loosely related results.
icp_title_pre_filter = False           # True or False
