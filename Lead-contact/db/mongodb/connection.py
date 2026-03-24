from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import certifi
from config import settings
from utils.logger import logger


class MongoDBConnection:
    """MongoDB connection manager using Motor"""

    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database: AsyncIOMotorDatabase = None

    async def connect(self):
        """Connect to MongoDB, trying multiple TLS strategies."""
        strategies = [
            {"tls": True, "tlsCAFile": certifi.where()},
            {"tls": True},
            {"tls": True, "tlsAllowInvalidCertificates": True},
        ]
        last_error = None
        for i, tls_opts in enumerate(strategies, 1):
            try:
                self.client = AsyncIOMotorClient(settings.mongo_uri, **tls_opts)
                self.database = self.client[settings.mongo_db_name]
                await self.client.admin.command('ping')
                logger.info(f"Connected to MongoDB database: {settings.mongo_db_name} (strategy {i})")
                return
            except Exception as e:
                last_error = e
                logger.warning(f"MongoDB connection strategy {i} failed: {e}")
                self.client = None
                self.database = None

        logger.error(f"All MongoDB connection strategies failed. Last error: {last_error}")
        logger.error("Please check: 1) Your IP is whitelisted in MongoDB Atlas Network Access  "
                      "2) Your MONGO_URI in .env is correct  3) The cluster is active")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client is not None:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def get_database(self) -> AsyncIOMotorDatabase:
        """Get the database instance"""
        if self.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database


# Global connection instance
mongodb_connection = MongoDBConnection()


async def get_database() -> AsyncIOMotorDatabase:
    """Convenience function to get database instance"""
    return mongodb_connection.get_database()
