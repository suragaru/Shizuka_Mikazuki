import discord
import datetime
import asyncio
import yt_dlp as youtube_dl
from discord.ext import commands, tasks
import random
import aiohttp
import re
import json
import os
import bible_verse_module 
import music_module  
import anime_module 
import astronomy_module
#from anime_module import fetch_anime_data
import logging
from bs4 import BeautifulSoup
import requests
import time
from colorlog import ColoredFormatter

# Set up logging with colorlog
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    },
    secondary_log_colors={},
    style='%'
)

logger = logging.getLogger('discord')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Set up logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logger = logging.getLogger(__name__)


# Initialize bot and intents
intents = discord.Intents.default()
intents.message_content = True  # Required for the `on_message` event

bot = commands.Bot(command_prefix="!", intents=intents)

# Record the start time
start_time = time.time()

# Define the URL of the webpage you want to scrape
main_url_news = 'https://asia.nikkei.com/Location/Rest-of-the-World'
jp_url_news = 'https://asia.nikkei.com/Location/East-Asia/Japan?gad_source=1&gclid=CjwKCAjwko21BhAPEiwAwfaQCCm2n55bexCCSDpcMYjc2yh_xJU7TqxDbYDABvUqzpIxIEegj9lmjhoCsrAQAvD_BwE'
ph_url_news= "https://asia.nikkei.com/Location/Southeast-Asia/Philippines"


# Your bot token
TOKEN = "YOUR_DISCORD_BOT_TOKEN"
YOUR_USER_ID = YOUR_DISCORD_USER_ID

# Files to save active channel IDs
ANNOUNCEMENT_CHANNEL_FILE = 'active_announcement_channels.json'
BIBLE_VERSE_CHANNEL_FILE = 'active_bible_verse_channels.json'

# Ensure the JSON files exist
for file in [ANNOUNCEMENT_CHANNEL_FILE, BIBLE_VERSE_CHANNEL_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([], f)

# Load active channel IDs from file
def load_active_channels(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save active channel IDs to file
def save_active_channels(channels, file):
    with open(file, 'w') as f:
        json.dump(channels, f)


@tasks.loop(time=datetime.time(hour=12, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))))
async def send_astronomy_announcement():
    logger.info("System is sending astronomy announcement.")
    active_channels = load_active_channels(ANNOUNCEMENT_CHANNEL_FILE)  # Load active channels before sending announcements
    astronomy_message = astronomy_module.astronomy()
    if astronomy_message:  # Check if there's an astronomy announcement to send
        for channel_id in active_channels:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(f"**Astronomy Event Announcement @everyone!** \n\n{astronomy_message}\n\nHave a good day! ✨")



@tasks.loop(time=datetime.time(hour=8, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))))
async def send_news():
    logger.info("System is sending news announcement.")
    active_channels = load_active_channels(ANNOUNCEMENT_CHANNEL_FILE)  # Load active channels before sending announcements
    try:
        response = requests.get(main_url_news)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        start_after_first_item = soup.find('span', class_='ezstring-field')
        if start_after_first_item:
            card_bodies = []
            for sibling in start_after_first_item.find_all_next('div', class_='card__body'):
                card_bodies.append(sibling)

            message = ""
            for card in card_bodies[:6]:
                link = card.find('a', href=True)
                if link:
                    full_link = f"https://asia.nikkei.com{link['href']}"
                    message += f"{full_link}\n"

            for channel_id in active_channels:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(f"\n{message}\n**Latest News Here! **\n.")
        else:
            logger.error("Start item not found in the HTML.")
            for channel_id in active_channels:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send("Failed to find news items in the webpage.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error during news retrieval: {e}")
        for channel_id in active_channels:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(f"Failed to retrieve the webpage. Error: {e}")
    except Exception as e:
        logger.error(f"Error during news processing: {e}")
        for channel_id in active_channels:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(f"An error occurred while processing the news. Error: {e}")



def activate_all_announcements(channel):
    active_channels = load_active_channels()
    if channel.id not in active_channels:
        active_channels.append(channel.id)
        save_active_channels(active_channels)
    if not send_astronomy_announcements.is_running():
        send_astronomy_announcements.start()
    if not send_news_in_channels.is_running():
        send_news_in_channels.start()
    return f"All announcements activated in {channel.mention}"

def deactivate_all_announcements(channel):
    active_channels = load_active_channels()
    if channel.id in active_channels:
        active_channels.remove(channel.id)
        save_active_channels(active_channels)
    if send_astronomy_announcements.is_running():
        send_astronomy_announcements.stop()
    if send_news_in_channels.is_running():
        send_news_in_channels.stop()
    return f"All announcements deactivated in {channel.mention}"


