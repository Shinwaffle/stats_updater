from enum import Enum
from optparse import Option
import random
from urllib.error import HTTPError
from venv import create
from pygsheets.exceptions import SpreadsheetNotFound
from googleapiclient.errors import HttpError
from requests import get
import threading
import pygsheets
import interactions
import logging
from time import sleep
import os
import shutil
import pandas as pd
TOKEN = "OTk2MjUwMDM4NzY4NTIxMzQ2.GH7vyQ.5PeEm_vHTh03oDl-hmFV4SfGDYOBbO6sZGjgAo"
PYGSHEETS_BOTACC_PATH = ".messager.json"

logging.basicConfig(level=logging.INFO)


class Columns(str, Enum):
    """
    Enum representating the columns used in the spreadsheet
    """
    NAME = "A"
    AVAILABILITY = "B"
    PVP_CR = "C"
    CHAR_CR = "D"
    RESONANCE = "E"
    PARAGON_LEVEL = "F"
    PARAGON_TREE = "G"
    BUILD = "H"


keys = []
for enum in Columns:
    keys.append(enum)
gc = pygsheets.authorize(service_file=PYGSHEETS_BOTACC_PATH)

bot = interactions.Client(
    token=TOKEN, intents=interactions.Intents.ALL)
GUILD_ID = 996247298185109525


