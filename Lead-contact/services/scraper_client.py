"""
Scraper Service - Integration layer between Lead-contact and the LinkedIn Scraper project.

Reads scraper output files (CSV/JSON) directly from the Scraper directory,
manages ICP configuration, and can launch scraper runs via subprocess.
"""

import os
import re
import csv
import json
import subprocess
import signal
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils.logger import logger


# Resolve the Scraper project root relative to this file
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_SCRAPER_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", "Scraper"))


class ScraperService:
    """Service for interacting with the LinkedIn Scraper project."""

    def __init__(self, scraper_dir: Optional[str] = None):
        self.scraper_dir = scraper_dir or os.environ.get("SCRAPER_DIR", _DEFAULT_SCRAPER_DIR)
        self.scraper_python = os.environ.get("SCRAPER_PYTHON", "python")
        self._process: Optional[subprocess.Popen] = None

    # ── helpers ───────────────────────────────────────────────────────

    def _abs(self, rel_path: str) -> str:
        """Resolve a path relative to the Scraper project root."""
        return os.path.normpath(os.path.join(self.scraper_dir, rel_path))

    # ── Run stats ────────────────────────────────────────────────────

    def get_run_stats(self) -> Optional[Dict[str, Any]]:
        """Read run_stats.json saved by the scraper after each run."""
        path = self._abs("run_stats.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading run_stats.json: {e}")
            return None

    # ── Read leads ───────────────────────────────────────────────────

    def get_leads_from_json(self) -> List[Dict[str, Any]]:
        """Read leads.json produced by the Scraper after each run."""
        path = self._abs("leads.json")
        if not os.path.exists(path):
            logger.warning(f"leads.json not found at {path}")
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error reading leads.json: {e}")
            return []

    def get_leads_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read leads from either a CSV or JSON file."""
        full_path = file_path if os.path.isabs(file_path) else self._abs(file_path)
        if not os.path.exists(full_path):
            logger.warning(f"File not found: {full_path}")
            return []
        try:
            if full_path.endswith(".json"):
                with open(full_path, encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            else:
                return self.get_leads_from_csv(full_path)
        except Exception as e:
            logger.error(f"Error reading file {full_path}: {e}")
            return []

    def get_leads_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """Parse an ICP leads CSV file into a list of dicts."""
        full_path = csv_path if os.path.isabs(csv_path) else self._abs(csv_path)
        if not os.path.exists(full_path):
            logger.warning(f"CSV file not found: {full_path}")
            return []
        try:
            with open(full_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Error reading CSV {full_path}: {e}")
            return []

    def list_lead_files(self) -> List[Dict[str, Any]]:
        """List all ICP lead CSV files in the Scraper's 'all excels' directory."""
        excels_dir = self._abs("all excels")
        if not os.path.isdir(excels_dir):
            return []
        files = []
        for fname in sorted(os.listdir(excels_dir), reverse=True):
            if "icp" in fname.lower() and fname.endswith(".csv"):
                fpath = os.path.join(excels_dir, fname)
                stat = os.stat(fpath)
                files.append({
                    "filename": fname,
                    "path": fpath,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        return files

    # ── ICP config ───────────────────────────────────────────────────

    def get_icp_config(self) -> Dict[str, Any]:
        """Read current ICP and search configuration from config files."""
        config: Dict[str, Any] = {}
        
        # Mapping of config files to the variables we want to extract
        files_to_parse = {
            "config/icp.py": {
                "strings": {
                    "lead_extraction_mode": r'lead_extraction_mode\s*=\s*"([^"]*)"',
                    "icp_match_mode": r'icp_match_mode\s*=\s*"([^"]*)"',
                    "icp_leads_file_name": r'icp_leads_file_name\s*=\s*"([^"]*)"',
                    "icp_search_location": r'icp_search_location\s*=\s*"([^"]*)"',
                },
                "ints": {
                    "icp_score_threshold": r'icp_score_threshold\s*=\s*(\d+)',
                },
                "bools": {
                    "icp_easy_apply_only": r'icp_easy_apply_only\s*=\s*(True|False)',
                    "icp_dedupe_by_job_id": r'icp_dedupe_by_job_id\s*=\s*(True|False)',
                    "icp_title_pre_filter": r'icp_title_pre_filter\s*=\s*(True|False)',
                },
                "lists": {
                    "icp_search_terms": r'icp_search_terms\s*=\s*\[(.*?)\]',
                    "icp_role_keywords": r'icp_role_keywords\s*=\s*\[(.*?)\]',
                    "icp_company_size_targets": r'icp_company_size_targets\s*=\s*\[(.*?)\]',
                    "icp_industry_keywords": r'icp_industry_keywords\s*=\s*\[(.*?)\]',
                    "icp_non_technical_signals": r'icp_non_technical_signals\s*=\s*\[(.*?)\]',
                    "icp_experience_level": r'icp_experience_level\s*=\s*\[(.*?)\]',
                    "icp_job_type": r'icp_job_type\s*=\s*\[(.*?)\]',
                    "icp_on_site": r'icp_on_site\s*=\s*\[(.*?)\]',
                }
            },
            "config/search.py": {
                "strings": {
                    "search_location": r'search_location\s*=\s*"([^"]*)"',
                },
                "ints": {},
                "bools": {},
                "lists": {
                    "on_site": r'on_site\s*=\s*\[(.*?)\]',
                }
            },
            "config/questions.py": {
                "strings": {
                    "default_resume_path": r'default_resume_path\s*=\s*"([^"]*)"',
                },
                "ints": {},
                "bools": {},
                "lists": {}
            }
        }

        for rel_path, patterns in files_to_parse.items():
            file_path = self._abs(rel_path)
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                for key, pattern in patterns["strings"].items():
                    match = re.search(pattern, content)
                    if match: config[key] = match.group(1)

                for key, pattern in patterns["ints"].items():
                    match = re.search(pattern, content)
                    if match: config[key] = int(match.group(1))

                for key, pattern in patterns["bools"].items():
                    match = re.search(pattern, content)
                    if match: config[key] = match.group(1) == "True"

                for key, pattern in patterns["lists"].items():
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        raw = match.group(1)
                        items = re.findall(r'"([^"]*)"', raw)
                        config[key] = items

            except Exception as e:
                logger.error(f"Error reading {rel_path}: {e}")
                config["error"] = str(e)

        return config

    def update_icp_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration settings across corresponding config files."""
        # Determine which file each key belongs to
        file_mapping = {
            "search_location": "config/search.py",
            "on_site": "config/search.py",
            "default_resume_path": "config/questions.py",
        }
        
        # Group updates by target file
        updates_by_file = {}
        for key, value in updates.items():
            target = file_mapping.get(key, "config/icp.py")
            if target not in updates_by_file:
                updates_by_file[target] = {}
            updates_by_file[target][key] = value

        success_files = []
        errors = []

        for target_file, file_updates in updates_by_file.items():
            config_path = self._abs(target_file)
            if not os.path.exists(config_path):
                errors.append(f"{target_file} not found")
                continue

            try:
                with open(config_path, encoding="utf-8") as f:
                    content = f.read()

                for key, value in file_updates.items():
                    if isinstance(value, list):
                        # Format as Python list of strings
                        items = ",\n    ".join(f'"{v}"' for v in value)
                        list_str = f"[\n    {items},\n]" if items else "[]"
                        pattern = rf'({key}\s*=\s*)\[.*?\]'
                        # Use re.sub with care, finding the exact key assignment
                        if re.search(pattern, content, flags=re.DOTALL):
                            content = re.sub(pattern, f'{key} = {list_str}', content, flags=re.DOTALL)
                        else:
                            # Fallback if list was empty on single line
                            pattern_single = rf'({key}\s*=\s*)\[\]'
                            content = re.sub(pattern_single, f'{key} = {list_str}', content)
                    elif isinstance(value, bool):
                        pattern = rf'({key}\s*=\s*)(True|False)'
                        content = re.sub(pattern, f'\\g<1>{value}', content)
                    elif isinstance(value, int):
                        pattern = rf'({key}\s*=\s*)\d+'
                        content = re.sub(pattern, f'\\g<1>{value}', content)
                    elif isinstance(value, str):
                        pattern = rf'({key}\s*=\s*)"[^"]*"'
                        content = re.sub(pattern, f'\\g<1>"{value}"', content)

                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                success_files.append(target_file)
            except Exception as e:
                logger.error(f"Error updating {target_file}: {e}")
                errors.append(str(e))

        if errors:
            return {"success": False, "error": "; ".join(errors)}
        return {"success": True, "updated_keys": list(updates.keys())}

    # ── Scraper process management ───────────────────────────────────

    def launch_scraper(self, mode: str = "jobs") -> Dict[str, Any]:
        """
        Launch the scraper as a subprocess.
        mode: 'jobs' for runAiBot.py, 'posts' for runPostContentBot.py
        """
        if self._process and self._process.poll() is None:
            return {"success": False, "error": "Scraper is already running", "pid": self._process.pid}

        script = "runAiBot.py" if mode == "jobs" else "runPostContentBot.py"
        script_path = self._abs(script)

        if not os.path.exists(script_path):
            return {"success": False, "error": f"{script} not found at {script_path}"}

        try:
            # Use DEVNULL for stdout/stderr to prevent pipe buffer from filling up
            # and blocking the scraper process (Windows pipe buffer is only 64KB)
            self._process = subprocess.Popen(
                [self.scraper_python, script_path],
                cwd=self.scraper_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            logger.info(f"Launched scraper ({mode}) with PID {self._process.pid}")
            return {
                "success": True,
                "pid": self._process.pid,
                "mode": mode,
                "script": script,
                "started_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error launching scraper: {e}")
            return {"success": False, "error": str(e)}

    def get_scraper_status(self) -> Dict[str, Any]:
        """Check if the scraper subprocess is running."""
        if self._process is None:
            return {"running": False, "message": "No scraper process has been launched"}

        poll = self._process.poll()
        if poll is None:
            return {"running": True, "pid": self._process.pid}
        else:
            return {
                "running": False,
                "pid": self._process.pid,
                "exit_code": poll,
                "message": "Scraper process has finished",
            }

    def stop_scraper(self) -> Dict[str, Any]:
        """Stop the running scraper subprocess."""
        if self._process is None or self._process.poll() is not None:
            return {"success": False, "error": "No running scraper process to stop"}

        try:
            if os.name == "nt":
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._process.terminate()
            self._process.wait(timeout=10)
            return {"success": True, "message": "Scraper stopped"}
        except subprocess.TimeoutExpired:
            self._process.kill()
            return {"success": True, "message": "Scraper force-killed after timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_recent_logs(self, lines: int = 50) -> List[str]:
        """Read the most recent scraper log file."""
        logs_dir = self._abs("logs")
        if not os.path.isdir(logs_dir):
            return []
        log_files = sorted(
            [f for f in os.listdir(logs_dir) if f.endswith(".log") or f.endswith(".txt")],
            reverse=True,
        )
        if not log_files:
            return []
        try:
            with open(os.path.join(logs_dir, log_files[0]), encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
            return [line.rstrip() for line in all_lines[-lines:]]
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []


# Global singleton
scraper_service = ScraperService()