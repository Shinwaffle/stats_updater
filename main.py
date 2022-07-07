import interactions

import pygsheets
from pygsheets.exceptions import SpreadsheetNotFound

import random
from enum import Enum


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

bot = interactions.Client(
    token="ODIzNTUwNzAxMTk5ODE4NzYz.GJA5DJ.guxVG6sAX6Q3J9O1XZBTw90nXDUQ5Vd1w47l9o", intents=interactions.Intents.ALL)
GUILD_ID = 981965586844254208


@bot.command(
    name="statistics",
    description="parent command",
    scope=GUILD_ID,
    options=[
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
                    type=interactions.OptionType.BOOLEAN,
                    required=False,
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
    to_check = [(availability, Columns.AVAILABILITY),
                (pvp_cr, Columns.PVP_CR),
                (char_cr, Columns.CHAR_CR),
                (resonance, Columns.RESONANCE),
                (paragon_level, Columns.PARAGON_LEVEL),
                (paragon_tree, Columns.PARAGON_TREE),
                (build, Columns.BUILD)]

    #worksheet = in_a_clan(ctx)
    global worksheet

    await ctx.defer()
    if sub_command == "show":
        # name is of Member type if specified, think of it as "user"
        # i think some of this doesn't even fire but whatever
        if name == None:
            if results := user_exists(worksheet, ctx.author.name):
                await send_embed(ctx, results)
                return
            else:
                await ctx.send("That user doesn't exist!", ephemeral=True)
                return

        if results := user_exists(worksheet, name.name):
            for user in bot.guilds[2].members:
                if user.name == results[Columns.NAME]:
                    await send_embed(ctx, results)
                    return
        else:
            await ctx.send("That user doesn't exist!", ephemeral=True)
            return

    if sub_command == "set":
        if results := user_exists(worksheet, ctx.author.name):
            worksheet.update_value(
                f'{Columns.NAME}{results["ROW"]}', ctx.author.name)
            for stat in to_check:
                if stat[0] is not None:
                    worksheet.update_value(
                        f'{stat[1]}{results["ROW"]}', stat[0])
            await ctx.send('Updated!', ephemeral=True)
            return
        else:
            new_user = new_user_row(worksheet)
            worksheet.update_value(
                f'{Columns.NAME}{new_user}', ctx.author.name)
            for stat in to_check:
                if stat[0] is not None:
                    worksheet.update_value(f'{stat[1]}{new_user}', stat[0])
            await ctx.send('Updated!', ephemeral=True)
            return


async def send_embed(ctx, results):
    """
    Creates a pretty embed for the bot to send in the context provided
    """
    if results[Columns.AVAILABILITY] == 'TRUE':
        results[Columns.AVAILABILITY] = 'Yes'
    else:
        results[Columns.AVAILABILITY] = 'No'

    for key, value in results.items():
        if not value:
            results[key] = "Not Set"

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

    await ctx.send(embeds=embed)


def gc_init():
    """
    init pygsheets with service account and the stats spreadsheet.
    if it doesn't exist, create it.

    returns: sheet1 of stats to edit info
    """
    gc = pygsheets.authorize(service_file='.stats-updater.json')
    sh = None
    try:
        sh = gc.open('stats')
    except SpreadsheetNotFound as ex:
        print('stats spreadsheet not found, creating...')
        gc.create('stats')
        sh = gc.open('stats')
    wks = sh.sheet1
    return wks


def gc_nonclan_init():
    """
    init pygsheets with service account and the stats spreadsheet.
    if it doesn't exist, create it.

    returns: sheet1 of stats to edit info
    """
    gc = pygsheets.authorize(service_file='.stats-updater.json')
    sh = None
    try:
        sh = gc.open('stats_nonclan')
    except SpreadsheetNotFound as ex:
        print('stats_nonclan spreadsheet not found, creating...')
        gc.create('stats_nonclan')
        sh = gc.open('stats_nonclan')
    wks = sh.sheet1
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
        return None
    for thingy in found:
        for index, cell in enumerate(thingy):
            final[keys[index]] = cell.value

    final["ROW"] = row
    return final


def new_user_row(wks):
    """
    Finds an empty c1000 to use for a new user to enter stats
    """
    for the_list in wks.range('A2:A1000'):
        for cell in the_list:
            if cell.value == '':
                return cell.row


worksheet = gc_init()
worksheet_nonclan = gc_nonclan_init()
bot.start()
