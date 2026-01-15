import discord
import datetime
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import threading
from flask import Flask

# --------------------
# ENV & LOGGING why

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

# Dynamic cooldown (owner bypass)
def stfu_cooldown(ctx: commands.Context):
    if ctx.guild and ctx.author.id == ctx.guild.owner_id:
        return None  # No cooldown

    return commands.Cooldown(1, 43200)

@bot.command()
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
@commands.dynamic_cooldown(stfu_cooldown, commands.BucketType.user)
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
async def stfu_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        hours = error.retry_after / 3600
        await ctx.send(
            f"Bitch chillout. You can mute again in {hours:.2f} hours."
        )
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")

def run_discord_bot():
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)

# --------------------
# FLASK SETUP
# --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord bot is running."

def start_discord():
    threading.Thread(target=run_discord_bot, daemon=True).start()
# --------------------
# START EVERYTHING
# --------------------
if __name__ == "__main__":
    start_discord()
    app.run(host="0.0.0.0", port=10000, use_reloader=False)
