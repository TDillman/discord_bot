import discord
import logging
import datetime
import logging.handlers
import bot_secrets
import bot_config
import random
import os
import socket

from discord import app_commands
from blizzardapi import BlizzardApi
from youtube_api import YouTubeDataAPI
from dataclasses import dataclass, field
from logging.handlers import SysLogHandler

class ContextFilter(logging.Filter):
    hostname = socket.gethostname()
    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True

syslog = SysLogHandler(
    address=(bot_secrets.papertrail_url,
             bot_secrets.papertrail_port)
)
syslog.addFilter(ContextFilter())
format = '%(asctime)s %(hostname)s beymax: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.INFO)

MY_GUILD = discord.Object(id=bot_config.GUILD_ID)
might_logo = 'https://cdn.discordapp.com/attachments/676183284123828236/679823287521771602/mightcoloredfinishedsmall.png'
error_icon_url = 'https://cdn0.iconfinder.com/data/icons/shift-interfaces/32/Error-512.png'
wow_url = "https://owen-wilson-wow-api.herokuapp.com/wows/random"

kat_gif_list = bot_config.kat_gif_list

enchant_map = bot_config.enchant_map
wow_spec_dict = bot_config.wow_spec_dict

#YouTube API
yt = YouTubeDataAPI(bot_secrets.YT_DATA_API)
#Blizzard API
api_client = BlizzardApi(bot_secrets.BLIZZARD_CLIENT_ID, bot_secrets.BLIZZARD_SECRET_ID)

death_knight_role = bot_config.class_role_dict['Death Knight']
demon_hunter_role = bot_config.class_role_dict['Demon Hunter']
druid_role = bot_config.class_role_dict['Druid']
evoker_role = bot_config.class_role_dict['Evoker']
hunter_role = bot_config.class_role_dict['Hunter']
mage_role = bot_config.class_role_dict['Mage']
monk_role = bot_config.class_role_dict['Monk']
paladin_role = bot_config.class_role_dict['Paladin']
priest_role = bot_config.class_role_dict['Priest']
rogue_role = bot_config.class_role_dict['Rogue']
shaman_role = bot_config.class_role_dict['Shaman']
warlock_role = bot_config.class_role_dict['Warlock']
warrior_role = bot_config.class_role_dict['Warrior']

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents.all()):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.overwatch_role = bot_config.overwatch_role
        self.movie_role = bot_config.movie_role
        self.m_plus_role = bot_config.m_plus_role
        self.pvp_role = bot_config.pvp_role
        self.colorado_role = bot_config.colorado_role
        self.mightcon_role = bot_config.mightcon_role
        self.ready_to_raid_role = bot_config.ready_to_raid_role
        self.guild_member_role = bot_config.guild_member_role
        self.raid_friends_role = bot_config.raid_friends_role

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.all()
client = MyClient(intents=intents)

async def is_blacklisted(interaction: discord.Interaction):
    if interaction.user.id in bot_config.blacklisted_users:
        return False #blacklisted. Seems backwards, but it's not.
        await interaction.response.send_message(
            'You are blacklisted from using commands.',
            ephemeral=True
        )
        logger.info(f'{interaction.user.name} ({interaction.user.id}) '
                    f'is blacklisted from using commands.')
    return True #not blacklisted

# The log_command decorator logs the user's command usage
def log_command(func):
    async def wrapper(interaction: discord.Interaction, **kwargs):
        logger.info(f'User: {interaction.user.name} ({interaction.user.id})\t'
                    f'Command: {func.__name__}\t'
                    f'Options: {kwargs}\t'
                    f'Channel: {interaction.channel.name}')
        return await func(interaction, **kwargs)
    return wrapper

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('with fire. Type /help!'))
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')

