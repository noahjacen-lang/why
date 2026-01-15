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
async def MuteABitch(ctx: commands.Context, member: discord.Member, duration_minutes: int = 1, required_percent: int = 50):
    embed = discord.Embed(
        title="Mute a Bitch Poll",
        description= f"Do you want to timeout {member.mention} for {duration_minutes} minute(s)?",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Poll started by {ctx.author}")

    poll_message = await ctx.send(embed=embed)

    await poll_message.add_reaction("✅")
    await poll_message.add_reaction("❌")

    await asyncio.sleep(45)

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

@bot.command()
@commands.has_permissions(moderate_members=True)
async def JudgeABitch(ctx, defendant: discord.Member):
    """
    Starts a trial where everyone in the defendant's voice channel is moved to Court-Room,
    and the defendant has 60 seconds to plead.
    """
    # Check if defendant is in a voice channel
    if defendant.voice is None:
        await ctx.send(f"{defendant.mention} is not in a voice channel!")
        return

    original_channel = defendant.voice.channel

    # Check if Court-Room exists, otherwise create it
    court_channel = discord.utils.get(ctx.guild.voice_channels, name="Court-Room")
    if court_channel is None:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=True)
        }
        court_channel = await ctx.guild.create_voice_channel("Court-Room", overwrites=overwrites)

    # Get all members in the defendant's channel
    members_to_move = original_channel.members
    if not members_to_move:
        await ctx.send("No one is in the defendant's channel to move!")
        return

    # Move everyone to Court-Room
    for member in members_to_move:
        try:
            await member.move_to(court_channel)
        except discord.Forbidden:
            await ctx.send(f"Can't move {member.mention} due to permissions.")
        except discord.HTTPException:
            await ctx.send(f"Failed to move {member.mention}.")

    # Announce the trial
    trial_msg = await ctx.send(
        f"⚖️ **Trial of {defendant.mention} has begun!**\n"
        f"{defendant.mention}, you have 60 seconds to plead your case!"
    )

    # Wait 60 seconds for defendant to plead
    await asyncio.sleep(60)

    # Create vote message
    vote_msg = await ctx.send(
        f"🗳️ **Vote: Should {defendant.mention} be muted for 1 minute?**\n"
        "✅ = Yes\n❌ = No"
    )
    await vote_msg.add_reaction("✅")
    await vote_msg.add_reaction("❌")


    # Start poll
    vote_msg = await ctx.send(
        f"🗳️ **Vote: Should {defendant.mention} be muted for 1 minute?**\n"
        "✅ = Yes\n❌ = No"
    )
    await vote_msg.add_reaction("✅")
    await vote_msg.add_reaction("❌")

    # Wait 30 seconds for votes
    await asyncio.sleep(15)

    # Fetch updated reactions
    vote_msg = await ctx.channel.fetch_message(vote_msg.id)
    reactions = {str(r.emoji): r.count - 1 for r in vote_msg.reactions}  # subtract bot's reaction
    yes_votes = reactions.get("✅", 0)
    no_votes = reactions.get("❌", 0)
    total_votes = yes_votes + no_votes

    # Decide outcome
    if total_votes == 0:
        await ctx.send("No votes were cast. Trial ends with no action.")
    else:
        yes_percent = (yes_votes / total_votes) * 100
        if yes_percent >= 50:
            try:
                await defendant.timeout(duration=datetime.timedelta(minutes=5))
                await ctx.send(f"{defendant.mention} has been muted for 1 minute by the court!")
            except discord.Forbidden:
                await ctx.send("I don't have permission to timeout the defendant.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to timeout defendant: {e}")
        else:
            await ctx.send(f"{defendant.mention} was acquitted by the court! ✅")

    # Move everyone back to original channel
    for member in members_to_move:
        try:
            await member.move_to(original_channel)
        except:
            pass

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
