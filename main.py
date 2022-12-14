import discord
import logging
import asyncio
import datetime
import logging.handlers
import bot_secrets
import bot_config
import gspread
import random
import requests
import json
import os

from discord import app_commands, ui, Interaction
from discord.app_commands import AppCommandError
from discord.ui import Button, View
from blizzardapi import BlizzardApi
from youtube_api import YouTubeDataAPI
from dataclasses import dataclass, field

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(
    filename='python.log',
    encoding='utf-8',
    maxBytes=5 * 1024 * 1024,  # 5 MiB
    backupCount=15,  # Rotate through 15 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
# Google Sheets API
gc = gspread.service_account()

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

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('with fire. Type /help!'))
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.error
async def on_app_command_error(interaction: Interaction, error: AppCommandError):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        embed = discord.Embed(title='Error')
        embed.add_field(name='Command on Cooldown', value=f'That command is on cooldown for {error.retry_after:.2f} more seconds.')
        embed.set_thumbnail(url=error_icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    if isinstance(error, discord.app_commands.MissingAnyRole):
        embed = discord.Embed(title='Error')
        embed.add_field(name='Permission Missing', value=f"You're missing a permission to do that.")
        embed.add_field(name='Error', value=error, inline=False)
        embed.set_thumbnail(url=error_icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ClassSelect(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Death Knight"),
            discord.SelectOption(label="Demon Hunter"),
            discord.SelectOption(label="Druid"),
            discord.SelectOption(label="Evoker"),
            discord.SelectOption(label="Hunter"),
            discord.SelectOption(label="Mage"),
            discord.SelectOption(label="Monk"),
            discord.SelectOption(label="Paladin"),
            discord.SelectOption(label="Priest"),
            discord.SelectOption(label="Rogue"),
            discord.SelectOption(label="Shaman"),
            discord.SelectOption(label="Warlock"),
            discord.SelectOption(label="Warrior")
            ]
        super().__init__(placeholder="Select an option",max_values=13,min_values=1,options=options)
    async def callback(self, interaction: discord.Interaction):
        if 676185937323229189 not in interaction.user.roles:
            for player_class in self.values:
                class_string = ', '.join(self.values)
                if bot_config.class_role_dict[player_class] in interaction.user.roles:
                    await interaction.user.remove_roles(discord.Object(bot_config.class_role_dict[player_class]))
                else: await interaction.user.add_roles(discord.Object(bot_config.class_role_dict[player_class]))
            await interaction.response.send_message(f'You have selected {class_string}. '
                                                    f'You now have access to these class channels.', ephemeral=True)
        else: await interaction.response.send_message(f'You need to have the Guild Member role to select classes.', ephemeral=True)

class ClassSelectView(discord.ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(ClassSelect())

@client.tree.command()
async def class_role_menu(interaction: discord.Interaction):
    await interaction.response.send_message("Select the class channels you want access to!",view=ClassSelectView())

@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')

@client.tree.command()
async def r2rlist(interaction: discord.Interaction):
    """Lists all the people who are ready to raid!"""
    guild = client.get_guild(bot_config.GUILD_ID)
    r2r_role = guild.get_role(bot_config.ready_to_raid_role)
    r2r_list = [member.display_name for member in r2r_role.members]
    r2r_list = ', '.join(r2r_list)
    await interaction.response.send_message(f'{r2r_list}', ephemeral=True)

# The rename decorator allows us to change the display of the parameter on Discord.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# This context menu command only works on members
@client.tree.context_menu(name='Show Member Info')
async def show_member_info(interaction: discord.Interaction, member: discord.Member):
    try:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        tdelta = now - member.joined_at
        if tdelta.days == 0:
            joined_at = f'That\'s {tdelta.seconds // 3600} hours, {(tdelta.seconds // 60) % 60} minutes, {tdelta.seconds % 60} seconds ago'
        else:
            joined_at = f'That\'s {tdelta.days} days, {tdelta.seconds // 3600} hours, {(tdelta.seconds // 60) % 60} minutes, {tdelta.seconds % 60} seconds ago'
        if len([role.mention for role in member.roles[1:]]) == 0:
            roles = 'None'
        else:
            roles = '\n'.join([role.mention for role in member.roles[1:]])

        print(discord.utils.get(member.activities, type=discord.ActivityType.custom))

        embed = discord.Embed(title=f'Member Info for {member}', color=member.color)
        #embed.add_field(name='Activity', value=f'{activity}', inline=False)
        embed.add_field(name=f'{member.display_name} joined on {discord.utils.format_dt(member.joined_at)}',
                        value=joined_at)
        embed.add_field(name="Roles", value=roles, inline=False)
        embed.set_author(name=member.display_name, icon_url=member.avatar)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def spooky(interaction: discord.Interaction):
    """There's always money in the banana stand!"""
    await interaction.response.send_message('https://tenor.com/view/arrested-development-claw-hand-juice-box-laughing-evil-laugh-gif-5335530')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def scrumpy(interaction: discord.Interaction):
    """Just his opinion"""
    await interaction.response.send_message('Thinks your bags are awful')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def golfclap(interaction: discord.Interaction):
    """Well played"""
    await interaction.response.send_message('https://tenor.com/view/charlie-sheen-emilio-estevez-golf-clap-men-at-work-gif-7577611')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def whatever(interaction: discord.Interaction):
    """Whatever man"""
    await interaction.response.send_message('https://media.discordapp.net/attachments/765619338337058827/802299499908563024/whatever.gif')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def cool(interaction: discord.Interaction):
    """Peralta says"""
    await interaction.response.send_message('https://tenor.com/view/andy-samberg-brooklyn99-jake-peralta-cool-gif-12063970')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def myst(interaction: discord.Interaction):
    """Is it though?"""
    await interaction.response.send_message('https://tenor.com/view/is-it-though-thor-smile-gif-13334930')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def myst2(interaction: discord.Interaction):
    """I mean..."""
    await interaction.response.send_message('https://tenor.com/view/shrug-what-huh-will-smith-i-mean-gif-15916247')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def beylock(interaction: discord.Interaction):
    """I love this song"""
    await interaction.response.send_message('https://imgur.com/a/xux2u6p')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def happybirthday(interaction: discord.Interaction):
    """Party at Kat's place!"""
    await interaction.response.send_message('https://giphy.com/gifs/i8htPQwChFOVcpnImq')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def magic(interaction: discord.Interaction):
    """Don't ask how"""
    await interaction.response.send_message('https://media.discordapp.net/attachments/676183284123828236/761438362720272394/Kat_Confetti.gif')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def lynkz(interaction: discord.Interaction):
    """Who is that?"""
    await interaction.response.send_message('https://media.discordapp.net/attachments/676183284123828236/899091363046522910/unknown.png')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def candercane(interaction: discord.Interaction):
    """This child is furious"""
    await interaction.response.send_message('https://giphy.com/gifs/angry-mad-anger-l1J9u3TZfpmeDLkD6')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def wat(interaction: discord.Interaction):
    """wat"""
    await interaction.response.send_message('https://imgur.com/a/PnB5eFk')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def thisisfine(interaction: discord.Interaction):
    """I'll probably survive"""
    await interaction.response.send_message('https://imgur.com/a/uDAO5In')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def pirate(interaction: discord.Interaction):
    """Pirate shimmy!"""
    await interaction.response.send_message('https://imgur.com/a/TDot4Ba')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def suckit(interaction: discord.Interaction):
    """Suck it!"""
    await interaction.response.send_message('https://imgur.com/Fy6RhWI')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def risn(interaction: discord.Interaction):
    """K"""
    await interaction.response.send_message('https://www.circlek.com/themes/custom/circlek/images/logos/logo-full-color-rgb.jpg')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def hakkd(interaction: discord.Interaction):
    """Don't let it happen again"""
    await interaction.response.send_message('https://tenor.com/view/mad-monster-dont-let-it-happen-again-gif-14024298')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def wtf(interaction: discord.Interaction):
    """What the fuck?"""
    await interaction.response.send_message('https://giphy.com/gifs/what-the-fuck-wtf-ukGm72ZLZvYfS')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def rain(interaction: discord.Interaction):
    """Lil bih"""
    await interaction.response.send_message('https://cdn.discordapp.com/attachments/676183384061378571/856642945481310228/unknown.png')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def imout(interaction: discord.Interaction):
    """Peace out"""
    await interaction.response.send_message('https://media.discordapp.net/attachments/676183306924064768/866005404839837706/sylvanas.gif')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def daddychill(interaction: discord.Interaction):
    """What the hell is even that?!"""
    await interaction.response.send_message('https://tenor.com/view/what-the-hell-is-even-gif-20535402')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def guacdrop(interaction: discord.Interaction):
    """Not the guacamole!"""
    await interaction.response.send_message('https://media.discordapp.net/attachments/917450971569877044/917465265036488704/20211105_213516.jpg')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def rightright(interaction: discord.Interaction):
    """From a show about nothing"""
    await interaction.response.send_message('https://tenor.com/view/seinfeld-jerry-seinfeld-oh-right-agree-gif-4436696')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def shit(interaction: discord.Interaction):
    """Get your poop in a group"""
    await interaction.response.send_message('https://giphy.com/gifs/get-well-then-woTdBa435yy6A')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def hydrate(interaction: discord.Interaction):
    """Hydration is important"""
    await interaction.response.send_message('https://tenor.com/view/water-smile-drink-water-gif-13518129')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def spoon(interaction: discord.Interaction):
    """My spoon is too big"""
    await interaction.response.send_message('https://media.discordapp.net/attachments/503025662546935809/747820543918735370/A_little_party_never_killed_no_body_gif.gif')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def imdumb(interaction: discord.Interaction):
    """I'm dumb"""
    await interaction.response.send_message('https://tenor.com/view/winston-schmidt-max-greenfield-new-girl-gif-15041554')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def aster(interaction: discord.Interaction):
    """That face. That goddamn face."""
    await interaction.response.send_message('https://cdn.discordapp.com/attachments/938971434246631435/940347663533084732/Chaotic_Aster.png')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def drew(interaction: discord.Interaction):
    """Cold. Dead. Lifeless."""
    await interaction.response.send_message('https://tenor.com/view/sparkly-eyes-joy-happy-anime-hug-gif-15852045')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def pig(interaction: discord.Interaction):
    """This little piggy..."""
    await interaction.response.send_message('https://tenor.com/view/pig-cute-gif-21946909')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def listen(interaction: discord.Interaction):
    """listen here"""
    await interaction.response.send_message('https://i.pinimg.com/originals/ef/a6/48/efa648c67f3cb05287ded99612af130f.png')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def nyrixx(interaction: discord.Interaction):
    """Never sneak up on a Schrute."""
    await interaction.response.send_message('https://tenor.com/view/office-dwight-schrute-surprised-gif-14541388')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def yzu(interaction: discord.Interaction):
    """eli5"""
    await interaction.response.send_message('https://tenor.com/view/confused-the-office-michael-scott-steve-carell-explain-this-to-me-like-im-five-gif-4527435')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def ben(interaction: discord.Interaction):
    """Finger"""
    await interaction.response.send_message('https://media.discordapp.net/attachments/199644505845137408/798327813479727114/2015-02-10.gif')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def cheat(interaction: discord.Interaction):
    """Get excited"""
    await interaction.response.send_message('https://tenor.com/view/the-office-space-umm-wow-ok-then-gif-15829379')

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def kat(interaction: discord.Interaction):
    """Squints"""
    kat_gif = random.choice(kat_gif_list)
    await interaction.response.send_message(kat_gif)

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def cheers(interaction: discord.Interaction):
    """Cheers mate"""
    await interaction.response.send_message("https://cdn.discordapp.com/attachments/775444197468667904/1042974872407646218/trim.9B102A43-2EA1-4846-847C-25468EB6804C.gif")

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def dontdothat(interaction: discord.Interaction):
    """Don't do that"""
    await interaction.response.send_message("https://imgur.com/a/xEKQA8H")

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def specimen(interaction: discord.Interaction):
    """Nope"""
    await interaction.response.send_message("https://tenor.com/view/run-running-rumning-away-gif-26050933")

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def wow(interaction: discord.Interaction):
    """Wow"""
    response = requests.get(wow_url)
    if response.status_code == 200:
        movie_object = json.loads(requests.get(wow_url).content)
        title = movie_object[0]["movie"]
        wow_vid = movie_object[0]["video"]["360p"]
        timestamp = movie_object[0]["timestamp"]
        character = movie_object[0]["character"]
        year = movie_object[0]["year"]
        current_wow = movie_object[0]["current_wow_in_movie"]
        total_wows = movie_object[0]["total_wows_in_movie"]
        director = movie_object[0]["director"]
        full_line = movie_object[0]["full_line"]
        await interaction.response.send_message(f"{title} ({year}), directed by {director}\n"
                       f"At {timestamp}, {character}: Wow number {current_wow} out of {total_wows} total\n"
                       f"{wow_vid}\n"
                       f"\"{full_line}\"")
    else:
        await interaction.response.send_message("Can't communicate with API. Sorry :(")

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
@app_commands.describe(search='Search criteria')
async def jams(interaction: discord.Interaction, search: str):
    """Search YouTube for a video!"""
    results = yt.search(search, max_results=5, order='relevance')
    if len(results) == 0:
        await interaction.response.send_message(f"No results for {search}")
    else:
        youtube_video_url = f"https://www.youtube.com/watch?v={results[0]['video_id']}"
        await interaction.response.send_message(youtube_video_url)

@client.tree.command()
@app_commands.describe(mock='Mocking text')
async def mock(interaction: discord.Interaction, mock: str):
    """QuIt MaKiNg FuN oF mE"""
    mocking_text = (''.join([letter.lower() if index % 2 == 0 else letter.upper() for index, letter in enumerate(mock)]))
    await interaction.response.send_message(mocking_text)

@client.tree.command()
async def mightcon2(interaction: discord.Interaction):
    """Mightcon 2: Las Vegas memories"""
    # Randomly selects an image to send to Discord
    path = "/home/ubuntu/beymax/mightcon2_pics"
    files = os.listdir(path)
    image = random.choice(files)
    embed = discord.Embed(title="Mightcon 2: Las Vegas", description="Random memory from Mightcon 2!",
                          color=0x0000ff, url="https://imgur.com/a/iJ3axyF")
    file = discord.File(f"{path}/{image}", filename=image)
    embed.set_image(url=f"attachment://{image}")
    await interaction.response.send_message(embed=embed, file=file)

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def sixtynine(interaction: discord.Interaction):
    """Nice"""
    await interaction.response.send_message("https://cdn.discordapp.com/attachments/1039705067235835934/1043215596181016666/IMG_3549.jpg")

@client.tree.command()
async def pick(interaction: discord.Interaction):
    """What should I play in Dragonflight?"""
    # Select random class from wow_spec_dict
    wow_class = random.choice(list(wow_spec_dict.keys()))

    # Select random spec from wow_spec_dict
    wow_spec = random.choice(list(wow_spec_dict[wow_class].keys()))

    color = wow_spec_dict[wow_class][wow_spec][0]
    spec_type = wow_spec_dict[wow_class][wow_spec][1]
    description = wow_spec_dict[wow_class][wow_spec][2]
    icon = wow_spec_dict[wow_class][wow_spec][3]

    embed = discord.Embed(title=f"You should play {wow_spec} {wow_class} ({spec_type})", color=color,
                          description=description)
    file = discord.File(f'./wow_icons/{icon}', filename=icon)
    embed.set_thumbnail(url=f'attachment://{icon}')
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)

    await interaction.response.send_message(file=file, embed=embed)

movie_worksheet = gc.open('Beyplex').get_worksheet(0)
@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def movie(interaction: discord.Interaction):
    try:
        """Get a random movie from Beyplex"""

        movie_list_length = range(len(movie_worksheet.col_values(1)))
        movie_index_pick = random.choice(movie_list_length)
        movie_data = movie_worksheet.row_values(movie_index_pick)
        movie_name = movie_data[0]
        movie_rating = movie_data[1]
        movie_release = movie_data[2]
        movie_description = movie_data[3]
        movie_tagline = movie_data[4]
        movie_audience_rating = movie_data[5]
        movie_duration = movie_data[6]
        movie_genres = movie_data[7]
        movie_actors = movie_data[8]

        embed = discord.Embed(title=f'{movie_name} ({movie_rating})\nRuntime: {movie_duration}', description=movie_tagline, color=0x00ff00)
        embed.add_field(name='Description', value=movie_description, inline=False)
        embed.add_field(name='Genres', value=movie_genres, inline=False)
        embed.add_field(name='Actors', value=movie_actors, inline=False)
        embed.add_field(name='Audience Rating', value=movie_audience_rating, inline=True)
        embed.add_field(name='Release Date', value=movie_release, inline=True)
        embed.set_footer(text=f'Movie {movie_index_pick} of {len(movie_worksheet.col_values(1))}')

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        await interaction.response.send_message("Something went wrong. Sorry :(")

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def token(interaction: discord.Interaction):
    """
    Returns an embed with the current WoW token price in gold
    """
    try:
        token_object = api_client.wow.game_data.get_token_index("us", "en_US")
        print(token_object)

        embed = discord.Embed(title='WoW Token')
        embed.add_field(name='Current Price', value=f'{token_object["price"] / 10000:,.0f} gold')
        embed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/676183284123828236/679823287521771602/mightcolored'
                'finishedsmall.png')
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        await interaction.response.send_message("Something went wrong. Please try again later.")

@client.tree.command()
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
            connections: list = field(default_factory=lambda: [server_object['realms'][x]['name'] for x in
                                                               range(len(server_object['realms']))])
            name: str = 'Arygos'

        server = Server()

        if server.status == "Up":
            status_color = 0x00ff00  # Green for up
        else:
            status_color = 0xff0000  # Red for down

        server_string = ', '.join(str(name) for name in server.connections)

        embed = discord.Embed(title='Arygos', color=status_color)
        embed.add_field(name='Current Status', value=f'Server is currently {server.status}', inline=True)
        if server.population == 'Offline':
            embed.add_field(name='Current Population', value=f'This server is currently {server.population}')
        else:
            embed.add_field(name='Current Population', value=f'This is a {server.population} pop server', inline=True)
        embed.add_field(name='Connected Realms', value=server_string, inline=False)
        if server.has_queue:
            embed.add_field(name='Queue Active', value='Server has a login queue')
        embed.add_field(name="Timezone", value=server.timezone, inline=True)
        embed.set_thumbnail(url=might_logo)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        await interaction.response.send_message("Something went wrong. Please try again later.")

raid_worksheet = gc.open('Raid Requirements').get_worksheet(1)
@client.tree.command(description="Checks a user's character for raid readiness")
@discord.app_commands.checks.has_any_role("GM", "Assistant GM", "Guild Officer", "Guild Leader", "Guild Member")
@app_commands.describe(character_name='character name')
@app_commands.describe(character_server='server name')
async def r2r(interaction: discord.Interaction, character_name: str, character_server: str = "Arygos"):
    """
    Returns an embed with the specified character's R2R status
    """

    try:
        min_ilvl: int = int(raid_worksheet.col_values(1)[0])
        enchants_list: list = raid_worksheet.col_values(9)[1:]
    except:
        logging.error("Exception occurred", exc_info=True)
        await interaction.response.send_message("Something went wrong getting raid ready info from Google Sheets. Please try again later.")

    embed = discord.Embed(title=f'Fetching {character_name.title()}-{character_server.title()}\'s Armory Data...')
    await interaction.response.send_message(embed=embed, ephemeral=True)
    server_slug = character_server.lower().replace("'", "").replace(" ", "")

    try:
        character_equipment_unloaded = requests.get(f"https://raider.io/api/v1/characters/profile?region=us&realm={server_slug}&name={character_name}&fields=gear:live").content
        character_equipment = json.loads(character_equipment_unloaded)
    except HTTPError as e:
        logging.error("Exception occurred", exc_info=True)
        await interaction.edit_original_response(embed=discord.Embed(title=f'Error: {e}'))

    character_name: str = character_equipment['name']
    character_race: str = character_equipment['race']
    character_class: str = character_equipment['class']
    character_class_color = bot_config.wow_class_color_dict[character_class]
    character_spec: str = character_equipment['active_spec_name']
    character_ilvl: int = character_equipment['gear']['item_level_equipped']
    thumbnail = character_equipment['thumbnail_url']

    embed = discord.Embed(title='Parsing API Response')
    await interaction.edit_original_response(embed=embed)


    enchanted_list: list = []
    for slot in character_equipment['gear']['items']:
        if "enchant" in character_equipment['gear']['items'][slot]:
            if slot == "waist":
                pass
            else:
                enchanted_list.append(slot)

    embed = discord.Embed(title='Parsing API Response.')
    await interaction.edit_original_response(embed=embed)

    embed = discord.Embed(title='Parsing API Response..')
    await interaction.edit_original_response(embed=embed)

    embed = discord.Embed(title='Parsing API Response...')
    await interaction.edit_original_response(embed=embed)

    embed = discord.Embed(title='Parsing API Response...done')
    await interaction.edit_original_response(embed=embed)

    embed = discord.Embed(title='Building Ready to Raid Table')
    await interaction.edit_original_response(embed=embed)

    embed = discord.Embed(
        description=f'{character_name}, {character_spec} {character_class}\n'
                    f'[Armory](https://worldofwarcraft.com/en-us/character/us/{server_slug}/{character_name}) | '
                    f'[Raider.io](https://raider.io/characters/us/{server_slug}/{character_name}) | '
                    f'[Warcraft Logs](https://www.warcraftlogs.com/character/us/{server_slug}/{character_name}) | '
                    f'[Raidbots](https://www.raidbots.com/simbot/quick?region=us&realm={server_slug}&name={character_name})',
        title='Ready to Raid Checker',
        url="https://docs.google.com/spreadsheets/d/1l_-cLmY7-kXp1OncDSk8wjgQWb5aT1WxJGLEU5_TQCM/edit?usp=sharing",
        color=character_class_color
    )

    checkmark = '???'
    xmark = '???'
    ready_mark = ''

    embed.add_field(
        name='Check for these enchanted slots:',
        value='Back, Chest, Wrist, Legs, Feet, Finger1, Finger2, Mainhand, Offhand (if applicable)',
        inline=False
    )

    if character_ilvl >= min_ilvl:
        ready_mark = checkmark
    else:
        ready_mark = xmark

    embed.add_field(name='Item Level Equipped', value=f'{ready_mark} {character_ilvl}', inline=True)

    expected_slots = ['back', 'chest', 'wrist', 'legs', 'feet', 'finger1', 'finger2', 'mainhand', 'offhand']

    for gearslot in enchanted_list:
        try:
            if enchant_map[character_equipment['gear']['items'][gearslot]['enchant']] in enchants_list:
                ready_mark = checkmark
            else:
                ready_mark = xmark
            embed.add_field(
                name=gearslot.capitalize(),
                value=f"{ready_mark} {enchant_map[character_equipment['gear']['items'][gearslot]['enchant']]}",
                inline=False
            )
        except:
            embed.add_field(
                name=gearslot.capitalize(),
                value=f"{xmark} Non-Dragonflight Enchant. Check armory or add it to the list of accepted enchants",
                inline=False
            )

    unenchanted_slots = [x for x in expected_slots if x not in enchanted_list]
    unenchanted_slots_string = ', '.join(unenchanted_slots)

    embed.set_footer(text=f'Unenchanted Slots: {unenchanted_slots_string}')

    embed.set_thumbnail(url=thumbnail)


    await interaction.edit_original_response(embed=embed)


# Get the names of all the commands in this file to make a help command
command_list: list = [f'/{x.name}' for x in client.tree.walk_commands()]
command_list.sort()
middle_index = len(command_list)//2
help_string1: str = f'\n'.join(str(name) for name in command_list[:middle_index])
help_string2: str = f'\n'.join(str(name) for name in command_list[middle_index:])

@client.tree.command()
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
