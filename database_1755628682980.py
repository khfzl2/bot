import aiosqlite
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self.db = None
        
    async def initialize(self):
        """Initialize the database and create tables"""
        self.db = await aiosqlite.connect(self.db_path)
        db = self.db
        
        # Create guild settings table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT 'k!',
                    modlog_channel INTEGER,
                    welcome_channel INTEGER,
                    autorole INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Create moderation logs table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS moderation_logs (
                    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    action TEXT,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guild_settings (guild_id)
                )
            """)
        
        # Create AFK users table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS afk_users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
        
        # Create verification table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS verification (
                    guild_id INTEGER,
                    user_id INTEGER,
                    verified BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
        
        # Create command restrictions table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS command_restrictions (
                    guild_id INTEGER,
                    user_id INTEGER,
                    restriction_type TEXT,
                    reason TEXT,
                    expires_at TIMESTAMP,
                    moderator_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
        
        await db.commit()
        logger.info("All database tables created successfully")
        
        logger.info("Database initialized successfully")
    
    async def get_guild_prefix(self, guild_id: int) -> str:
        """Get the command prefix for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT prefix FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 'k!'
    
    async def set_guild_prefix(self, guild_id: int, prefix: str):
        """Set the command prefix for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, prefix) VALUES (?, ?)",
                (guild_id, prefix)
            )
            await db.commit()
    
    async def create_guild_entry(self, guild_id: int):
        """Create a new guild entry in the database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
                (guild_id,)
            )
            await db.commit()
        logger.info(f"Created database entry for guild {guild_id}")
    
    async def add_moderation_log(self, guild_id: int, user_id: int, moderator_id: int, action: str, reason: Optional[str] = None):
        """Add a moderation log entry"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO moderation_logs (guild_id, user_id, moderator_id, action, reason) VALUES (?, ?, ?, ?, ?)",
                (guild_id, user_id, moderator_id, action, reason or "No reason provided")
            )
            await db.commit()
            return cursor.lastrowid
    
    async def set_afk(self, user_id: int, guild_id: int, message: Optional[str] = None):
        """Set a user as AFK"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO afk_users (user_id, guild_id, message) VALUES (?, ?, ?)",
                (user_id, guild_id, message or "AFK")
            )
            await db.commit()
    
    async def remove_afk(self, user_id: int, guild_id: int):
        """Remove a user from AFK"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM afk_users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            await db.commit()
    
    async def get_afk_user(self, user_id: int, guild_id: int):
        """Get AFK status for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT message, timestamp FROM afk_users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            return await cursor.fetchone()
    
    async def add_command_restriction(self, guild_id: int, user_id: int, restriction_type: str, reason: str, moderator_id: int, expires_at=None):
        """Add command restriction for user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO command_restrictions (guild_id, user_id, restriction_type, reason, expires_at, moderator_id) VALUES (?, ?, ?, ?, ?, ?)",
                (guild_id, user_id, restriction_type, reason, expires_at, moderator_id)
            )
            await db.commit()
    
    async def remove_command_restriction(self, guild_id: int, user_id: int):
        """Remove command restriction for user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM command_restrictions WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            await db.commit()
    
    async def get_command_restriction(self, guild_id: int, user_id: int):
        """Check if user has command restrictions"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT restriction_type, reason, expires_at FROM command_restrictions WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            result = await cursor.fetchone()
            if result:
                restriction_type, reason, expires_at = result
                # Check if restriction has expired
                if expires_at:
                    import datetime
                    from datetime import datetime as dt
                    try:
                        if dt.fromisoformat(expires_at.replace('Z', '+00:00')) < dt.now():
                            # Expired, remove it
                            await self.remove_command_restriction(guild_id, user_id)
                            return None
                    except:
                        pass
                
                return {
                    "type": restriction_type,
                    "reason": reason,
                    "expires_at": expires_at
                }
            return None
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
            self.db = None
            logger.info("Database connection closed")