@bot.command(
    name='share_sheet',
    description='share the google sheet with other people!',
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
    options=[
        interactions.Option(
                name="role",
                description="Choose what kind of permissions the person has to the sheet",
                type=interactions.OptionType.STRING,
                required=True,
                choices=[
                    interactions.Choice(
                        name="Editor", value="writer"),
                    interactions.Choice(
                        name="Viewer", value="reader"),
                    interactions.Choice(
                        name="Commenter", value="commenter"),
                ],
        ),
        interactions.Option(
            name="email",
            description="put in an email to share to",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def cmd(ctx: interactions.CommandContext, role=None, email=None):
    await ctx.defer(ephemeral=True)
    guild_id = str(ctx.guild_id)
    try:
        gc.open(guild_id).share(role=role, email_or_domain=email)
    except SpreadsheetNotFound as ex:
        gc.create(guild_id).share(role=role, email_or_domain=email)
    except HttpError as ex:
        await ctx.send("I don't think that is a correct email address, try again.")
        return
    await ctx.send('check your email')


@bot.command(
    name='csv',
    description='parent',
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
    options=[
        interactions.Option(
                name="upload",
                description="upload your own csv file for your data!",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="file",
                        description="upload your csv",
                        type=interactions.OptionType.ATTACHMENT,
                        required=True,
                    ),
                ],
        ),
    ],
)
async def cmd(ctx: interactions.CommandContext, sub_command: str, file: interactions.Attachment = None):
    with open(f'./guilds/{ctx.guild_id}/stats.csv', 'wb') as f:
        response = get(file.url)
        f.write(response.content)
    await ctx.send('i think i did it?')


@bot.command(
    name="statistics",
    description="parent command",
    options=[
        interactions.Option(
            name="info",
            description="Spreadsheet links and help video",
            type=interactions.OptionType.SUB_COMMAND
        ),
        interactions.Option(
            name="show",
            description="Display somebody's stats (if they set it, of course)",
            type=interactions.OptionType.SUB_COMMAND,
            options=[
                interactions.Option(
                    name="name",
                    description="Specify the name of the user, or leave blank for yourself",
                    type=interactions.OptionType.USER,
                    required=False,
                ),
            ],
        ),
        interactions.Option(
            name="set",
            description="Set your stats for everyone to see!",
            type=interactions.OptionType.SUB_COMMAND,
            options=[
                interactions.Option(
                    name="availability",
                    description="Will you be available for Rite of Exile?",
                    type=interactions.OptionType.STRING,
                    required=False,
                    choices=[
                        interactions.Choice(
                            name="Yes", value='Yes'
                        ),
                        interactions.Choice(
                            name="Maybe", value='Maybe'
                        ),
                        interactions.Choice(
                            name="No", value='No'
                        )
                    ]
                ),
                interactions.Option(
                    name="pvp_cr",
                    description="Life & Combat Attributes, put -1 for Completed",
                    type=interactions.OptionType.INTEGER,
                    required=False,
                ),
                interactions.Option(
                    name="char_cr",
                    description="Combat Rating",
                    type=interactions.OptionType.INTEGER,
                    required=False,
                ),
                interactions.Option(
                    name="resonance",
                    description="Your resonance",
                    type=interactions.OptionType.INTEGER,
                    required=False,
                ),
                interactions.Option(
                    name="paragon_level",
                    description="Your paragon level",
                    type=interactions.OptionType.INTEGER,
                    required=False,
                ),
                interactions.Option(
                    name="paragon_tree",
                    description="Your paragon tree. Choose one!",
                    type=interactions.OptionType.STRING,
                    required=False,
                    choices=[
                        interactions.Choice(
                            name="Vanquisher", value="Vanquisher"),
                        interactions.Choice(
                            name="Survivor", value="Survivor"),
                        interactions.Choice(
                            name="Treasure Hunter", value="Treasure Hunter"),
                        interactions.Choice(
                            name="Gladiator", value="Gladiator"),
                        interactions.Choice(
                            name="Soldier", value="Soldier"),
                        interactions.Choice(
                            name="Mastermind", value="Mastermind"),
                    ]
                ),
                interactions.Option(
                    name="build",
                    description="Description of build, skills/combos/playstyle etc.",
                    type=interactions.OptionType.STRING,
                    required=False,
                )
            ],
        ),
    ],
)
async def cmd(ctx: interactions.CommandContext, sub_command: str, name=None, availability=None, pvp_cr=None, char_cr=None, resonance=None, paragon_level=None, paragon_tree=None, build=None):
    to_check = [[availability, Columns.AVAILABILITY],
                [pvp_cr, Columns.PVP_CR],
                [char_cr, Columns.CHAR_CR],
                [resonance, Columns.RESONANCE],
                [paragon_level, Columns.PARAGON_LEVEL],
                [paragon_tree, Columns.PARAGON_TREE],
                [build, Columns.BUILD]]

    guild_id = str(ctx.guild_id)

    if sub_command == "info":
        await ctx.send('Link to youtube video on how to use the command: https://www.youtube.com/watch?v=IWRB_7_-r2g\ndocs coming soon', ephemeral=True)
        return
    elif sub_command == "show":
        await show_command(ctx, guild_id, name)
        return
    elif sub_command == "set":
        await set_command(ctx, guild_id, to_check)
        return
    else:
        await ctx.send('Something went wrong. Please try again', ephemeral=True)
        logging.critical("We have reached end of cmd without a return."
                         f"Name: {ctx.author.name}"
                         f"Number of parameters provided: {to_check}")
        return


async def show_command(ctx, guild_id, name):
    name = str(name)
    await ctx.defer(ephemeral=True)
    df = get_table(guild_id, lock=False)
    if name == 'None':
        if df.loc[(df['Name'] == str(ctx.author.name))].empty:
            await ctx.send("you haven't put in your info yet!")
            return
        else:
            stats = df.loc[df.loc[(
                df['Name'] == str(ctx.author.name))].index[0]].tolist()
            await send_embed(ctx, stats)
            return

    else:
        if not df.loc[df['Name'] == name].empty:
            stats = df.loc[df.loc[(df['Name'] == name)].index[0]].tolist()
            await send_embed(ctx, stats)
            return
        else:
            await ctx.send("that person hasn't put in their info yet!")
            return


async def set_command(ctx, guild_id, to_check):
    await ctx.defer(ephemeral=True)
    _first_time_setup_check(guild_id)
    seconds = 1
    while os.path.isfile(f'./guilds/{guild_id}/db.lock'):
        sleep(seconds)
        seconds *= 2
        if seconds > 8:
            # TODO better log
            logging.warning(
                'set command timed out for longer than 30 seconds, please check.')
            os.remove(f'./guilds/{guild_id}/db.lock')
    df = get_table(guild_id)

    columns = ['Name',
               "Availability",
               "PVP CR",
               "Character CR",
               "Resonance",
               "Paragon Level",
               "Paragon Tree",
               "Build"]
    stats = [ctx.author.name]
    for stat in to_check:
        stats.append(stat[0])

    if stats[2] == -1:
        stats[2] = "Max"  # see line 88

    for index, stat in enumerate(stats):
        try:
            if len(stat) > 1024:
                # TODO log instance
                await ctx.send('One of your inputs is longer than 1024 characters, consider rewriting.')
                return
        except TypeError as ex:
            pass  # tested int
        if stat is None or stat == "NaN":
            stats[index] = "Not Set"

    if df.loc[(df['Name'] == ctx.author.name)].empty:
        df = pd.concat(
            [df, pd.DataFrame([stats], columns=columns)], ignore_index=True)
    else:
        index = df.loc[(df['Name'] == ctx.author.name)].index[0]
        for column, stat in zip(columns, stats):
            if not df.loc[index, [column]].empty and stat == "Not Set":
                continue
            df.loc[index, [column]] = stat
    await save_changes(df, guild_id)
    await ctx.send('Updated!')
    return


async def send_embed(ctx, results):
    """
    Creates a pretty embed for the bot to send in the context provided
    """

    # cannot send embed with int64 values as they are not serializible
    # these come from the pandas df
    for index, stat in enumerate(results):
        if isinstance(stat, str):
            continue
        results[index] = int(stat)

    embed = interactions.Embed(color=random.randint(0, 65536))
    embed.set_author(name=results[0])  # get author icon url here
    embed.add_field(name="Available for Rite of Exile?",
                    value=results[1], inline=True)
    embed.add_field(name="PVP CR",
                    value=results[2], inline=True)
    embed.add_field(name="Character CR",
                    value=results[3], inline=True)
    embed.add_field(name="Resonance",
                    value=results[4], inline=True)
    embed.add_field(name="Paragon Level",
                    value=results[5], inline=True)
    embed.add_field(name="Paragon Tree",
                    value=results[6], inline=True)
    embed.add_field(name="Build",
                    value=results[7], inline=False)

    debug = ""
    for field in embed.fields:
        debug += f'{field.value}\n'
    logging.info(
        f'Sending embed with author {embed.author.name} and value fields: \n{debug}')
    channel = await ctx.get_channel()
    await channel.send(embeds=embed)
    await ctx.send('sent!')


def get_table(guild_id, lock=True):
    if os.path.exists(f"./guilds/{guild_id}/stats.csv"):
        if lock:
            open(f"./guilds/{guild_id}/db.lock", "w")
        return pd.read_csv(f"./guilds/{guild_id}/stats.csv")
    else:
        logging.error(f"We can't get table for guild id {guild_id}")


async def save_changes(df, guild_id):
    df.to_csv(f'./guilds/{guild_id}/stats.csv', index=False)
    try:
        os.remove(f'./guilds/{guild_id}/db.lock')
    except FileNotFoundError as ex:
        pass

_ready = False


@bot.event
async def on_ready():
    logging.info(f'logged in as {bot}')
    global _ready
    if not _ready:
        _ready = True
        print('created thread')
        upload = threading.Thread(target=minutely_upload_csv, name="uploader")
        upload.start()


def minutely_upload_csv():
    while True:
        for guild in os.listdir("./guilds"):
            if guild == 'example':
                continue
            df = pd.read_csv(f'./guilds/{guild}/stats.csv')
            try:
                gc.open(guild).sheet1.set_dataframe(df, [1, 0])
            except SpreadsheetNotFound as ex:
                pass  # haven't used any of the commands yet, no need to waste resources
        sleep(60)


def _first_time_setup_check(guild):
    if os.path.exists(f"./guilds/{guild}"):
        return
    os.mkdir(f'./guilds/{guild}')
    shutil.copy("./guilds/example/stats.csv", f"./guilds/{guild}/")
    try:
        gc.open(guild)
    except SpreadsheetNotFound as ex:
        gc.create(guild)


bot.start()
