import discord
import datetime
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import threading

from flask import Flask

# --------------------
# ENV & LOGGING
# --------------------
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(
    filename="discord.log",
    encoding="utf-8",
    mode="w"
)

# --------------------
# DISCORD SETUP
# --------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

def stfu_cooldown(ctx: commands.Context):
    # Server owner gets no cooldown
    if ctx.guild and ctx.author.id == ctx.guild.owner_id:
        return None  # No cooldown

    # Everyone else: 1 use per 24 hours
    return commands.Cooldown(1, 86400)


@bot.command()
@commands.has_permissions(moderate_members=True)
@commands.cooldown(1, 86400, commands.BucketType.user)
async def stfu(ctx: commands.Context, member: discord.Member):
    duration = datetime.timedelta(minutes=1)
    try:
        await member.timeout(duration)
        await ctx.send(f"{member.mention} is a bitch so they got muted.")
    except discord.Forbidden:
        await ctx.send("I'm a bitch and can't mute this member.")
    except discord.HTTPException as e:
        await ctx.send(f"Couldn't contain its oil: {e}")

@stfu.error
async def stfu(ctx: commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        hours = round(error.retry_after / 3600, 2)
        await ctx.send(f"Bitch chillout. You can't mute for another {24 - hours} hours.")
def run_discord_bot():
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)

# --------------------
# FLASK SETUP
# --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord bot is running."

# --------------------
# START EVERYTHING
# --------------------
if __name__ == "__main__":
    # Run Discord bot in background thread
    threading.Thread(target=run_discord_bot).start()

    # Run Flask web server
    app.run(host="0.0.0.0", port=10000, use_reloader=False)
