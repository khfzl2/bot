import discord
from discord.ext import commands
import logging
from ..utils import create_embed, create_error_embed, create_success_embed, has_permissions

logger = logging.getLogger(__name__)

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify")
    async def verify_user(self, ctx):
        """Verify yourself in the server"""
        if self.bot.database:
            # Check if already verified
            existing = await self.bot.database.get_verification_status(ctx.guild.id, ctx.author.id)
            if existing and existing[0]:  # If verified is True
                await ctx.send(embed=create_embed("Already Verified", "You are already verified in this server!"))
                return

            # Set as verified
            await self.bot.database.set_verification_status(ctx.guild.id, ctx.author.id, True)
            
            # Try to give verified role if configured
            verified_role_id = await self.bot.database.get_verification_role(ctx.guild.id)
            if verified_role_id:
                verified_role = ctx.guild.get_role(verified_role_id)
                if verified_role:
                    try:
                        await ctx.author.add_roles(verified_role, reason="User verification")
                    except discord.Forbidden:
                        pass  # Ignore if bot can't manage roles

            embed = create_success_embed("Verification Successful", "You have been verified in this server!")
            await ctx.send(embed=embed)

    @commands.command(name="unverify")
    @has_permissions(manage_roles=True)
    async def unverify_user(self, ctx, member: discord.Member):
        """Remove verification from a user"""
        if self.bot.database:
            await self.bot.database.set_verification_status(ctx.guild.id, member.id, False)
            
            # Try to remove verified role if configured
            verified_role_id = await self.bot.database.get_verification_role(ctx.guild.id)
            if verified_role_id:
                verified_role = ctx.guild.get_role(verified_role_id)
                if verified_role and verified_role in member.roles:
                    try:
                        await member.remove_roles(verified_role, reason=f"Unverified by {ctx.author}")
                    except discord.Forbidden:
                        pass  # Ignore if bot can't manage roles

            embed = create_success_embed("User Unverified", f"{member.mention} has been unverified.")
            await ctx.send(embed=embed)

    @commands.command(name="verifysetup")
    @has_permissions(manage_roles=True)
    async def verify_setup(self, ctx, role: discord.Role = None):
        """Set up the verification role for this server"""
        if not role:
            # Show current verification role
            current_role_id = await self.bot.database.get_verification_role(ctx.guild.id)
            if current_role_id:
                current_role = ctx.guild.get_role(current_role_id)
                if current_role:
                    embed = create_embed("Current Verification Role", f"The verification role is set to: {current_role.mention}")
                else:
                    embed = create_error_embed("Invalid Role", "The configured verification role no longer exists. Please set a new one.")
            else:
                embed = create_embed("No Verification Role", "No verification role is currently configured for this server.\nUse `k!verifysetup @role` to set one.")
            await ctx.send(embed=embed)
            return

        # Check if bot can manage this role
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=create_error_embed("Role Too High", "I cannot manage this role as it's higher than or equal to my highest role."))
            return

        # Check if the role is @everyone
        if role.id == ctx.guild.default_role.id:
            await ctx.send(embed=create_error_embed("Invalid Role", "Cannot use @everyone role for verification."))
            return

        # Set the verification role
        await self.bot.database.set_verification_role(ctx.guild.id, role.id)

        embed = create_success_embed(
            "✅ Verification Setup Complete",
            f"**Verification Role:** {role.mention}\n\n"
            f"Users who use `k!verify` will now receive the {role.name} role."
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