# The rename decorator allows us to change the display of the parameter on Discord.
@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# This context menu command only works on members
@client.tree.context_menu(name='Show Member Info')
#@log_command
@app_commands.check(is_blacklisted)
async def show_member_info(interaction: discord.Interaction, member: discord.Member):
    try:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        tdelta = now - member.joined_at
        if tdelta.days == 0:
            joined_at = f'That\'s {tdelta.seconds // 3600} hours, ' \
                        f'{(tdelta.seconds // 60) % 60} minutes, ' \
                        f'{tdelta.seconds % 60} seconds ago'
        else:
            joined_at = f'That\'s {tdelta.days} days, ' \
                        f'{tdelta.seconds // 3600} hours, ' \
                        f'{(tdelta.seconds // 60) % 60} minutes, ' \
                        f'{tdelta.seconds % 60} seconds ago'
        if len([role.mention for role in member.roles[1:]]) == 0:
            roles = 'None'
        else:
            roles = '\n'.join([role.mention for role in member.roles[1:]])

        embed = discord.Embed(title=f'Member Info for {member}',
                              color=member.color
                              )
        embed.add_field(name=f'{member.display_name} joined on '
                             f'{discord.utils.format_dt(member.joined_at)}',
                        value=joined_at)
        embed.add_field(name="Roles", value=roles,
                        inline=False
                        )
        embed.set_author(name=member.display_name,
                         icon_url=member.avatar
                         )
        logger.info(f'User: {interaction.user.name} ({interaction.user.id})\t'
                    f'Command: {show_member_info.name}\t'
                    f'Options: {member} ({member.id})\t'
                    f'Channel: {interaction.channel.name}')
        await interaction.response.send_message(embed=embed)
    except Exception:
        logger.error("Exception occurred", exc_info=True)

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def spooky(interaction: discord.Interaction):
    """There's always money in the banana stand!"""
    await interaction.response.send_message(
        'https://tenor.com/view/arrested-development-claw-hand-juice-box-laughing-evil-laugh-gif-5335530'
    )

