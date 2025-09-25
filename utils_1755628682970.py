import discord
from discord.ext import commands
from functools import wraps

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