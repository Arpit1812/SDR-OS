"""
Scraper API routes for managing LinkedIn lead scraping, ICP configuration,
and importing scraped leads into the Lead-contact platform.
"""

from fastapi import APIRouter, Header, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from services.scraper_client import scraper_service
from db.repository_factory import get_linkedin_lead_repository, get_contact_repository
from utils.logger import logger


router = APIRouter(prefix="/scraper")


def _get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return x_user_id


# ── Leads ────────────────────────────────────────────────────────────


@router.get("/leads")
async def get_scraped_leads(
    source: Optional[str] = Query(None, description="File path to read leads from (CSV or JSON). Defaults to leads.json"),
):
    """Get scraped leads from a file. Defaults to leads.json if no source specified."""
    if source and source != "leads.json":
        leads = scraper_service.get_leads_from_file(source)
    else:
        leads = scraper_service.get_leads_from_json()
    return {"leads": leads, "count": len(leads)}


@router.get("/leads/files")
async def list_lead_files():
    """List all available ICP lead CSV files."""
    files = scraper_service.list_lead_files()
    return {"files": files, "count": len(files)}


@router.get("/leads/stored")
async def get_stored_leads(
    x_user_id: Optional[str] = Header(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    source_file: Optional[str] = Query(None),
):
    """Get LinkedIn leads stored in MongoDB."""
    user_id = _get_user_id(x_user_id)
    repo = await get_linkedin_lead_repository()
    skip = (page - 1) * page_size
    leads = await repo.get_leads(user_id, skip=skip, limit=page_size, source_file=source_file)
    total = await repo.count_leads(user_id, source_file=source_file)
    return {"leads": leads, "total": total, "page": page, "page_size": page_size}


@router.get("/leads/stats")
async def get_lead_stats(x_user_id: Optional[str] = Header(None)):
    """Get lead statistics."""
    user_id = _get_user_id(x_user_id)
    repo = await get_linkedin_lead_repository()
    stats = await repo.get_stats(user_id)
    return stats


@router.post("/leads/ingest")
async def ingest_leads(
    x_user_id: Optional[str] = Header(None),
    source: str = Query("leads.json", description="'leads.json' or path to a CSV file"),
):
    """
    Ingest scraped leads from a file into the linkedin_leads MongoDB collection.
    Reads from leads.json by default, or a specific CSV file.
    """
    user_id = _get_user_id(x_user_id)

    if source == "leads.json":
        leads = scraper_service.get_leads_from_json()
        source_name = "leads.json"
    else:
        leads = scraper_service.get_leads_from_csv(source)
        source_name = source.split("/")[-1].split("\\")[-1]

    if not leads:
        return {"imported": 0, "skipped": 0, "total": 0, "message": "No leads found in source"}

    repo = await get_linkedin_lead_repository()
    result = await repo.bulk_create_leads(user_id, leads, source_name)
    return result


@router.post("/leads/import-to-contacts")
async def import_leads_to_contacts(
    x_user_id: Optional[str] = Header(None),
    lead_ids: List[str] = Body(..., description="List of LinkedIn lead IDs to import"),
):
    """Import selected LinkedIn leads into the contacts collection."""
    user_id = _get_user_id(x_user_id)

    lead_repo = await get_linkedin_lead_repository()
    contact_repo = await get_contact_repository()

    # Fetch the selected leads
    leads = await lead_repo.get_leads(user_id, skip=0, limit=len(lead_ids))
    selected = [l for l in leads if l["id"] in lead_ids]

    if not selected:
        raise HTTPException(status_code=404, detail="No matching leads found")

    imported = 0
    skipped = 0
    imported_ids = []

    for lead in selected:
        try:
            await contact_repo.create_contact(
                user_id=user_id,
                email=lead.get("email") or "",
                name=lead.get("full_name") or "",
                company=lead.get("company_name") or "",
                phone=lead.get("company_phone_numbers") or "",
                custom_fields={
                    "linkedin_url": lead.get("linkedin_url", ""),
                    "job_title": lead.get("job_title", ""),
                    "company_website": lead.get("company_website", ""),
                    "city": lead.get("city", ""),
                    "state": lead.get("state", ""),
                    "country": lead.get("country", ""),
                    "industry": lead.get("industry", ""),
                    "keywords": lead.get("keywords", ""),
                    "employees": lead.get("employees", ""),
                    "buying_intent": lead.get("buying_intent", ""),
                    "trigger": lead.get("trigger", ""),
                    "job_link": lead.get("job_link", ""),
                    "company_linkedin_url": lead.get("company_linkedin_url", ""),
                },
                source=f"linkedin-scraper:{lead.get('source_file', 'unknown')}",
            )
            imported += 1
            imported_ids.append(lead["id"])
        except Exception as e:
            logger.error(f"Error importing lead {lead.get('id')}: {e}")
            skipped += 1

    # Mark as imported in linkedin_leads collection
    if imported_ids:
        await lead_repo.mark_as_imported(user_id, imported_ids)

    return {
        "imported": imported,
        "skipped": skipped,
        "total": len(selected),
        "message": f"Successfully imported {imported} leads to contacts",
    }


# ── ICP Configuration ───────────────────────────────────────────────


@router.get("/config")
async def get_icp_config():
    """Get current ICP configuration."""
    config = scraper_service.get_icp_config()
    return config


@router.put("/config")
async def update_icp_config(updates: Dict[str, Any] = Body(...)):
    """Update ICP configuration settings across all files."""
    result = scraper_service.update_icp_config(updates)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


from fastapi import UploadFile, File
import os

@router.post("/config/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file specifically for the LinkedIn scraper."""
    # The scraper expects the file to be inside 'all resumes/' directory
    resumes_dir = scraper_service._abs("all resumes")
    os.makedirs(resumes_dir, exist_ok=True)
    
    # Prefix to avoid conflicts and keep clean
    filename = f"upload_{file.filename}"
    file_path = os.path.join(resumes_dir, filename)
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        # Update the configuration to map to this file (relative path expected by scraper)
        rel_path = f"all resumes/{filename}"
        update_result = scraper_service.update_icp_config({"default_resume_path": rel_path})
        
        if not update_result.get("success"):
            return {"success": False, "error": update_result.get("error")}
            
        return {"success": True, "message": "Resume uploaded and config updated", "path": rel_path}
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload resume")


# ── Scraper Process Management ───────────────────────────────────────


@router.post("/run")
async def launch_scraper(
    mode: str = Query("jobs", description="'jobs' or 'posts'"),
):
    """Launch a scraper run."""
    if mode not in ("jobs", "posts"):
        raise HTTPException(status_code=400, detail="mode must be 'jobs' or 'posts'")
    result = scraper_service.launch_scraper(mode)
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("error", "Failed to launch"))
    return result


@router.get("/status")
async def get_scraper_status():
    """Get scraper process status."""
    return scraper_service.get_scraper_status()


@router.post("/stop")
async def stop_scraper():
    """Stop the running scraper."""
    result = scraper_service.stop_scraper()
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("error", "Failed to stop"))
    return result


@router.get("/run-stats")
async def get_run_stats():
    """Get the statistics from the most recent scraper run."""
    stats = scraper_service.get_run_stats()
    return {"stats": stats}


@router.get("/logs")
async def get_scraper_logs(lines: int = Query(50, ge=1, le=500)):
    """Get recent scraper log lines."""
    log_lines = scraper_service.get_recent_logs(lines)
    return {"lines": log_lines, "count": len(log_lines)}