@client.tree.command()
#@log_command
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def scrumpy(interaction: discord.Interaction):
    """Just his opinion"""
    await interaction.response.send_message('Thinks your bags are awful')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def golfclap(interaction: discord.Interaction):
    """Well played"""
    await interaction.response.send_message(
        'https://tenor.com/view/charlie-sheen-emilio-estevez-golf-clap-men-at-work-gif-7577611'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def whatever(interaction: discord.Interaction):
    """Whatever man"""
    await interaction.response.send_message(
        'https://media.discordapp.net/attachments/765619338337058827/802299499908563024/whatever.gif'
    )

@client.tree.command()
#@log_command
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def cool(interaction: discord.Interaction):
    """Peralta says"""
    await interaction.response.send_message(
        'https://tenor.com/view/andy-samberg-brooklyn99-jake-peralta-cool-gif-12063970'
    )

@client.tree.command()
#@log_command
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def myst(interaction: discord.Interaction):
    """Is it though?"""
    await interaction.response.send_message(
        'https://tenor.com/view/is-it-though-thor-smile-gif-13334930'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def myst2(interaction: discord.Interaction):
    """I mean..."""
    await interaction.response.send_message(
        'https://tenor.com/view/shrug-what-huh-will-smith-i-mean-gif-15916247'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def beylock(interaction: discord.Interaction):
    """I love this song"""
    await interaction.response.send_message('https://imgur.com/a/xux2u6p')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def happybirthday(interaction: discord.Interaction):
    """Party at Kat's place!"""
    #check if today is April 21st
    if datetime.datetime.today().month == 4 and datetime.datetime.today().day == 21:
        await interaction.response.send_message(
            'https://tenor.com/view/we-dont-do-that-here-black-panther-tchalla-bruce-gif-16558003',
            ephemeral=True
        )
    else:
        await interaction.response.send_message('https://giphy.com/gifs/i8htPQwChFOVcpnImq')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def magic(interaction: discord.Interaction):
    """Don't ask how"""
    await interaction.response.send_message(
        'https://media.discordapp.net/attachments/676183284123828236/761438362720272394/Kat_Confetti.gif'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def wat(interaction: discord.Interaction):
    """wat"""
    await interaction.response.send_message('https://imgur.com/a/PnB5eFk')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def thisisfine(interaction: discord.Interaction):
    """I'll probably survive"""
    await interaction.response.send_message('https://imgur.com/a/uDAO5In')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def suckit(interaction: discord.Interaction):
    """Suck it!"""
    await interaction.response.send_message('https://imgur.com/Fy6RhWI')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def risn(interaction: discord.Interaction):
    """K"""
    await interaction.response.send_message(
        'https://www.circlek.com/themes/custom/circlek/images/logos/logo-full-color-rgb.jpg'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def hakkd(interaction: discord.Interaction):
    """Don't let it happen again"""
    await interaction.response.send_message(
        'https://tenor.com/view/mad-monster-dont-let-it-happen-again-gif-14024298'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def wtf(interaction: discord.Interaction):
    """What the fuck?"""
    await interaction.response.send_message('https://giphy.com/gifs/what-the-fuck-wtf-ukGm72ZLZvYfS')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def rain(interaction: discord.Interaction):
    """Lil bih"""
    await interaction.response.send_message(
        'https://cdn.discordapp.com/attachments/676183384061378571/856642945481310228/unknown.png'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def daddychill(interaction: discord.Interaction):
    """What the hell is even that?!"""
    await interaction.response.send_message('https://tenor.com/view/what-the-hell-is-even-gif-20535402')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def rightright(interaction: discord.Interaction):
    """From a show about nothing"""
    await interaction.response.send_message(
        'https://tenor.com/view/seinfeld-jerry-seinfeld-oh-right-agree-gif-4436696'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def hydrate(interaction: discord.Interaction):
    """Hydration is important"""
    await interaction.response.send_message('https://tenor.com/view/water-smile-drink-water-gif-13518129')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def spoon(interaction: discord.Interaction):
    """My spoon is too big"""
    await interaction.response.send_message(
        'https://media.discordapp.net/attachments/503025662546935809/747820543918735370/'
        'A_little_party_never_killed_no_body_gif.gif'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def imdumb(interaction: discord.Interaction):
    """I'm dumb"""
    await interaction.response.send_message(
        'https://tenor.com/view/winston-schmidt-max-greenfield-new-girl-gif-15041554'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def aster(interaction: discord.Interaction):
    """That face. That goddamn face."""
    await interaction.response.send_message(
        'https://cdn.discordapp.com/attachments/938971434246631435/940347663533084732/Chaotic_Aster.png'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def pig(interaction: discord.Interaction):
    """This little piggy..."""
    await interaction.response.send_message('https://tenor.com/view/pig-cute-gif-21946909')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def listen(interaction: discord.Interaction):
    """listen here"""
    await interaction.response.send_message(
        'https://i.pinimg.com/originals/ef/a6/48/efa648c67f3cb05287ded99612af130f.png'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def nyrixx(interaction: discord.Interaction):
    """Never sneak up on a Schrute."""
    await interaction.response.send_message('https://tenor.com/view/office-dwight-schrute-surprised-gif-14541388')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def yzu(interaction: discord.Interaction):
    """eli5"""
    await interaction.response.send_message(
        'https://tenor.com/view/confused-the-office-michael-scott-steve-carell-explain-this-to-me-like-im-five-gif-4527435'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def ben(interaction: discord.Interaction):
    """Finger"""
    await interaction.response.send_message(
        'https://media.discordapp.net/attachments/199644505845137408/798327813479727114/2015-02-10.gif'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def cheat(interaction: discord.Interaction):
    """Get excited"""
    await interaction.response.send_message('https://tenor.com/view/the-office-space-umm-wow-ok-then-gif-15829379')

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def kat(interaction: discord.Interaction):
    """Squints"""
    kat_gif = random.choice(kat_gif_list)
    await interaction.response.send_message(kat_gif)

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def cheers(interaction: discord.Interaction):
    """Cheers mate"""
    await interaction.response.send_message(
        'https://cdn.discordapp.com/attachments/775444197468667904/1042974872407646218/trim.9B102A43-2EA1-4846-847C-25468EB6804C.gif'
    )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def specimen(interaction: discord.Interaction):
    """Nope"""
    await interaction.response.send_message("https://tenor.com/view/run-running-rumning-away-gif-26050933")

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
@app_commands.describe(search='Search criteria')
async def jams(interaction: discord.Interaction, search: str):
    """Search YouTube for a video!"""
    results = yt.search(search, max_results=5, order='relevance')
    #check if today is April First
    if datetime.datetime.today().month == 4 and datetime.datetime.today().day == 1:
        await interaction.response.send_message("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    elif len(results) == 0:
        await interaction.response.send_message(f"No results for {search}")
    else:
        youtube_video_url = f"https://www.youtube.com/watch?v={results[0]['video_id']}"
        await interaction.response.send_message(youtube_video_url)

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.describe(mock='Mocking text')
async def mock(interaction: discord.Interaction, mock: str):
    """QuIt MaKiNg FuN oF mE"""
    # Check if today is April Fool's day
    if datetime.datetime.today().month == 4 and datetime.datetime.today().day == 1:
        mocking_text = "I'm A bIg DuMb SmElLy IdIoT"
    else:
        mocking_text = (''.join([letter.lower()
                                 if index % 2 == 0 else letter.upper()
                                 for index, letter in enumerate(mock)]))
    await interaction.response.send_message(mocking_text)

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
async def mightcon2(interaction: discord.Interaction):
    """Mightcon 2: Las Vegas memories"""
    # Randomly selects an image to send to Discord
    path = "/home/ubuntu/beymax/mightcon2_pics"
    files = os.listdir(path)
    image = random.choice(files)
    embed = discord.Embed(title="Mightcon 2: Las Vegas",
                          description="Random memory from Mightcon 2!",
                          color=0x0000ff,
                          url="https://imgur.com/a/iJ3axyF"
                          )
    file = discord.File(f"{path}/{image}",
                        filename=image
                        )
    embed.set_image(url=f"attachment://{image}")
    await interaction.response.send_message(embed=embed, file=file)

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def sixtynine(interaction: discord.Interaction):
    """Nice"""
    await interaction.response.send_message(
        "https://cdn.discordapp.com/attachments/1039705067235835934/1043215596181016666/IMG_3549.jpg"
    )
    

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def token(interaction: discord.Interaction):
    """
    Returns an embed with the current WoW token price in gold
    """
    try:
        token_object = api_client.wow.game_data.get_token_index("us", "en_US")
        print(token_object)

        embed = discord.Embed(title='WoW Token')
        # check if today is April First
        if datetime.datetime.today().month == 4 and datetime.datetime.today().day == 1:
            embed.add_field(name='Current Price',
                            value='696969 gold lol')
        else:
            embed.add_field(name='Current Price',
                            value=f'{token_object["price"] / 10000:,.0f} gold'
                            )
        embed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/676183284123828236/679823287521771602/mightcolored'
                'finishedsmall.png')
        await interaction.response.send_message(embed=embed)
    except Exception:
        await interaction.response.send_message(
            "Something went wrong. Please try again later."
        )

@client.tree.command()
#@log_command
#@handle_errors
@app_commands.check(is_blacklisted)
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def status(interaction: discord.Interaction):
    """Status of the Arygos server"""
    try:
        server_object = api_client.wow.game_data.get_connected_realm("us", "en_US", 99)

        @dataclass
        class Server:
            status: str = server_object['status']['name']
            population: str = server_object['population']['name']
            has_queue: bool = server_object['has_queue']
            region: str = server_object['realms'][0]['region']['name']
            country: str = server_object['realms'][0]['category']
            timezone: str = server_object['realms'][0]['timezone']
            connections: list = field(
                default_factory=lambda: [server_object['realms'][x]['name']
                                         for x in range(len(server_object['realms']))]
            )
            name: str = 'Arygos'

        server = Server()

        if server.status == "Up":
            status_color = 0x00ff00  # Green for up
        else:
            status_color = 0xff0000  # Red for down

        server_string = ', '.join(str(name) for name in server.connections)

        embed = discord.Embed(title='Arygos', color=status_color)
        embed.add_field(name='Current Status',
                        value=f'Server is currently {server.status}',
                        inline=True
                        )
        if server.population == 'Offline':
            embed.add_field(name='Current Population',
                            value=f'This server is currently {server.population}'
                            )
        else:
            embed.add_field(name='Current Population',
                            value=f'This is a {server.population} pop server',
                            inline=True
                            )
        embed.add_field(name='Connected Realms',
                        value=server_string,
                        inline=False
                        )
        if server.has_queue:
            embed.add_field(name='Queue Active',
                            value='Server has a login queue'
                            )
        embed.add_field(name="Timezone",
                        value=server.timezone,
                        inline=True
                        )
        embed.set_thumbnail(url=might_logo)
        await interaction.response.send_message(embed=embed)
    except Exception:
        logger.error("Exception occurred with server status", exc_info=True)
        await interaction.response.send_message(
            "Something went wrong. Please try again later."
        )

# Get the names of all the commands in this file to make a help command
command_list: list = [f'/{x.name}' for x in client.tree.walk_commands()]
command_list.sort()
middle_index = len(command_list)//2
help_string1: str = '\n'.join(str(name) for name in command_list[:middle_index])
help_string2: str = '\n'.join(str(name) for name in command_list[middle_index:])

@client.tree.command()
#@log_command
#@handle_errors
async def help(interaction: discord.Interaction) -> str:
    """List out the bot commands"""
    embed = discord.Embed(title='Bot Commands')
    embed.add_field(name='User Commands',
                    value=help_string1,
                    inline=True)
    embed.add_field(name='User Commands',
                    value=help_string2,
                    inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

client.run(bot_secrets.DISCORD_API, log_handler=None)
