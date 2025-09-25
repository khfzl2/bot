import discord
from discord.ext import commands
import random
import asyncio
import datetime
import json
from ..utils import create_embed, create_error_embed

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="8ball")
    async def eight_ball(self, ctx, *, question: str = None):
        """Ask the magic 8-ball a question"""
        if not question:
            await ctx.send(embed=create_error_embed("Missing Question", "Please ask a question!"))
            return

        responses = [
            "It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
            "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
            "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
            "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good",
            "Very doubtful"
        ]

        response = random.choice(responses)
        embed = create_embed("🎱 Magic 8-Ball", f"**Question:** {question}\n**Answer:** {response}")
        await ctx.send(embed=embed)

    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coin_flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        embed = create_embed("🪙 Coin Flip", f"The coin landed on: **{result}**")
        await ctx.send(embed=embed)

    @commands.command(name="dice", aliases=["roll"])
    async def roll_dice(self, ctx, sides: int = 6):
        """Roll a dice with specified number of sides (default 6)"""
        if sides < 2 or sides > 100:
            await ctx.send(embed=create_error_embed("Invalid Dice", "Dice must have between 2 and 100 sides."))
            return

        result = random.randint(1, sides)
        embed = create_embed("🎲 Dice Roll", f"You rolled a **{result}** on a {sides}-sided dice!")
        await ctx.send(embed=embed)

    @commands.command(name="joke")
    async def random_joke(self, ctx):
        """Get a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't a bicycle stand up by itself? It's two tired!",
            "What do you call a sleeping bull? A bulldozer!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus!"
        ]

        joke = random.choice(jokes)
        embed = create_embed("😂 Random Joke", joke)
        await ctx.send(embed=embed)

    @commands.command(name="choose", aliases=["pick"])
    async def choose_option(self, ctx, *choices):
        """Choose between multiple options"""
        if len(choices) < 2:
            await ctx.send(embed=create_error_embed("Not Enough Options", "Please provide at least 2 options to choose from."))
            return

        choice = random.choice(choices)
        embed = create_embed("🤔 Choice Made", f"I choose: **{choice}**")
        await ctx.send(embed=embed)

    @commands.command(name="love")
    async def love_calculator(self, ctx, person1: str, person2: str = None):
        """Calculate love compatibility between two people"""
        if not person2:
            person2 = ctx.author.display_name

        # Simple hash-based "calculation" for consistency
        combined = person1.lower() + person2.lower()
        love_score = abs(hash(combined)) % 101

        if love_score >= 90:
            result = "💕 Perfect Match!"
        elif love_score >= 70:
            result = "💖 Great Compatibility!"
        elif love_score >= 50:
            result = "💛 Good Potential!"
        elif love_score >= 30:
            result = "💙 Some Chemistry!"
        else:
            result = "💔 Not Meant to Be..."

        embed = create_embed("💕 Love Calculator", f"**{person1}** + **{person2}** = **{love_score}%**\n{result}")
        await ctx.send(embed=embed)

    @commands.command(name="rps")
    async def rock_paper_scissors(self, ctx, choice: str = None):
        """Play Rock, Paper, Scissors"""
        if not choice:
            await ctx.send(embed=create_error_embed("Missing Choice", "Choose rock, paper, or scissors!"))
            return

        choice = choice.lower()
        if choice not in ['rock', 'paper', 'scissors', 'r', 'p', 's']:
            await ctx.send(embed=create_error_embed("Invalid Choice", "Choose rock, paper, or scissors!"))
            return

        # Normalize choice
        if choice in ['r', 'rock']:
            user_choice = 'rock'
        elif choice in ['p', 'paper']:
            user_choice = 'paper'
        elif choice in ['s', 'scissors']:
            user_choice = 'scissors'

        bot_choice = random.choice(['rock', 'paper', 'scissors'])

        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie!"
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'paper' and bot_choice == 'rock') or \
             (user_choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
        else:
            result = "I win!"

        embed = create_embed("✂️ Rock Paper Scissors", f"You: {user_choice.title()}\nBot: {bot_choice.title()}\n\n**{result}**")
        await ctx.send(embed=embed)

    @commands.command(name="dadjoke")
    async def dad_joke(self, ctx):
        """Get a random dad joke"""
        dad_jokes = [
            "I'm afraid for the calendar. Its days are numbered.",
            "My wife said I should do lunges to stay in shape. That would be a big step forward.",
            "Why do fathers take an extra pair of socks when they go golfing? In case they get a hole in one!",
            "Singing in the shower is fun until you get soap in your mouth. Then it's a soap opera.",
            "What do you call a fish wearing a bowtie? Sofishticated.",
            "How do you organize a space party? You planet.",
            "I only know 25 letters of the alphabet. I don't know y.",
            "What did the ocean say to the beach? Nothing, it just waved.",
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks."
        ]

        joke = random.choice(dad_jokes)
        embed = create_embed("👨 Dad Joke", joke)
        await ctx.send(embed=embed)

    @commands.command(name="meme")
    async def meme_command(self, ctx):
        """Get a random meme quote"""
        memes = [
            "That's what she said! 😏",
            "No u 🔄",
            "This is fine 🔥☕",
            "Much wow, very meme! 🐕",
            "I can has cheezburger? 🍔",
            "One does not simply... walk into Mordor 🚶‍♂️",
            "Y U NO work?! 😤",
            "All your base are belong to us 💻",
            "The cake is a lie! 🎂",
            "Hello there! General Kenobi! ⚔️"
        ]

        meme = random.choice(memes)
        embed = create_embed("😂 Random Meme", meme)
        await ctx.send(embed=embed)

    @commands.command(name="fortune")
    async def fortune(self, ctx):
        """Get your fortune told"""
        fortunes = [
            "A great fortune awaits you! 🔮💰",
            "Love is in your future! 🔮❤️",
            "Adventure calls to you! 🔮🗺️",
            "Wisdom will guide your path! 🔮🦉",
            "Good luck is coming your way! 🔮🍀",
            "A new friendship will bloom! 🔮👫",
            "Success is within your reach! 🔮🏆",
            "Happiness will find you! 🔮😊"
        ]
        fortune = random.choice(fortunes)
        embed = create_embed("🔮 Fortune", f"{fortune}")
        await ctx.send(embed=embed)

    @commands.command(name="transform")
    async def transform(self, ctx):
        """Transform into something random"""
        transformations = [
            "transforms into a dragon! 🐉",
            "becomes a unicorn! 🦄",
            "turns into a wolf! 🐺",
            "becomes a phoenix! 🔥🐦",
            "transforms into a mermaid! 🧜‍♀️",
            "becomes a vampire! 🧛‍♂️",
            "turns into a wizard! 🧙‍♂️",
            "transforms into an angel! 😇"
        ]
        transformation = random.choice(transformations)
        embed = create_embed("✨ Transformation", f"{ctx.author.display_name} {transformation}")
        await ctx.send(embed=embed)

    @commands.command(name="scream")
    async def scream(self, ctx):
        """Express fear"""
        screams = [
            "AAAAHHHHHHH!",
            "screams at the top of their lungs!",
            "lets out a blood-curdling scream!",
            "screams like they saw a spider!",
            "screams in frustration!"
        ]
        scream = random.choice(screams)
        embed = create_embed("😱 Scream", f"{ctx.author.display_name} {scream}")
        await ctx.send(embed=embed)

    @commands.command(name="facepalm")
    async def facepalm(self, ctx):
        """Express disappointment with a facepalm"""
        embed = create_embed("🤦 Facepalm", f"{ctx.author.display_name} *facepalms* Why did I do that?!")
        await ctx.send(embed=embed)

    @commands.command(name="shrug")
    async def shrug(self, ctx):
        """Shrug it off"""
        embed = create_embed("🤷 Shrug", f"{ctx.author.display_name} ¯\\_(ツ)_/¯")
        await ctx.send(embed=embed)

    @commands.command(name="clap")
    async def clap(self, ctx):
        """Clap your hands"""
        embed = create_embed("👏 Clap", f"{ctx.author.display_name} *clap clap clap* Well done!")
        await ctx.send(embed=embed)

    @commands.command(name="wave")
    async def wave(self, ctx, member: discord.Member = None):
        """Wave at someone"""
        if not member:
            embed = create_embed("👋 Wave", f"{ctx.author.display_name} waves at everyone! Hello!")
        else:
            embed = create_embed("👋 Wave", f"{ctx.author.display_name} waves at {member.display_name}! 👋")
        await ctx.send(embed=embed)

    @commands.command(name="pet")
    async def pet(self, ctx, member: discord.Member = None):
        """Pet someone gently"""
        if not member:
            embed = create_embed("🐾 Pet", f"{ctx.author.display_name} pets an imaginary cat!")
        elif member == ctx.author:
            embed = create_embed("🐾 Self Pet", f"{ctx.author.display_name} pets themselves! How flexible!")
        else:
            embed = create_embed("🐾 Pet", f"{ctx.author.display_name} gently pets {member.display_name}! *pat pat*")
        await ctx.send(embed=embed)

    @commands.command(name="boop")
    async def boop(self, ctx, member: discord.Member = None):
        """Boop someone's nose"""
        if not member:
            embed = create_embed("👃 Boop", f"{ctx.author.display_name} boops the air! *boop*")
        elif member == ctx.author:
            embed = create_embed("👃 Self Boop", f"{ctx.author.display_name} boops their own nose! *boop*")
        else:
            embed = create_embed("👃 Boop", f"{ctx.author.display_name} boops {member.display_name}'s nose! *boop*")
        await ctx.send(embed=embed)

    @commands.command(name="zombie")
    async def zombie(self, ctx):
        """Become a zombie"""
        embed = create_embed("🧟 Zombie", f"{ctx.author.display_name} becomes a zombie! *groooooan* Braaaains!")
        await ctx.send(embed=embed)

    @commands.command(name="dance")
    async def dance(self, ctx):
        """Start dancing"""
        dances = [
            "does the robot! 🤖",
            "breaks it down! 💃",
            "does the moonwalk! 🌙",
            "starts breakdancing! 🕺",
            "does the floss! 💪"
        ]
        dance = random.choice(dances)
        embed = create_embed("💃 Dance", f"{ctx.author.display_name} {dance}")
        await ctx.send(embed=embed)

    @commands.command(name="hug")
    async def hug(self, ctx, member: discord.Member = None):
        """Give someone a hug"""
        if not member:
            embed = create_embed("🤗 Hug", f"{ctx.author.display_name} gives everyone a big hug! 🤗")
        elif member == ctx.author:
            embed = create_embed("🤗 Self Hug", f"{ctx.author.display_name} hugs themselves! Self-love is important! 💕")
        else:
            embed = create_embed("🤗 Hug", f"{ctx.author.display_name} gives {member.display_name} a warm hug! 🤗💕")
        await ctx.send(embed=embed)

    @commands.command(name="slap")
    async def slap(self, ctx, member: discord.Member = None):
        """Playfully slap someone"""
        if not member:
            embed = create_embed("👋 Slap", f"{ctx.author.display_name} slaps the air! *whoosh*")
        elif member == ctx.author:
            embed = create_embed("👋 Self Slap", f"{ctx.author.display_name} slaps themselves! Ouch!")
        else:
            embed = create_embed("👋 Slap", f"{ctx.author.display_name} playfully slaps {member.display_name}! 👋")
        await ctx.send(embed=embed)

    @commands.command(name="kiss")
    async def kiss(self, ctx, member: discord.Member = None):
        """Give someone a kiss"""
        if not member:
            embed = create_embed("💋 Kiss", f"{ctx.author.display_name} blows a kiss to everyone! 💋")
        elif member == ctx.author:
            embed = create_embed("💋 Self Kiss", f"{ctx.author.display_name} kisses themselves in the mirror! 💋")
        else:
            embed = create_embed("💋 Kiss", f"{ctx.author.display_name} gives {member.display_name} a sweet kiss! 💋")
        await ctx.send(embed=embed)

    @commands.command(name="punch")
    async def punch(self, ctx, member: discord.Member = None):
        """Playfully punch someone"""
        if not member:
            embed = create_embed("👊 Punch", f"{ctx.author.display_name} punches the air! *swoosh*")
        elif member == ctx.author:
            embed = create_embed("👊 Self Punch", f"{ctx.author.display_name} punches themselves! Why?!")
        else:
            embed = create_embed("👊 Punch", f"{ctx.author.display_name} playfully punches {member.display_name}! 👊")
        await ctx.send(embed=embed)

    @commands.command(name="cry")
    async def cry(self, ctx):
        """Start crying"""
        reasons = [
            "starts crying because they dropped their ice cream! 😭🍦",
            "cries tears of joy! 😭💕",
            "is crying because they're cutting onions! 😭🧅",
            "cries because they watched a sad movie! 😭🎬",
            "is crying happy tears! 😭✨"
        ]
        reason = random.choice(reasons)
        embed = create_embed("😭 Cry", f"{ctx.author.display_name} {reason}")
        await ctx.send(embed=embed)

    @commands.command(name="laugh")
    async def laugh(self, ctx):
        """Start laughing"""
        laughs = [
            "starts laughing uncontrollably! 😂",
            "giggles like a little kid! 😄",
            "laughs so hard they snort! 😂",
            "can't stop laughing! 🤣",
            "is rolling on the floor laughing! 🤣"
        ]
        laugh = random.choice(laughs)
        embed = create_embed("😂 Laugh", f"{ctx.author.display_name} {laugh}")
        await ctx.send(embed=embed)

    @commands.command(name="sleep")
    async def sleep(self, ctx):
        """Go to sleep"""
        embed = create_embed("😴 Sleep", f"{ctx.author.display_name} falls asleep... 😴💤 Zzz...")
        await ctx.send(embed=embed)

    @commands.command(name="eat")
    async def eat(self, ctx):
        """Eat something random"""
        foods = [
            "eats a delicious pizza! 🍕",
            "munches on some cookies! 🍪",
            "enjoys a burger! 🍔",
            "eats some ice cream! 🍦",
            "devours a cake! 🎂",
            "snacks on chips! 🍟",
            "eats a healthy salad! 🥗"
        ]
        food = random.choice(foods)
        embed = create_embed("🍽️ Eat", f"{ctx.author.display_name} {food}")
        await ctx.send(embed=embed)

    @commands.command(name="magic")
    async def magic(self, ctx):
        """Perform magic"""
        magic_tricks = [
            "pulls a rabbit out of a hat! 🎩🐰",
            "makes a coin disappear! ✨🪙",
            "turns water into wine! ✨🍷",
            "makes flowers appear! ✨🌸",
            "casts a spell! ✨🪄"
        ]
        trick = random.choice(magic_tricks)
        embed = create_embed("✨ Magic", f"{ctx.author.display_name} {trick}")
        await ctx.send(embed=embed)

    @commands.command(name="superhero")
    async def superhero(self, ctx):
        """Become a superhero"""
        heroes = [
            "becomes Superman! 🦸‍♂️",
            "transforms into Wonder Woman! 🦸‍♀️",
            "becomes Batman! 🦇",
            "turns into Spider-Man! 🕷️",
            "becomes The Flash! ⚡",
            "transforms into Captain Marvel! ⭐"
        ]
        hero = random.choice(heroes)
        embed = create_embed("🦸 Superhero", f"{ctx.author.display_name} {hero}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FunCog(bot))