@bot.tree.command(name="activate_all_announcement")
async def activate_all_announcement_command(interaction: discord.Interaction, channel: discord.TextChannel):
    logger.info(f"/activate_all_announcement is used by {interaction.user} in {interaction.guild} for channel {channel.name}")
    response = activate_all_announcements(channel)
    await interaction.response.send_message(response)

@bot.tree.command(name="deactivate_all_announcement")
async def deactivate_all_announcement_command(interaction: discord.Interaction, channel: discord.TextChannel):
    logger.info(f"/deactivate_all_announcement is used by {interaction.user} in {interaction.guild} for channel {channel.name}")
    response = deactivate_all_announcements(channel)
    await interaction.response.send_message(response)



@tasks.loop(time=datetime.time(hour=7, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))))
async def send_daily_verse():
    logger.info("send_daily_verse task is running.")
    try:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        current_month = now.strftime("%B")
        current_day = now.day
        month_verses = bible_verse_module.bible_verses.get(current_month, {})
        verse = month_verses.get(current_day, "No verse for today.")
        
        active_channels = load_active_channels(BIBLE_VERSE_CHANNEL_FILE)
        logger.info(f"Active channels for Bible verses: {active_channels}")

        for channel_id in active_channels:
            channel = bot.get_channel(channel_id)
            if channel:
                logger.info(f"Sending Bible verse to channel {channel.name} ({channel.id})")
                await channel.send(f"**Daily Bible Verse @everyone!** \n\n*{verse}*\n\nHave a blessed day! 💗")
            else:
                logger.warning(f"Channel with ID {channel_id} not found.")
    except Exception as e:
        logger.error(f"Error in send_daily_verse task: {e}")


def activate_daily_bible_verse(channel):
    active_channels = load_active_channels(BIBLE_VERSE_CHANNEL_FILE)
    if channel.id not in active_channels:
        active_channels.append(channel.id)
        save_active_channels(active_channels, BIBLE_VERSE_CHANNEL_FILE)
    if not send_daily_verse.is_running():
        send_daily_verse.start()
    return f"Daily Bible Verse activated in {channel.mention}"

def deactivate_daily_bible_verse(channel):
    active_channels = load_active_channels(BIBLE_VERSE_CHANNEL_FILE)
    if channel.id in active_channels:
        active_channels.remove(channel.id)
        save_active_channels(active_channels, BIBLE_VERSE_CHANNEL_FILE)
    return f"Daily Bible Verse deactivated in {channel.mention}"


@bot.tree.command(name="activate_daily_bible_verse")
async def activate_daily_bible_verse_command(interaction: discord.Interaction, channel: discord.TextChannel):
    logger.info(f"/activate_daily_bible_verse is used by {interaction.user} in {interaction.guild} for channel {channel.name}")
    response = activate_daily_bible_verse(channel)
    await interaction.response.send_message(response)

@bot.tree.command(name="deactivate_daily_bible_verse")
async def deactivate_daily_bible_verse_command(interaction: discord.Interaction, channel: discord.TextChannel):
    logger.info(f"/deactivate_daily_bible_verse is used by {interaction.user} in {interaction.guild} for channel {channel.name}")
    response = deactivate_daily_bible_verse(channel)
    await interaction.response.send_message(response)

