from enum import Enum
import random
from pygsheets.exceptions import SpreadsheetNotFound
import pygsheets
import interactions
import logging
from time import sleep
import os
import shutil
import pandas as pd
TOKEN = ""
PYGSHEETS_BOTACC_PATH = os.environ.get("PYGSHEETS_BOTACC_PATH")

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
GUILD_ID = 996247141553033327


@bot.command(
    name="statistics",
    description="parent command",
    scope=GUILD_ID,
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

    guild_id = ctx.get_guild().id
    worksheet = in_a_clan(ctx)
    if sub_command == "info":
        await ctx.send('Link to spreadsheet for people in a clan (Winter Clan, Ancient Defenders, Legion): https://docs.google.com/spreadsheets/d/1EezXrKVAaoXGyAis7u5j_70iUiPZhGJwp82akXtdeXQ/edit?usp=sharing\n'
                       'Link to spreadsheet for everyone else: https://docs.google.com/spreadsheets/d/1TvnuY4fSNcAPCNir0m2Uy_cWcSqQjXzcvWlz8T4INxs/edit#gid=0\n'
                       'Link to youtube video on how to use the command: https://www.youtube.com/watch?v=IWRB_7_-r2g', ephemeral=True)
        return
    elif sub_command == "show":
        await show_command(ctx, worksheet, name)
        return
    elif sub_command == "set":
        await set_command(ctx, worksheet, to_check)
        return
    else:
        await ctx.send('Something went wrong. Please try again', ephemeral=True)
        logging.critical("We have reached end of cmd without a return."
                         f"Name: {ctx.author.name}"
                         f"Number of parameters provided: {to_check}")
        return


async def show_command(ctx, worksheet, name):
    await ctx.defer(ephemeral=True)
    # name is of Member type if specified, think of it as "user"
    # i think some of this doesn't even fire but whatever
    if name == None:
        if results := user_exists(worksheet, ctx.author.name):
            logging.info(
                f'Found user {ctx.author.user}, now calling send_embed')
            await ctx.send(f'Found user! Sending stats...')
            await send_embed(ctx, results)
            return
        else:
            logging.debug(f'Did not find user {name.name}.')
            await ctx.send("You haven't put in your info yet!", ephemeral=True)
            return

    if results := user_exists(worksheet, name.name):
        logging.debug(f'Found lookup of user {name.name}')
        await ctx.send(f'Found user! Sending stats...')
        await send_embed(ctx, results)
        return
    else:
        logging.debug(f"Did not find user {name.name}")
        await ctx.send("That user doesn't exist!", ephemeral=True)
        return

    async def show_command_test(ctx, name):
        df = get_table(guild_id, lock=False)
        if name is None:
            if df.loc[(df['Name'] == ctx.author.name)].empty:
                await ctx.send("you haven't put in your info yet!")
            else:
                # send embed
                ...
        else:
            if df.loc[(df['Name'] == ctx.author.name)].empty:
                await ctx.send("that person hasn't put in their info yet!")
            else:
                # send embed
                ...


async def set_command(ctx, worksheet, to_check):
    await ctx.defer(ephemeral=True)
    if results := user_exists(worksheet, ctx.author.name):
        worksheet.update_value(
            f'{Columns.NAME}{results["ROW"]}', ctx.author.name)
        for stat in to_check:
            if stat[0] is not None:
                try:
                    if len(stat[0]) > 1024:
                        logging.debug(
                            f'Caught input longer than 1024 {stat[0]}')
                        await ctx.send('One of your fields is beyond 1024 characters! considering shortening it.')
                        return
                except TypeError as ex:
                    pass
                if stat[0] == -1:
                    worksheet.update_value(f'{stat[1]}{results["ROW"]}', 'Max')
                    logging.debug(f'Synced change Max to {ctx.author.name}')
                    continue
                worksheet.update_value(
                    f'{stat[1]}{results["ROW"]}', stat[0])
                logging.debug(f'Synced change {stat[0]} to {ctx.author.name}')
        logging.info(f'updated user {ctx.author.name}')
        await ctx.send('Updated! Make sure to sign up for Rite of Exile in #rite-of-exile because THIS DOESNT COUNT AS A SIGN UP!!!!!!!', ephemeral=True)
        return
    else:
        new_user = new_user_row(worksheet)
        worksheet.update_value(
            f'{Columns.NAME}{new_user}', ctx.author.name)
        for stat in to_check:
            if stat[0] is not None:
                if stat[0] == -1:
                    worksheet.update_value(f'{stat[1]}{results["ROW"]}', 'Max')
                    logging.debug(f'Synced change Max to {ctx.author.name}')
                    continue
                worksheet.update_value(f'{stat[1]}{new_user}', stat[0])
                logging.debug(f'Synced change {stat[0]} to {ctx.author.name}')
        logging.info(f'updated new user {ctx.author.name}')
        await ctx.send('Updated!', ephemeral=True)
        return
    logging.error(
        f'Could not update user {ctx.author.name} with values {to_check}')
    await ctx.send(f'Could not update user.', ephemeral=True)
    return

    async def _testing_function(ctx, guild_id, to_check):
        await ctx.send('Updating...')
        df = get_table(guild_id)
        while os.path.isfile(f'./guilds/{guild_id}/db.lock'):
            seconds = 1
            await ctx.send("Please wait, waiting turn for lock. This shouldn't take longer than 5 minutes.")
            sleep(seconds)
            seconds *= 2
            if seconds > 128:  # checks for 256, after doubling it is 4.25 minutes.
                # TODO better log
                logging.warning(
                    'set command timed out for longer than 5 minutes, please check.')
                os.remove(f'./guilds/{guild_id}/db.lock')

        await ctx.send('Updating...')
        columns = ['Name',
                   "Availability",
                   "PVP CR",
                   "Character CR",
                   "Resonance",
                   "Paragon Level",
                   "Paragon Tree",
                   "Build"]
        stats = []
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
            if stat == "None" or stat == "NaN":
                stats[index] = "Not Set"

        if df.loc[(df['Name'] == ctx.author.name)].empty:
            df = pd.concat([df, pd.DataFrame([stats], columns=columns)])
        else:
            index = df.loc[(df['Name'] == ctx.author.name)].index[0]
            for column, stat in zip(columns, stats):
                df.loc[index, [column]] = stat
        save_changes(df, guild_id)


async def send_embed(ctx, results):
    """
    Creates a pretty embed for the bot to send in the context provided
    """

    for key, value in results.items():
        if not value:
            logging.debug(f'Set {results[key]} to "Not Set"')
            results[key] = "Not Set"

    # look into EmbedImageStruct for images

    embed = interactions.Embed(color=random.randint(0, 65536))
    embed.set_author(name=results[Columns.NAME])
    embed.add_field(name="Available for Rite of Exile?",
                    value=results[Columns.AVAILABILITY], inline=True)
    embed.add_field(name="PVP CR",
                    value=results[Columns.PVP_CR], inline=True)
    embed.add_field(name="Character CR",
                    value=results[Columns.CHAR_CR], inline=True)
    embed.add_field(name="Resonance",
                    value=results[Columns.RESONANCE], inline=True)
    embed.add_field(name="Paragon Level",
                    value=results[Columns.PARAGON_LEVEL], inline=True)
    embed.add_field(name="Paragon Tree",
                    value=results[Columns.PARAGON_TREE], inline=True)
    embed.add_field(name="Build",
                    value=results[Columns.BUILD], inline=False)
    debug = ""
    for field in embed.fields:
        debug += f'{field.value}\n'
    logging.info(
        f'Sending embed with author {embed.author.name} and value fields: \n{debug}')
    channel = await ctx.get_channel()
    await channel.send(embeds=embed)


def gc_init():
    """
    init pygsheets with service account and the stats spreadsheet.
    if it doesn't exist, create it.

    returns: sheet1 of stats to edit info
    """
    gc = pygsheets.authorize(
        service_file=PYGSHEETS_BOTACC_PATH)
    sh = None
    try:
        sh = gc.open('stats')
    except SpreadsheetNotFound as ex:
        logging.info('stats spreadsheet not found, creating...')
        gc.create('stats')
        sh = gc.open('stats')
    wks = sh.sheet1
    wks.link()
    return wks


def gc_nonclan_init():
    """
    init pygsheets with service account and the stats spreadsheet.
    if it doesn't exist, create it.

    returns: sheet1 of stats to edit info
    """
    gc = pygsheets.authorize(service_file=PYGSHEETS_BOTACC_PATH)
    sh = None
    try:
        sh = gc.open('stats_nonclan')
    except SpreadsheetNotFound as ex:
        logging.info('stats_nonclan spreadsheet not found, creating...')
        gc.create('stats_nonclan')
        sh = gc.open('stats_nonclan')
    wks = sh.sheet1
    wks.link()
    return wks


def in_a_clan(ctx):
    global worksheet, worksheet_nonclan
    # ancient defenders then legion then winter clan
    clans = [989278711478124655, 989278770009632858, 983855347867451452]
    for role in ctx.author.roles:
        if role in clans:
            return worksheet

    return worksheet_nonclan


def user_exists(wks, name):
    """
    takes in worksheet object and finds given name. if it finds it, spit out related values
    """
    global keys

    logging.debug(f'Looking up name {name}')
    found = None
    final = {}
    row = None
    # for SOME reason it puts a list inside of a list.
    # im guessing theres a method to do this better but whatever
    for the_list in wks.range('A2:A1000'):
        for cell in the_list:
            if cell.value == name:
                found = wks.range(
                    f'{Columns.NAME}{cell.row}:{Columns.BUILD}{cell.row}')
                row = cell.row
    if not found:
        logging.info(f'Requested user {name} does not exist.')
        return None
    for thingy in found:
        for index, cell in enumerate(thingy):
            final[keys[index]] = cell.value

    final["ROW"] = row
    logging.info(f'Returning final value of {final}')
    return final


def new_user_row(wks):
    """q
    Finds an empty c1000 to use for a new user to enter stats
    """
    for the_list in wks.range('A2:A1000'):
        for cell in the_list:
            if cell.value == '':
                logging.info(f'New user row was requested. Giving {cell.row}')
                return cell.row


def get_table(guild_id, lock=True):
    if os.path.exists(f"./guilds/{guild_id}/stats.csv"):
        if lock:
            open(f"./guilds/{guild_id}/db.lock", "w")
        return pd.read_csv(f"./guilds/{guild_id}/stats.csv")
    else:
        logging.error(f"We can't get table for guild id {guild_id}")


async def save_changes(df, guild_id):
    df.to_csv(f'./guilds/{guild_id}/stats.csv')
    try:
        os.remove(f'./guilds/{guild_id}/db.lock')
    except FileNotFoundError as ex:
        pass


@bot.event
async def on_ready():
    logging.info(f'logged in as {bot.name}')


@bot.event
async def on_guild_join(guild):
    os.mkdir(f'./guilds/{guild.id}')
    shutil.copy("./guilds/example/*", f"./guilds/{guild.id}/")
    try:
        sh = gc.open(guild.id)
    except SpreadsheetNotFound as ex:
        logging.info(f'{guild.id} doesnt have sheet, creating')
        gc.create(guild.id)


worksheet = gc_init()
worksheet_nonclan = gc_nonclan_init()
bot.start()
