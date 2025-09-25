import discord
from discord.ext import commands
from functools import wraps

# Bot owners list - SECURITY: Using user IDs instead of usernames to prevent spoofing
# IMPORTANT: Replace these placeholder IDs with actual Discord user IDs
BOT_OWNERS = [
    1155072620438503536,  # Replace with kh2.officialeditz's actual user ID
    987654321098765432,  # Replace with r3act0r_editzofficial's actual user ID
]

def is_bot_owner(user):
    """Check if user is one of the hardcoded bot owners using secure user ID"""
    return user.id in BOT_OWNERS

async def is_super_admin(user, database):
    """Check if user is a hardcoded owner OR database bot owner (super admin)"""
    if is_bot_owner(user):
        return True
    if database:
        return await database.is_bot_owner_db(user.id)
    return False

def create_embed(title, description, color=discord.Color.blue()):
    """Create a standard embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

def create_error_embed(title, description):
    """Create an error embed"""
    return create_embed(title, description, discord.Color.red())

def create_success_embed(title, description):
    """Create a success embed"""
    return create_embed(title, description, discord.Color.green())

def has_permissions(**permissions):
    """Decorator to check if user has required permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            # Check if user has required permissions
            missing_permissions = []
            for perm, required in permissions.items():
                if not getattr(ctx.author.guild_permissions, perm, False):
                    missing_permissions.append(perm.replace('_', ' ').title())
            
            if missing_permissions:
                embed = create_error_embed(
                    "Insufficient Permissions",
                    f"You need the following permissions: {', '.join(missing_permissions)}"
                )
                await ctx.send(embed=embed)
                return
            
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator
