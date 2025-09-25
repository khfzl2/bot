import aiosqlite
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

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
                    appeal_ban_link TEXT,
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
                    is_global BOOLEAN DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # Add is_global column if it doesn't exist (for existing databases)
        try:
            await db.execute("ALTER TABLE command_restrictions ADD COLUMN is_global BOOLEAN DEFAULT 0")
            await db.commit()
        except:
            pass  # Column already exists
            
        # Add appeal_ban_link column if it doesn't exist (for existing databases)
        try:
            await db.execute("ALTER TABLE guild_settings ADD COLUMN appeal_ban_link TEXT")
            await db.commit()
        except:
            pass  # Column already exists

        # Create appeal cooldowns table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS appeal_cooldowns (
                    guild_id INTEGER,
                    user_id INTEGER,
                    last_appeal_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # Create server promotions table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS server_promotions (
                    guild_id INTEGER PRIMARY KEY,
                    promotion_text TEXT,
                    set_by_user_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Create admin settings table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS admin_settings (
                    guild_id INTEGER,
                    setting_name TEXT,
                    setting_value BOOLEAN DEFAULT 0,
                    updated_by INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, setting_name)
                )
            """)

        # Create global settings table for bot-wide settings
        await db.execute("""
                CREATE TABLE IF NOT EXISTS global_settings (
                    setting_name TEXT PRIMARY KEY,
                    setting_value TEXT,
                    updated_by TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Create admin users table for bot admins
        await db.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    granted_by INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Create bot owners table for super admins who can manage bot admins
        await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_owners (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    granted_by INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Create server command bans table
        await db.execute("""
                CREATE TABLE IF NOT EXISTS server_command_bans (
                    server_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    banned_by INTEGER,
                    ban_limit INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            # Insert guild if it doesn't exist, then update the specific column
            await db.execute(
                "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
                (guild_id,)
            )
            await db.execute(
                "UPDATE guild_settings SET prefix = ? WHERE guild_id = ?",
                (prefix, guild_id)
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

    async def add_command_restriction(self, guild_id: int, user_id: int, restriction_type: str, reason: str, moderator_id: int, expires_at=None, is_global=False):
        """Add command restriction for user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO command_restrictions (guild_id, user_id, restriction_type, reason, expires_at, moderator_id, is_global) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (guild_id, user_id, restriction_type, reason, expires_at, moderator_id, is_global)
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

    async def remove_global_command_restriction(self, user_id: int):
        """Remove global command restriction for user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM command_restrictions WHERE user_id = ? AND is_global = 1",
                (user_id,)
            )
            await db.commit()

    async def get_command_restriction(self, guild_id: int, user_id: int):
        """Check if user has command restrictions (including global bans)"""
        async with aiosqlite.connect(self.db_path) as db:
            # First check for global bans
            cursor = await db.execute(
                "SELECT restriction_type, reason, expires_at, is_global FROM command_restrictions WHERE user_id = ? AND is_global = 1",
                (user_id,)
            )
            result = await cursor.fetchone()

            # If no global ban, check for guild-specific restrictions
            if not result:
                cursor = await db.execute(
                    "SELECT restriction_type, reason, expires_at, is_global FROM command_restrictions WHERE guild_id = ? AND user_id = ? AND is_global = 0",
                    (guild_id, user_id)
                )
                result = await cursor.fetchone()

            if result:
                restriction_type, reason, expires_at, is_global = result
                # Check if restriction has expired
                if expires_at:
                    try:
                        if datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.now():
                            # Expired, remove it
                            if is_global:
                                await self.remove_global_command_restriction(user_id)
                            else:
                                await self.remove_command_restriction(guild_id, user_id)
                            return None
                    except:
                        pass

                return {
                    "type": restriction_type,
                    "reason": reason,
                    "expires_at": expires_at,
                    "is_global": bool(is_global)
                }
            return None

    async def get_global_command_restriction(self, user_id: int):
        """Check if user has global command restrictions"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT restriction_type, reason, expires_at FROM command_restrictions WHERE user_id = ? AND is_global = 1",
                (user_id,)
            )
            result = await cursor.fetchone()

            if result:
                restriction_type, reason, expires_at = result
                # Check if restriction has expired
                if expires_at:
                    try:
                        if datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.now():
                            # Expired, remove it
                            await self.remove_global_command_restriction(user_id)
                            return None
                    except:
                        pass

                return {
                    "type": restriction_type,
                    "reason": reason,
                    "expires_at": expires_at,
                    "is_global": True
                }
            return None

    async def get_command_moderation_logs(self, guild_id: int, user_id: int = None, limit: int = 10):
        """Get command moderation logs for a guild or specific user"""
        async with aiosqlite.connect(self.db_path) as db:
            if user_id:
                cursor = await db.execute(
                    "SELECT case_id, user_id, moderator_id, action, reason, timestamp FROM moderation_logs WHERE guild_id = ? AND user_id = ? AND action LIKE 'command_%' ORDER BY timestamp DESC LIMIT ?",
                    (guild_id, user_id, limit)
                )
            else:
                cursor = await db.execute(
                    "SELECT case_id, user_id, moderator_id, action, reason, timestamp FROM moderation_logs WHERE guild_id = ? AND action LIKE 'command_%' ORDER BY timestamp DESC LIMIT ?",
                    (guild_id, limit)
                )
            return await cursor.fetchall()

    async def set_appeal_cooldown(self, guild_id: int, user_id: int):
        """Set appeal cooldown for user (15 minutes)"""
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        await self.execute(
            "INSERT OR REPLACE INTO appeal_cooldowns (guild_id, user_id, expires_at) VALUES (?, ?, ?)",
            (guild_id, user_id, expires_at)
        )

    async def check_appeal_cooldown(self, guild_id: int, user_id: int):
        """Check if user can appeal (15 minute cooldown)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT last_appeal_time FROM appeal_cooldowns WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            result = await cursor.fetchone()
            if result:
                try:
                    last_appeal = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                    now = datetime.now()
                    time_diff = (now - last_appeal).total_seconds()
                    if time_diff < 900:  # 15 minutes = 900 seconds
                        remaining = 900 - time_diff
                        return False, remaining
                except:
                    pass
            return True, 0

    async def set_server_promotion(self, guild_id: int, promotion_text: str, user_id: int):
        """Set server promotion text"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO server_promotions (guild_id, promotion_text, set_by_user_id) VALUES (?, ?, ?)",
                (guild_id, promotion_text, user_id)
            )
            await db.commit()

    async def get_server_promotion(self, guild_id: int):
        """Get server promotion text"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT promotion_text, set_by_user_id, timestamp FROM server_promotions WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            if result:
                return {
                    "text": result[0],
                    "set_by": result[1],
                    "timestamp": result[2]
                }
            return None

    async def set_admin_setting(self, guild_id: int, setting_name: str, setting_value: bool, updated_by: int):
        """Set an admin setting for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO admin_settings (guild_id, setting_name, setting_value, updated_by) VALUES (?, ?, ?, ?)",
                (guild_id, setting_name, setting_value, updated_by)
            )
            await db.commit()

    async def get_admin_setting(self, guild_id: int, setting_name: str) -> bool:
        """Get an admin setting for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT setting_value FROM admin_settings WHERE guild_id = ? AND setting_name = ?",
                (guild_id, setting_name)
            )
            result = await cursor.fetchone()
            return bool(result[0]) if result else False

    async def get_global_setting(self, setting_name: str) -> str | None:
        """Get a global bot setting"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT setting_value FROM global_settings WHERE setting_name = ?",
                (setting_name,)
            )
            result = await cursor.fetchone()
            return result[0] if result else None

    async def set_global_setting(self, setting_name: str, setting_value: str, updated_by: str):
        """Set a global bot setting"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO global_settings (setting_name, setting_value, updated_by, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (setting_name, setting_value, updated_by)
            )
            await db.commit()


    async def get_verification_role(self, guild_id: int) -> int | None:
        """Get the verification role ID for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT autorole FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result and result[0] else None

    async def set_verification_role(self, guild_id: int, role_id: int):
        """Set the verification role ID for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, autorole) VALUES (?, ?)",
                (guild_id, role_id)
            )
            await db.commit()

    async def set_modlog_channel(self, guild_id: int, channel_id: int):
        """Set the moderation log channel for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            # Insert guild if it doesn't exist, then update the specific column
            await db.execute(
                "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
                (guild_id,)
            )
            await db.execute(
                "UPDATE guild_settings SET modlog_channel = ? WHERE guild_id = ?",
                (channel_id, guild_id)
            )
            await db.commit()

    async def get_modlog_channel(self, guild_id: int) -> int | None:
        """Get the moderation log channel for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT modlog_channel FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result and result[0] else None
            
    async def set_appeal_ban_link(self, guild_id: int, link: str):
        """Set the appeal ban link for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            # Insert guild if it doesn't exist, then update the specific column
            await db.execute(
                "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
                (guild_id,)
            )
            await db.execute(
                "UPDATE guild_settings SET appeal_ban_link = ? WHERE guild_id = ?",
                (link, guild_id)
            )
            await db.commit()
            
    async def get_appeal_ban_link(self, guild_id: int) -> str | None:
        """Get the appeal ban link for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT appeal_ban_link FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result and result[0] else None

    async def get_verification_status(self, guild_id: int, user_id: int):
        """Get verification status for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT verified FROM verification WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            return await cursor.fetchone()

    async def set_verification_status(self, guild_id: int, user_id: int, verified: bool):
        """Set verification status for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO verification (guild_id, user_id, verified) VALUES (?, ?, ?)",
                (guild_id, user_id, verified)
            )
            await db.commit()

    async def get_all_command_bans(self, guild_id: int, page: int = 1, per_page: int = 10):
        """Get all command bans for a guild (including global bans)"""
        offset = (page - 1) * per_page
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get both server-specific and global command bans
            cursor = await db.execute("""
                SELECT user_id, restriction_type, reason, moderator_id, timestamp, is_global 
                FROM command_restrictions 
                WHERE (guild_id = ? AND restriction_type = 'command_ban' AND is_global = 0)
                   OR (restriction_type = 'command_ban' AND is_global = 1)
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            """, (guild_id, per_page, offset))
            
            results = await cursor.fetchall()
            
            # Remove expired restrictions
            valid_bans = []
            for result in results:
                user_id, restriction_type, reason, moderator_id, timestamp, is_global = result
                
                # Check if restriction has expired (though command_ban typically doesn't expire)
                restriction = await self.get_command_restriction(guild_id, user_id)
                if restriction and restriction["type"] == "command_ban":
                    valid_bans.append(result)
            
            return valid_bans

    async def add_admin_user(self, user_id: int, reason: str, granted_by: int):
        """Add a user to the admin list"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO admin_users (user_id, reason, granted_by) VALUES (?, ?, ?)",
                (user_id, reason, granted_by)
            )
            await db.commit()

    async def remove_admin_user(self, user_id: int):
        """Remove a user from the admin list"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM admin_users WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def is_admin_user(self, user_id: int) -> bool:
        """Check if a user is an admin"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id FROM admin_users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result is not None

    async def get_all_admin_users(self):
        """Get all admin users"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id, reason, granted_by, timestamp FROM admin_users ORDER BY timestamp DESC"
            )
            return await cursor.fetchall()

    async def add_bot_owner(self, user_id: int, reason: str, granted_by: int):
        """Add a user to the bot owners list"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO bot_owners (user_id, reason, granted_by) VALUES (?, ?, ?)",
                (user_id, reason, granted_by)
            )
            await db.commit()

    async def remove_bot_owner(self, user_id: int):
        """Remove a user from the bot owners list"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM bot_owners WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def is_bot_owner_db(self, user_id: int) -> bool:
        """Check if a user is a bot owner in database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id FROM bot_owners WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result is not None

    async def get_all_bot_owners(self):
        """Get all bot owners"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id, reason, granted_by, timestamp FROM bot_owners ORDER BY timestamp DESC"
            )
            return await cursor.fetchall()

    async def add_server_command_ban(self, server_id: int, reason: str, banned_by: int, limit: int = None):
        """Add a server command ban"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO server_command_bans (server_id, reason, banned_by, ban_limit) VALUES (?, ?, ?, ?)",
                (server_id, reason, banned_by, limit)
            )
            await db.commit()

    async def remove_server_command_ban(self, server_id: int):
        """Remove a server command ban"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM server_command_bans WHERE server_id = ?",
                (server_id,)
            )
            await db.commit()

    async def is_server_command_banned(self, server_id: int) -> bool:
        """Check if a server is command banned"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT server_id FROM server_command_bans WHERE server_id = ?",
                (server_id,)
            )
            result = await cursor.fetchone()
            return result is not None

    async def get_server_command_ban(self, server_id: int):
        """Get server command ban details"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT reason, banned_by, ban_limit, timestamp FROM server_command_bans WHERE server_id = ?",
                (server_id,)
            )
            result = await cursor.fetchone()
            if result:
                return {
                    "reason": result[0],
                    "banned_by": result[1],
                    "limit": result[2],
                    "timestamp": result[3]
                }
            return None

    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
            self.db = None
            logger.info("Database connection closed")