"""
MongoDB repository for LinkedIn leads scraped from the Scraper project.
Stores leads in a dedicated 'linkedin_leads' collection with rich metadata.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.mongodb.connection import get_database
from utils.logger import logger


class MongoLinkedInLeadRepository:
    """MongoDB repository for linkedin_leads collection."""

    def __init__(self, database: Optional[AsyncIOMotorDatabase] = None):
        self.database = database if database is not None else get_database()
        self.collection = self.database.linkedin_leads

    def _doc_to_dict(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to API-friendly dict."""
        doc["id"] = str(doc.pop("_id"))
        doc["user_id"] = str(doc.get("user_id", ""))
        return doc

    async def bulk_create_leads(
        self,
        user_id: str,
        leads: List[Dict[str, Any]],
        source_file: str,
    ) -> Dict[str, Any]:
        """
        Bulk insert leads, deduplicating by linkedin_url + job_link.
        Returns counts of imported and skipped.
        """
        if not leads:
            return {"imported": 0, "skipped": 0, "total": 0}

        # Build set of existing keys for dedup
        existing_keys = set()
        cursor = self.collection.find(
            {"user_id": ObjectId(user_id)},
            {"linkedin_url": 1, "job_link": 1},
        )
        async for doc in cursor:
            key = (doc.get("linkedin_url", ""), doc.get("job_link", ""))
            existing_keys.add(key)

        documents = []
        skipped = 0
        now = datetime.utcnow()

        for lead in leads:
            linkedin_url = (lead.get("Linkedin Url") or lead.get("linkedin_url") or "").strip()
            job_link = (lead.get("Job Link") or lead.get("job_link") or "").strip()
            dedup_key = (linkedin_url, job_link)

            if dedup_key in existing_keys and (linkedin_url or job_link):
                skipped += 1
                continue

            existing_keys.add(dedup_key)
            documents.append({
                "user_id": ObjectId(user_id),
                "linkedin_url": linkedin_url,
                "full_name": (lead.get("Full Name") or lead.get("full_name") or "").strip(),
                "email": (lead.get("Email") or lead.get("email") or "").strip(),
                "email_status": (lead.get("Email Status") or lead.get("email_status") or "").strip(),
                "job_title": (lead.get("Job Title") or lead.get("job_title") or "").strip(),
                "company_name": (lead.get("Company Name") or lead.get("company_name") or "").strip(),
                "company_website": (lead.get("Company Website") or lead.get("company_website") or "").strip(),
                "city": (lead.get("City") or lead.get("city") or "").strip(),
                "state": (lead.get("State") or lead.get("state") or "").strip(),
                "country": (lead.get("Country") or lead.get("country") or "").strip(),
                "industry": (lead.get("Industry") or lead.get("industry") or "").strip(),
                "keywords": (lead.get("Keywords") or lead.get("keywords") or "").strip(),
                "employees": (lead.get("Employees") or lead.get("employees") or "").strip(),
                "company_linkedin_url": (lead.get("Company Linkedin Url") or lead.get("company_linkedin_url") or "").strip(),
                "company_twitter_url": (lead.get("Company Twitter Url") or lead.get("company_twitter_url") or "").strip(),
                "company_facebook_url": (lead.get("Company Facebook Url") or lead.get("company_facebook_url") or "").strip(),
                "company_phone_numbers": (lead.get("Company Phone Numbers") or lead.get("company_phone_numbers") or "").strip(),
                "buying_intent": (lead.get("Buying Intent") or lead.get("buying_intent") or "").strip(),
                "trigger": (lead.get("Trigger") or lead.get("trigger") or "").strip(),
                "job_link": job_link,
                "source_file": source_file,
                "imported_to_contacts": False,
                "created_at": now,
            })

        imported = 0
        if documents:
            result = await self.collection.insert_many(documents)
            imported = len(result.inserted_ids)
            logger.info(f"Imported {imported} LinkedIn leads for user {user_id}")

        return {"imported": imported, "skipped": skipped, "total": len(leads)}

    async def get_leads(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        source_file: Optional[str] = None,
        imported_only: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Get LinkedIn leads with optional filters and pagination."""
        query: Dict[str, Any] = {"user_id": ObjectId(user_id)}
        if source_file:
            query["source_file"] = source_file
        if imported_only is True:
            query["imported_to_contacts"] = True
        elif imported_only is False:
            query["imported_to_contacts"] = False

        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_dict(doc) for doc in docs]

    async def count_leads(self, user_id: str, source_file: Optional[str] = None) -> int:
        """Count leads for a user."""
        query: Dict[str, Any] = {"user_id": ObjectId(user_id)}
        if source_file:
            query["source_file"] = source_file
        return await self.collection.count_documents(query)

    async def mark_as_imported(self, user_id: str, lead_ids: List[str]) -> int:
        """Mark leads as imported to contacts."""
        object_ids = [ObjectId(lid) for lid in lead_ids]
        result = await self.collection.update_many(
            {"_id": {"$in": object_ids}, "user_id": ObjectId(user_id)},
            {"$set": {"imported_to_contacts": True}},
        )
        return result.modified_count

    async def delete_by_source(self, user_id: str, source_file: str) -> int:
        """Delete all leads from a specific source file."""
        result = await self.collection.delete_many({
            "user_id": ObjectId(user_id),
            "source_file": source_file,
        })
        return result.deleted_count

    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get lead statistics for a user."""
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "imported": {"$sum": {"$cond": ["$imported_to_contacts", 1, 0]}},
                    "not_imported": {"$sum": {"$cond": ["$imported_to_contacts", 0, 1]}},
                    "sources": {"$addToSet": "$source_file"},
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        if results:
            r = results[0]
            return {
                "total": r["total"],
                "imported": r["imported"],
                "not_imported": r["not_imported"],
                "source_count": len(r["sources"]),
            }
        return {"total": 0, "imported": 0, "not_imported": 0, "source_count": 0}
