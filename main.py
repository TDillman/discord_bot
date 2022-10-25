import discord
import logging
import asyncio
import datetime
import logging.handlers
import bot_secrets
import gspread
import random

from discord import app_commands, ui
from blizzardapi import BlizzardApi
from youtube_api import YouTubeDataAPI
from dataclasses import dataclass, field


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

MY_GUILD = discord.Object(id=bot_secrets.GUILD_ID)
might_logo = 'https://cdn.discordapp.com/attachments/676183284123828236/679823287521771602/mightcoloredfinishedsmall.png'
error_icon_url = 'https://cdn0.iconfinder.com/data/icons/shift-interfaces/32/Error-512.png'

kat_gif_list = [
    "https://tenor.com/view/eye-squint-markiplier-glare-suspicious-gif-15742154",
    "https://tenor.com/view/really-what-squint-chicken-gif-15168180",
    "https://tenor.com/view/skeptical-futurama-fry-hmmm-i-got-my-eyes-on-you-gif-17101711",
    "https://tenor.com/view/buffy-the-vampire-slayer-eye-gif-26036478",
    "https://tenor.com/view/dog-suspicious-suspicious-dog-squinting-squint-chihuahua-squint-gif-26088382",
    "https://tenor.com/view/pusheen-pusheen-cat-cat-cartoon-cute-gif-25196813"
]

#YouTube API
yt = YouTubeDataAPI(bot_secrets.YT_DATA_API)
#Blizzard API
api_client = BlizzardApi(bot_secrets.BLIZZARD_CLIENT_ID, bot_secrets.BLIZZARD_SECRET_ID)

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.overwatch_role = bot_secrets.overwatch_role
        self.movie_role = bot_secrets.movie_role
        self.m_plus_role = bot_secrets.m_plus_role
        self.pvp_role = bot_secrets.pvp_role
        self.colorado_role = bot_secrets.colorado_role
        self.mightcon_role = bot_secrets.mightcon_role
        self.ready_to_raid_role = bot_secrets.ready_to_raid_role

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        self.add_view(RoleSelectView())


intents = discord.Intents.default()
client = MyClient(intents=intents)

