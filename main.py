"""Shinwaffle

command: /stats
args:
availability: bool (self explanatory)
pvp CR: int
char sheet CR: int
resonance: int
paragon level: int
paragon tree: string 
build notes: string

on the sheet itself, it will show "nickname" and "discord name" first
then the args that were provided, cause yeah.

command: /exit
only for me, checks if its EXACTLY me and then "await client.close()"
to gracefully shut down the bot, prevents a lot of annoying backend work.

"inhouse player card", i have an idea of what they're talking about and
honestly? could pull it off tbh


first, find an api that is actually friendly to use with sheets
(if it exists with google keep then sheets for sure has one)

create a service account with it because you'll want to transport this
to the cloud, for obvious reasons.

once you can successfully retrieve the sheet's data, here is how this will work:

I am guessing with how slash commands work (and how you can have kwargs and shit)
is that you will get arguments in a dictionary. 
sort it just like it is above and then schmack that into a column. (horizontal thing)

but FIRST, you need to have a check routine.
(i was thinking about creating a cache but this api will NEVER be rate limited lmao)
grab the name from the second row (that is the real discord name)
and then match it
IF it matches:
    update the values (IF PROVIDED)
    spit out the updated values
    if no values provided: spit it back out at them
IF it doesn't:
    create a new entry
    spit out the new entry

"""
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
GUILD_ID = 832085929262055494  # priv


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
    global worksheet
    to_check = [(availability, Columns.AVAILABILITY),
                (pvp_cr, Columns.PVP_CR),
                (char_cr, Columns.CHAR_CR),
                (resonance, Columns.RESONANCE),
                (paragon_level, Columns.PARAGON_LEVEL),
                (paragon_tree, Columns.PARAGON_TREE),
                (build, Columns.BUILD)]

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

            for user in bot.guilds[1].members:
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
            resuts = user_exists(worksheet, ctx.author.name)
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

    embed = interactions.Embed(color=0xFF77FF)
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
    print('start init')
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
    print('done with init')
    return wks


def user_exists(wks, name):
    global keys
    print(f'starting lookup of {name}')
    """
    takes in worksheet object and finds given name. if it finds it, spit out related values
    """
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
    print(f'returning final {final}')
    return final


def new_user_row(wks):
    """
    Finds an empty column to use for a new user to enter stats
    """
    for the_list in wks.range('A2:A1000'):
        for cell in the_list:
            if cell.value == '':
                return cell.row


worksheet = gc_init()
bot.start()
