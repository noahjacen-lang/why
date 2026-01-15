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
    the defendant has 60 seconds to plead, then a poll decides their fate.
    Everyone is returned to their original channels afterward.
    """
    if defendant.voice is None:
        await ctx.send(f"{defendant.mention} is not in a voice channel!")
        return

    original_channel = defendant.voice.channel
    members_to_move = original_channel.members
    if not members_to_move:
        await ctx.send("No one is in the defendant's channel to move!")
        return

    member_orig_channels = {member: member.voice.channel for member in members_to_move}

    # Get or create Court-Room
    court_channel = discord.utils.get(ctx.guild.voice_channels, name="Court-Room")
    if court_channel is None:
        overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(connect=True)}
        court_channel = await ctx.guild.create_voice_channel("Court-Room", overwrites=overwrites)

    # Move everyone to Court-Room
    for member in members_to_move:
        try:
            await member.move_to(court_channel)
        except:
            pass

    await ctx.send(
        f"⚖️ **Trial of {defendant.mention} has begun!**\n"
        f"{defendant.mention}, you have 60 seconds to plead your case!"
    )
    await asyncio.sleep(60)

    # Create poll embed
    poll_embed = discord.Embed(
        title=f"Trial Poll for {defendant.display_name}",
        description=f"Should {defendant.mention} be muted for 5 minutes?\nReact below:",
        color=discord.Color.orange()
    )
    poll_embed.add_field(name="✅ Yes", value="0 votes", inline=False)
    poll_embed.add_field(name="❌ No", value="0 votes", inline=False)

    poll_msg = await ctx.send(embed=poll_embed)
    await poll_msg.add_reaction("✅")
    await poll_msg.add_reaction("❌")

    # Update poll every 5 seconds for 30 seconds
    poll_duration = 30
    update_interval = 5
    for _ in range(0, poll_duration, update_interval):
        await asyncio.sleep(update_interval)
        poll_msg = await ctx.channel.fetch_message(poll_msg.id)
        reactions = {str(r.emoji): r.count - 1 for r in poll_msg.reactions}  # subtract bot's reaction
        yes_votes = reactions.get("✅", 0)
        no_votes = reactions.get("❌", 0)

        poll_embed.set_field_at(0, name="✅ Yes", value=f"{yes_votes} votes", inline=False)
        poll_embed.set_field_at(1, name="❌ No", value=f"{no_votes} votes", inline=False)
        await poll_msg.edit(embed=poll_embed)

    # Final vote count
    poll_msg = await ctx.channel.fetch_message(poll_msg.id)
    reactions = {str(r.emoji): r.count - 1 for r in poll_msg.reactions}
    yes_votes = reactions.get("✅", 0)
    no_votes = reactions.get("❌", 0)
    total_votes = yes_votes + no_votes

    if total_votes == 0:
        await ctx.send("No votes were cast. Trial ends with no action.")
    else:
        yes_percent = (yes_votes / total_votes) * 100
        if yes_percent >= 50:
            try:
                await defendant.timeout(duration=datetime.timedelta(minutes=5))
                await ctx.send(f"{defendant.mention} has been muted for 5 minutes by the court!")
            except:
                await ctx.send("Could not timeout the defendant due to permissions.")
        else:
            await ctx.send(f"{defendant.mention} was acquitted by the court! ✅")

    # Move everyone back to their original channels
    for member, channel in member_orig_channels.items():
        try:
            if member.voice and member.voice.channel != channel:
                await member.move_to(channel)
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