class RoleSelectView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout = None)

    @discord.ui.button(label = "Overwatch", style=discord.ButtonStyle.green, custom_id="overwatch", emoji="🔫")
    async def overwatch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if type(client.overwatch_role) is not discord.Role:
            client.overwatch_role = interaction.guild.get_role(bot_secrets.overwatch_role)
        if client.overwatch_role not in interaction.user.roles:
            await interaction.user.add_roles(client.overwatch_role)
            button.label = "Remove Overwatch Role"
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
        else:
            await interaction.user.remove_roles(client.overwatch_role)
            button.label = "Add Overwatch Role"
            button.style = discord.ButtonStyle.green
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label = "WoW M+", style=discord.ButtonStyle.green, custom_id="m_plus_runner", emoji="🥇")
    async def m_plus_runner(self, interaction: discord.Interaction, button: discord.ui.Button):
        if type(client.m_plus_role) is not discord.Role:
            client.m_plus_role = interaction.guild.get_role(bot_secrets.m_plus_role)
        if client.m_plus_role not in interaction.user.roles:
            await interaction.user.add_roles(client.m_plus_role)
            button.label = "Remove M+ Role"
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
        else:
            await interaction.user.remove_roles(client.m_plus_role)
            button.label = "Add M+ Role"
            button.style = discord.ButtonStyle.green
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label = "WoW PvP", style=discord.ButtonStyle.green, custom_id="wow_pvp", emoji="🪓")
    async def wow_pvp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if type(client.pvp_role) is not discord.Role:
            client.pvp_role = interaction.guild.get_role(bot_secrets.pvp_role)
        if client.pvp_role not in interaction.user.roles:
            await interaction.user.add_roles(client.pvp_role)
            button.label = "Remove PvP Role"
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
        else:
            await interaction.user.remove_roles(client.pvp_role)
            button.label = "Add PvP Role"
            button.style = discord.ButtonStyle.green
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label = "Movie Night", style=discord.ButtonStyle.green, custom_id="movie_night", emoji="🍿")
    async def movie_night(self, interaction: discord.Interaction, button: discord.ui.Button):
        if type(client.movie_role) is not discord.Role:
            client.movie_role = interaction.guild.get_role(bot_secrets.movie_role)
        if client.movie_role not in interaction.user.roles:
            await interaction.user.add_roles(client.movie_role)
            button.label = "Remove Movie Night Role"
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
        else:
            await interaction.user.remove_roles(client.movie_role)
            button.label = "Add Movie Night Role"
            button.style = discord.ButtonStyle.green
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Mightcon Vegas", style=discord.ButtonStyle.green, custom_id="mightcon_vegas", emoji="🎰")
    async def mightcon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if type(client.mightcon_role) is not discord.Role:
            client.mightcon_role = interaction.guild.get_role(bot_secrets.mightcon_role)
        if client.mightcon_role not in interaction.user.roles:
            await interaction.user.add_roles(client.mightcon_role)
            button.label = "Remove Mightcon Vegas Role"
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.response.send_message(f'{client.mightcon_role.mention} has been added to your roles!\n'
                                                    f'Make sure you update the sheet at https://1drv.ms/x/s!AkHIyFpbYJ2agmoleZoB1hQm8ad7?e=3Sf8z8', ephemeral=True)
        else:
            await interaction.user.remove_roles(client.mightcon_role)
            button.label = "Add Mightcon Vegas Role"
            button.style = discord.ButtonStyle.green
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Colorado Peeps", style=discord.ButtonStyle.green, custom_id="colorado", emoji="🏔")
    async def colorado(self, interaction: discord.Interaction, button: discord.ui.Button):
        if type(client.colorado_role) is not discord.Role:
            client.colorado_role = interaction.guild.get_role(bot_secrets.colorado_role)
        if client.colorado_role not in interaction.user.roles:
            await interaction.user.add_roles(client.colorado_role)
            button.label = "Remove Colorado Peeps Role"
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
        else:
            await interaction.user.remove_roles(client.colorado_role)
            button.label = "Add Colorado Peeps Role"
            button.style = discord.ButtonStyle.green
            await interaction.response.edit_message(view=self)


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('with fire. Type /help!'))
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        embed = discord.Embed(title='Error')
        embed.add_field(name='Command on Cooldown', value=f'That command is on cooldown for {error.retry_after:.2f} more seconds.')
        embed.set_thumbnail(url=error_icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingAnyRole):
        embed = discord.Embed(title='Error')
        embed.add_field(name='Permission Missing', value=f"You're missing a permission to do that.")
        embed.add_field(name='Error', value=error, inline=False)
        embed.set_thumbnail(url=error_icon_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


@client.tree.command()
@discord.app_commands.checks.has_any_role("GM", "Assistant GM", "Guild Officer", "Guild Leader")
async def role_select(interaction: discord.Interaction):
    embed = discord.Embed(title='Roles')
    embed.add_field(name='Select Your Roles',
                    value=f"Click the button you'd like to get pings for! Click it again to remove the role.")
    embed.set_thumbnail(url=might_logo)
    await interaction.response.send_message(embed=embed, view = RoleSelectView())


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')
    print(interaction.user.roles)


# The rename decorator allows us to change the display of the parameter on Discord.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)

# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')

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
async def abba(interaction: discord.Interaction):
    """Hehehehehehehe"""
    await interaction.response.send_message('https://tenor.com/view/lizard-laughing-laughinglizard-hehehe-gif-5215392')

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
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def token(interaction: discord.Interaction):
    """
    Returns an embed with the current WoW token price in gold
    """
    token_object = api_client.wow.game_data.get_token_index("us", "en_US")
    print(token_object)

    embed = discord.Embed(title='WoW Token')
    embed.add_field(name='Current Price', value=f'{token_object["price"] / 10000:,.0f} gold')
    embed.set_thumbnail(
        url='https://cdn.discordapp.com/attachments/676183284123828236/679823287521771602/mightcolored'
            'finishedsmall.png')
    await interaction.response.send_message(embed=embed)

@client.tree.command()
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def status(interaction: discord.Interaction):
    """Status of the Arygos server"""

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


# Google Sheets API
gc = gspread.service_account()
worksheet = gc.open('Raid Requirements').get_worksheet(1)
@client.tree.command(description="Checks a user's character for raid readiness")
@discord.app_commands.checks.has_any_role("GM", "Assistant GM", "Guild Officer", "Guild Leader")
@app_commands.describe(character_name='character name')
@app_commands.describe(character_server='server name')
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
async def r2r(interaction: discord.Interaction, character_name: str, character_server: str):
    """
    Returns an embed with the specified character's R2R status
    """

    min_ilvl: int = int(worksheet.col_values(1)[0])
    bracer_enchants_list: list = worksheet.col_values(2)[1:]
    weapon_enchants_list: list = worksheet.col_values(3)[1:]
    chest_enchants_list: list = worksheet.col_values(4)[1:]
    ring_enchants_list: list = worksheet.col_values(5)[1:]
    cloak_enchants_list: list = worksheet.col_values(6)[1:]
    boots_enchants_list: list = worksheet.col_values(7)[1:]

    embed = discord.Embed(title=f'Fetching {character_name.title()}-{character_server.title()}\'s Armory Data...')
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await asyncio.sleep(1)
    server_slug = character_server.lower().replace("'", "").replace(" ", "")
    character_profile = api_client.wow.profile.get_character_profile_summary("us", "en_US", server_slug,
                                                                                 character_name.lower())
    character_equipment = api_client.wow.profile.get_character_equipment_summary("us", "en_US", server_slug,
                                                                                        character_name.lower())
    embed2 = discord.Embed(title='Parsing API Response')
    await interaction.edit_original_response(embed=embed2)
    await asyncio.sleep(.5)

    character_name = character_profile['name']
    character_level = character_profile['level']
    character_spec = character_profile['active_spec']['name']
    character_ilvl_avg = float(character_profile['average_item_level'])
    character_class = character_profile['character_class']['name']
    character_last_login = character_profile['last_login_timestamp']

    for item in character_equipment['equipped_items']:
        if item['slot']['type'] == 'WRIST':
            bracer_enchant = item['enchantments'][0]['source_item']['name']
        if item['slot']['type'] == 'MAIN_HAND':
            weapon_enchant = item['enchantments'][0]['source_item']['name']
        if item['slot']['type'] == 'CHEST':
            chest_enchant = item['enchantments'][0]['source_item']['name']
        if item['slot']['type'] == 'FINGER_1':
            ring1_enchant = item['enchantments'][0]['source_item']['name']
        if item['slot']['type'] == 'FINGER_2':
            ring2_enchant = item['enchantments'][0]['source_item']['name']
        if item['slot']['type'] == 'BACK':
            cloak_enchant = item['enchantments'][0]['source_item']['name']
        if item['slot']['type'] == 'FEET':
            boots_enchant = item['enchantments'][0]['source_item']['name']

    embed3 = discord.Embed(title='Building Ready to Raid Table')
    await interaction.edit_original_response(embed=embed3)
    await asyncio.sleep(.5)

    embed4 = discord.Embed(title='Ready to Raid',
                           description=f'{character_name}, level {character_level} {character_spec} {character_class}')

    checkmark = '✅'
    xmark = '❌'

    # Check character ilvl average against R2R minimum
    if character_ilvl_avg >= min_ilvl:
        ilvl_check = True
        embed4.add_field(name='Item Level', value=f'{checkmark} {character_ilvl_avg}', inline=False)
    if character_ilvl_avg < min_ilvl:
        ilvl_check = False
        embed4.add_field(name='Item Level', value=f'{xmark} {character_ilvl_avg}', inline=False)

    embed4.add_field(name='Enchants', value="------------------------------------", inline=False)

    # Check weapon enchant against R2R list
    if weapon_enchant in weapon_enchants_list:
        weapon_check = True
        embed4.add_field(name='Weapon', value=f'{checkmark} {weapon_enchant}', inline=False)
    else:
        weapon_check = False
        embed4.add_field(name='Item Level', value=f'{xmark} {weapon_enchant}', inline=False)

    # Check cloak enchant against R2R list
    if cloak_enchant in cloak_enchants_list:
        cloak_check = True
        embed4.add_field(name='Cloak', value=f'{checkmark} {cloak_enchant}', inline=False)
    else:
        cloak_check = False
        embed4.add_field(name='Cloak', value=f'{xmark} {cloak_enchant}', inline=False)

    # Check chest enchant against R2R list
    if chest_enchant in chest_enchants_list:
        chest_check = True
        embed4.add_field(name='Chest', value=f'{checkmark} {chest_enchant}', inline=False)
    else:
        chest_check = False
        embed4.add_field(name='Chest', value=f'{xmark} {chest_enchant}', inline=False)

    # Check boots enchant against R2R list
    if boots_enchant in boots_enchants_list:
        boots_check = True
        embed4.add_field(name='Boots', value=f'{checkmark} {boots_enchant}', inline=False)
    else:
        boots_check = False
        embed4.add_field(name='Boots', value=f'{xmark} {boots_enchant}', inline=False)

    # Check ring 1 enchant against R2R list
    if ring1_enchant in ring_enchants_list:
        ring1_check = True
        embed4.add_field(name='Ring 1', value=f'{checkmark} {ring1_enchant}', inline=True)
    else:
        ring1_check = False
        embed4.add_field(name='Ring 1', value=f'{xmark} {ring1_enchant}', inline=True)

    # Check ring 2 enchant against R2R list
    if ring2_enchant in ring_enchants_list:
        ring2_check = True
        embed4.add_field(name='Ring 2', value=f'{checkmark} {ring2_enchant}', inline=True)
    else:
        ring2_check = False
        embed4.add_field(name='Ring 2', value=f'{xmark} {ring2_enchant}', inline=True)

    # Check bracer enchant against R2R list
    if bracer_enchant in bracer_enchants_list:
        bracer_check = True
        embed4.add_field(name='Bracers', value=f'{checkmark} {bracer_enchant}', inline=False)
    else:
        bracer_check = False
        embed4.add_field(name='Bracers', value=f'{xmark} {bracer_enchant}', inline=False)

    # Check booleans from previous checks to determine ready to raid status
    if ilvl_check and weapon_check and cloak_check and chest_check and boots_check and ring1_check and ring2_check and bracer_check:
        r2r_check = True
        embed4.add_field(name='Ready to Raid', value=f'{checkmark} Ready to Raid', inline=False)
    else:
        r2r_check = False
        embed4.add_field(name='Ready to Raid', value=f'{xmark} Not Ready to Raid', inline=False)

    if r2r_check == True:
        r2r_color = 0x00ff00  # Green for up
    else:
        r2r_color = 0xff0000  # Red for down

    datetime_last_login = datetime.datetime.fromtimestamp(character_last_login / 1000)
    embed4.set_footer(text=f'Last login: {datetime_last_login}')
    embed4.color = r2r_color
    embed4.set_thumbnail(url=might_logo)

    await interaction.edit_original_response(embed=embed4)


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