@bot.tree.command(name="random_bible_verse")
async def random_bible_verse_command(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        logger.info(f"/random_bible_verse is used by {interaction.user} in DMs")
    else:
        logger.info(f"/random_bible_verse is used by {interaction.user} in {interaction.guild} for channel {interaction.channel.name}")

    all_verses = []
    for month in bible_verse_module.bible_verses.values():
        all_verses.extend(month.values())

    if all_verses:
        verse = random.choice(all_verses)
        await interaction.response.send_message(f"**Random Bible Verse!** \n\n*{verse}*\n\nHave a blessed day! 💗")
    else:
        await interaction.response.send_message("No Verses available.")



@bot.tree.command(name='anisearch', description='Search for anime details')
async def anisearch(interaction: discord.Interaction, title: str):
    if isinstance(interaction.channel, discord.DMChannel):
        logger.info(f"/anisearch is used by {interaction.user} in DMs with title '{title}'")
    else:
        logger.info(f"/anisearch is used by {interaction.user} in {interaction.guild} for channel {interaction.channel.name} with title '{title}'")
    
    if not title:
        await interaction.response.send_message("Please provide an anime title to search.")
        return

    data = await anime_module.fetch_anime_data(title)
    if data:
        media = data['data']['Media']
        if media:
            title = media['title']['romaji']
            english_title = media['title']['english'] or "N/A"
            description = anime_module.clean_html_tags(media['description'])  # Clean HTML tags from the description
            genres = ', '.join(media['genres'])
            format_ = media.get('format', 'N/A')
            episodes = media.get('episodes', 'N/A')
            status = media.get('status', 'N/A')
            season = media.get('season', 'N/A')
            favourites = media.get('favourites', 'N/A')
            anime_url = media['siteUrl']

            # Start and End Dates
            start_date = f"{media['startDate']['year']}-{media['startDate']['month']:02d}-{media['startDate']['day']:02d}" if media['startDate']['year'] else "Unknown"
            end_date = f"{media['endDate']['year']}-{media['endDate']['month']:02d}-{media['endDate']['day']:02d}" if media['endDate']['year'] else "Unknown"
            
            # Additional Information
            average_score = media.get('averageScore', 'N/A')
            popularity = media.get('popularity', 'N/A')
            studios = ', '.join(studio['name'] for studio in media['studios']['nodes'])
            cover_image_url = media['coverImage']['large'] if media.get('coverImage') else None
            banner_image_url = media.get('bannerImage') if media.get('bannerImage') else None

            embed = discord.Embed(
                title=f"{title} ({english_title})",  # Combined title with both titles
                description=description,
                color=discord.Color.blue(),
                url=anime_url  # Make the entire embed clickable
            )

            # Add cover image as a large image field
            if cover_image_url:
                embed.set_thumbnail(url=cover_image_url)  # Set cover image as a thumbnail

            embed.add_field(name="Genres", value=genres, inline=False)
            embed.add_field(name="Format", value=format_, inline=False)
            embed.add_field(name="Episodes", value=episodes, inline=False)
            embed.add_field(name="Status", value=status, inline=False)
            embed.add_field(name="Season", value=season, inline=False)
            embed.add_field(name="Start Date", value=start_date, inline=False)
            embed.add_field(name="End Date", value=end_date, inline=False)
            embed.add_field(name="Average Score", value=average_score, inline=False)
            embed.add_field(name="Popularity", value=popularity, inline=False)
            embed.add_field(name="Favorites", value=favourites, inline=False)
            embed.add_field(name="Studios", value=studios or "N/A", inline=False)

            # Add banner image as a large image field
            if banner_image_url:
                embed.set_image(url=banner_image_url)  # Set banner image as a large image

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Anime not found.")
    else:
        await interaction.response.send_message("An error occurred while fetching the data.")



@bot.tree.command(name="info")
async def help_command(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        logger.info(f"/info is used by {interaction.user} in DMs")
    else:
        logger.info(f"/info is used by {interaction.user} in {interaction.guild} for channel {interaction.channel.name}")

    embed = discord.Embed(
        title="Hey there, Shizuka here!",
        description="Here is a list of what I can do:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Announcements:",
        value="`/activate_all_announcements`  - Receive all announcements about news and upcoming astronomy events.\n"
              "- I send daily news at 8 AM and astronomy updates around 12 PM if there is any upcoming news about it.\n"
              "`/ph_news` To receive Philippines news updates.\n"
              "`/jp_news` To receive Japan news updates.",
        inline=False
    )

    embed.add_field(
        name="Bible Verse:",
        value="`/activate_bible_verse` - Activate a daily Bible Verse to send to a specific channel.\n"
              "- I send a daily Bible Verse every 7 AM GMT+8.\n\n"
              "`/random_bible_verse` - Receive a random Bible Verse.",
        inline=False
    )

    embed.add_field(
        name="Anime:",
        value="`/anisearch <anime title>` - Search for anime information.",
        inline=False
    )

    embed.add_field(
        name="Music:",
        value="`!play <song>` - Play a song.\n"
              "- To add a song, simply enter the same command.\n\n"
              "`!pause` - Pause a song.\n"
              "`!resume` - Resume a song.\n"
              "`!stop` - Stop a song.",
        inline=False
    )

    embed.add_field(
        name="Other Commands:",
        value="`!status` - Check my uptime.\n"
              "`!ping` - Check my latency.\n"
              "`!roll` - Roll a dice with a specified number of sides (default is 6).",
        inline=False
    )

    embed.add_field(
        name="Moderator:",
        value="`/send_a_message_to_user` - Send a message to a specific user.\n"
              "`/send_a_message_to_channel` - Send a message to a specific channel.\n"
              "`!serverinfo` - Get information about the server.\n"
              "`!userinfo` - Displays the ID, nickname, status, join date, and avatar of a specified user.\n"
              "`!clear` - Deletes a specified number of messages from the channel.\n"
              "`/feedback` - Send a feedback.",
        inline=False
    )

    embed.set_footer(text="Have a good day! 💗")

    await interaction.response.send_message(embed=embed)

    

@bot.tree.command(name="jp_news")
async def jp_news_command(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        logger.info(f"/jp_news is used by {interaction.user} in DMs")
        await interaction.response.defer(ephemeral=True)
        await fetch_and_send_news(interaction.user, jp_url_news)
    else:
        logger.info(f"/jp_news is used by {interaction.user} in {interaction.guild} for channel {interaction.channel.name}")
        await interaction.response.defer(ephemeral=True)
        await fetch_and_send_news(interaction.channel, jp_url_news)
    await interaction.followup.send("Japanese news has been sent to this channel.", ephemeral=True)


@bot.tree.command(name="ph_news")
async def ph_news_command(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        logger.info(f"/ph_news is used by {interaction.user} in DMs")
        await interaction.response.defer(ephemeral=True)
        await fetch_and_send_news(interaction.user, ph_url_news)
    else:
        logger.info(f"/ph_news is used by {interaction.user} in {interaction.guild} for channel {interaction.channel.name}")
        await interaction.response.defer(ephemeral=True)
        await fetch_and_send_news(interaction.channel, ph_url_news)
    await interaction.followup.send("Philippine news has been sent to this channel.", ephemeral=True)



async def fetch_and_send_news(channel: discord.abc.Messageable, url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        card_bodies = soup.find_all('div', class_='card__body')
        if card_bodies:
            message = ""
            for card in card_bodies[:6]:
                link = card.find('a', href=True)
                if link:
                    full_link = f"https://asia.nikkei.com{link['href']}"
                    message += f"{full_link}\n"

            await channel.send(f"\n{message}\n**Here is the latest news you asked for: **\n")
        else:
            logger.error("No news items found in the HTML.")
            await channel.send("Failed to find news items on the webpage.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error during news retrieval: {e}")
        await channel.send(f"Failed to retrieve the webpage. Error: {e}")
    except Exception as e:
        logger.error(f"Error during news processing: {e}")
        await channel.send(f"An error occurred while processing the news. Error: {e}")
        


@bot.tree.command(name="sendamessage")
async def send_message_to_channel(interaction: discord.Interaction, channel: discord.TextChannel, *, message: str):
    """
    Sends a message to a specified channel in the server.
    """
    logger.info(f"/sendamessage is used by {interaction.user} in {interaction.guild} for channel {channel.name} with message '{message}'")
    if channel:
        await channel.send(message)
        await interaction.response.send_message(f"Message sent to {channel.mention}")
    else:
        await interaction.response.send_message(f"Channel {channel.name} not found in the server.")

@bot.command()
async def set_status(ctx, status_type: str, *, activity_name: str):
    statuses = {
        'online': discord.Status.online,
        'idle': discord.Status.idle,
        'dnd': discord.Status.do_not_disturb,
        'offline': discord.Status.offline
    }

    activities = {
        'playing': discord.Game,
        'streaming': discord.Streaming,
        'listening': discord.Activity(type=discord.ActivityType.listening),
        'watching': discord.Activity(type=discord.ActivityType.watching)
    }

    status = statuses.get(status_type.lower(), discord.Status.online)
    activity = activities.get(activity_name.split()[0].lower(), discord.Game)(name=activity_name)

    await bot.change_presence(status=status, activity=activity)
    await ctx.send(f"Status changed to {status_type} with activity '{activity_name}'")


# Roll dice command
@bot.command()
async def roll(ctx, sides: int = 6):
    if isinstance(ctx.channel, discord.DMChannel):
        logger.info(f"!roll is used by {ctx.author} in DMs")
    else:
        logger.info(f"!roll is used by {ctx.author} in {ctx.guild.name} for channel {ctx.channel.name}")
    result = random.randint(1, sides)
    await ctx.send(f'Rolled a {sides}-sided dice: **{result}**')

# Command to check bot uptime
@bot.command()
async def status(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        logger.info(f"!status is used by {ctx.author} in DMs")
    else:
        logger.info(f"!status is used by {ctx.author} in {ctx.guild.name} for channel {ctx.channel.name}")
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours} hours, {minutes} minutes, {seconds} seconds"
    await ctx.send(f"I have been online for {uptime_str}.")

# Ping command
@bot.command()
async def ping(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        logger.info(f"!ping is used by {ctx.author} in DMs")
    else:
        logger.info(f"!ping is used by {ctx.author} in {ctx.guild.name} for channel {ctx.channel.name}")
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! My Latency is {latency}ms')

async def check_dm(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command cannot be used in DMs.")
        return True
    return False
    
# Server info command
@bot.command()
async def serverinfo(ctx):
    logger.info(f"!serverinfo is used by {ctx.author} in DMs")
    if await check_dm(ctx):
        return
    try:
        logger.info(f"!serverinfo is used by {ctx.author} in {ctx.guild.name} for channel {ctx.channel.name}")
        server = ctx.guild
        num_members = server.member_count
        num_channels = len(server.channels)
        server_name = server.name
        await ctx.send(f'Server name: {server_name}\nMembers: {num_members}\nChannels: {num_channels}')
    except Exception as e:
        logger.error(f"!serverinfo is used by {ctx.author} but error: {e}")

# User info command
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    logger.info(f"!userinfo is used by {ctx.author} in DMs")
    if await check_dm(ctx):
        return
    try:
        logger.info(f"!userinfo is used by {ctx.author} in {ctx.guild.name} for channel {ctx.channel.name}")
        if member is None:
            member = ctx.author
        embed = discord.Embed(title=f"{member.name}'s info", color=discord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="Status", value=member.status, inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"!userinfo is used by {ctx.author} but error: {e}")

# Clear messages command
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    logger.info(f"!clear is used by {ctx.author} in DMs")
    if await check_dm(ctx):
        return
    logger.info(f"!clear is used by {ctx.author} in {ctx.guild.name} for channel {ctx.channel.name}")
    """Clears a specified number of messages from the channel."""
    if amount <= 0:
        await ctx.send("Please provide a number greater than 0.", delete_after=5)
        return
    if amount > 100:
        await ctx.send("You cannot delete more than 100 messages at a time.", delete_after=5)
        return
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Cleared {amount} messages.", delete_after=5)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify the number of messages to clear.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please provide a valid number of messages.")
    else:
        await ctx.send("An error occurred while trying to clear messages.")
        logger.error(f"!clear is used by {ctx.author} but error: {error}")


@bot.tree.command(name='feedback')
async def feedback(interaction: discord.Interaction, feedback_text: str):
    logger.info(f"/feedback is used by {interaction.user}")
    try:
        user = await bot.fetch_user(YOUR_USER_ID)
        if user:
            await user.send(f'*Feedback from {interaction.user} ({interaction.user.id}):* **{feedback_text}**')
            await interaction.response.send_message('Thank you for your feedback!', ephemeral=True)
        else:
            await interaction.response.send_message('Unable to send feedback. Please try again later.', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'An error occurred: {e}', ephemeral=True)
        logger.error(f"/feedback is used by {interaction.user} but error: {e}")

        

@bot.tree.command(name='send_a_message_to_user')
async def send_a_message_to_user(interaction: discord.Interaction, user_id: str, message: str):
    logger.info(f"/send_a_message_to_user is used by {interaction.user} to send a message to {user_id}")
    try:
        user = await bot.fetch_user(int(user_id))
        if user:
            await user.send(message)
            await interaction.response.send_message(f'Message sent to user {user_id}.', ephemeral=True)
        else:
            await interaction.response.send_message('Unable to send message. User not found.', ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f'Failed to send message. HTTPException: {e}', ephemeral=True)
        logger.error(f"/send_a_message_to_user is used by {interaction.user} but error: {e}")
    except discord.Forbidden:
        await interaction.response.send_message('Unable to send message. Forbidden: Cannot send messages to this user.', ephemeral=True)
        logger.error(f"/send_a_message_to_user is used by {interaction.user} but error: Forbidden")
    except Exception as e:
        await interaction.response.send_message(f'An error occurred: {e}', ephemeral=True)
        logger.error(f"/send_a_message_to_user is used by {interaction.user} but error: {e}")


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    await bot.change_presence(
        status=discord.Status.do_not_disturb, 
        activity=discord.Activity(type=discord.ActivityType.listening, name="BRODYAGA FUNK")
    )
    
    active_all_announcement_channels = load_active_channels(ANNOUNCEMENT_CHANNEL_FILE)
    if active_all_announcement_channels:
        if not send_astronomy_announcement.is_running():
            send_astronomy_announcement.start()
        if not send_news.is_running():
            send_news.start()
        print(f"All announcements activated in {len(active_all_announcement_channels)} channel(s)")

    active_bible_verse_channels = load_active_channels(BIBLE_VERSE_CHANNEL_FILE)
    if active_bible_verse_channels:
        if not send_daily_verse.is_running():
            send_daily_verse.start()
        print(f"Bible verse announcements activated in {len(active_bible_verse_channels)} channel(s)")
   
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Register the music commands
    music_module.setup(bot)
    
# Run the bot
bot.run(TOKEN)
