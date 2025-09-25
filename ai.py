import discord
from discord.ext import commands
import aiohttp
import logging
import os
import json
from ..utils import create_embed, create_error_embed, create_success_embed

logger = logging.getLogger(__name__)

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize OpenRouter API settings
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    @commands.command(name="createimage", aliases=["genimage", "imagine"])
    async def create_image(self, ctx, *, description: str):
        """Generate an AI image based on your description

        Usage: k!createimage <description>
        Example: k!createimage a cute cat wearing a wizard hat in a magical forest
        """
        if len(description) > 1000:
            await ctx.send(embed=create_error_embed("Description Too Long", "Please keep your description under 1000 characters."))
            return

        embed = create_embed("🎨 Generating Image...", f"Creating an image based on: `{description}`\nThis may take a moment...")
        message = await ctx.send(embed=embed)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://replit.com",
                    "X-Title": "Discord Bot"
                }
                
                payload = {
                    "model": "openai/dall-e-3",
                    "prompt": description,
                    "size": "1024x1024",
                    "quality": "standard",
                    "n": 1
                }
                
                async with session.post(f"{self.base_url}/images/generations", headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        image_url = data["data"][0]["url"]
                        
                        embed = discord.Embed(
                            title="🎨 AI Generated Image (DALL-E 3)",
                            description=f"**Your prompt:** {description}",
                            color=discord.Color.purple()
                        )
                        embed.set_image(url=image_url)
                        embed.set_footer(text=f"Generated for {ctx.author.display_name}")
                        
                        await message.edit(embed=embed)
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        await message.edit(embed=create_error_embed("Image Generation Failed", "Sorry, I couldn't generate the image. Please try again later."))

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            await message.edit(embed=create_error_embed("Image Generation Failed", "Sorry, I couldn't generate the image. Please try again later."))

    @commands.command(name="question", aliases=["ask", "ai"])
    async def ask_question(self, ctx, *, question: str):
        """Ask AI a question and get an intelligent response"""
        if len(question) > 2000:
            await ctx.send(embed=create_error_embed("Question Too Long", "Please keep your question under 2000 characters."))
            return

        embed = create_embed("🤖 Thinking...", f"Processing your question: `{question}`")
        message = await ctx.send(embed=embed)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://replit.com",
                    "X-Title": "Discord Bot"
                }
                
                payload = {
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant in a Discord server. Keep responses concise and friendly."},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
                
                async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        answer = data["choices"][0]["message"]["content"]

                        embed = discord.Embed(
                            title="🤖 AI Response (DeepSeek)",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Question", value=question, inline=False)
                        embed.add_field(name="Answer", value=answer, inline=False)
                        embed.set_footer(text=f"Asked by {ctx.author.display_name}")

                        await message.edit(embed=embed)
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        await message.edit(embed=create_error_embed("AI Response Failed", "Sorry, I couldn't process your question. Please try again later."))

        except Exception as e:
            logger.error(f"Error processing question: {e}")
            await message.edit(embed=create_error_embed("AI Response Failed", "Sorry, I couldn't process your question. Please try again later."))

    @commands.command(name="aimodel", aliases=["model"])
    async def ai_model_info(self, ctx):
        """Show information about the current AI model"""
        embed = create_embed(
            "🤖 AI Model Information",
            "**Text Model:** DeepSeek Chat (via OpenRouter)\n"
            "**Image Model:** GPT-4 (via OpenRouter)\n"
            "**API Provider:** OpenRouter AI\n\n"
            "Use `k!question` or `k!ask` to chat with DeepSeek\n"
            "Use `k!createimage` to generate images with GPT-4"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AICog(bot))