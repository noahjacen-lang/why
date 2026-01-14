import discord
import datetime
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode="w")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True



bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
        print("Logged in as BitchBot")

@bot.command()
@commands.has_permissions(moderate_members=True) # Check if the command user has permission
async def stfu(ctx: commands.Context, member: discord.Member):
    duration = datetime.timedelta(minutes=1)
    """Server-mutes a user in a voice channel."""
    try:
        await member.timeout(duration)
        await ctx.send(f"{member.mention} is a bitch so they got muted.")
    except discord.Forbidden:
        await ctx.send("I'm a bitch and can't mute this member.")
    except discord.HTTPException as e:
        await ctx.send(f"Couldn't contain its oil: {e}")

#Don't forget to run your bot with your token
bot.run('MTQ2MDgyNTYzMTQ5ODY5ODkxNA.GtO98h.57v_lk0oOV4qxE1WMO0_RSBhUzpSPQWK3cP5xU', log_handler=handler, log_level=logging.INFO)
