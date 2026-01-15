import discord
import datetime
import asyncio
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

@bot.command()
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
async def MuteABitch(ctx: commands.Context, member: discord.Member, duration_minutes: int = 1, required_percent: int = 50)
    embed = discord.Embed(
        title="Mute a Bitch Poll",
        description= f"Do you want to timeout {member.mention} for {duration_minutes} minute(s)?",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Poll started by {ctx.author}")

    poll_message = await ctx.send(embed=embed)

    await poll_message.add_reaction("✅")
    await poll_message.add_reaction("❌")

    await asyncio.sleep(120)

    poll_message = await ctx.channel.fetch_message(poll_message.id)
    reactions = {str(r.emoji): r.count for r in poll_message.reactions}
    yes_votes = reactions.get("✅",0)
    no_votes = reactions.get("❌",0)
    total_votes = yes_votes + no_votes

    if total_votes == 0:
        await ctx.send("You all are a bunch of bitches.")
        return

    yes_percent = (yes_votes / total_votes) * 100
    if yes_percent >= required_percent:
        try:
            duration = datetime.timedelta(minutes=duration_minutes)
            await member.timeout(duration)
            await ctx.send(f"{member.mention} is a bitch so they got muted.")
        except discord.Forbidden:
            await ctx.send("I'm a bitch and can't mute this member.")
        except discord.HTTPException as e:
            await ctx.send(f"Couldn't contain its oil: {e}")
    else:
        await ctx.send("The Bitch Lives!")

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


# --------------------
# START EVERYTHING
# --------------------
if __name__ == "__main__":
    threading.Thread(
        target=run_discord_bot,
        daemon=True
    ).start()
    app.run(host="0.0.0.0", port=10000, use_reloader=False)
