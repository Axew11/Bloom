import discord, asyncio, random, os
from discord.ext import commands
from colour import Color
import sqlite3, logging

logging.basicConfig (
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

DiscordToken = 'NzYxNDgxNjYzODAwNTQxMjE0.X3bPEA.z0DqDKN2dvPk2LK6BwR7R9wiJvU'
bot = commands.Bot(command_prefix='+')
camellia = Color("#d47fb9")
colors = list(camellia.range_to(Color("#000000"), 100))
colors.reverse()
jobs = [("Healer"), ("Warrior"), ("Spellcaster"), ("Potionsmaker")]

database = sqlite3.connect('players.db')

c = database.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS players (
            id integer,
            name text,
            petals integer DEFAULT 0,
            stems integer DEFAULT 0,
            leaves integer DEFAULT 0,
            flowers integer DEFAULT 0,
            credits integer DEFAULT 0,
            karma integer DEFAULT 100
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS globals (
            season integer,
            entropy REAL DEFAULT 0
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS attributes (
            id integer,
            name text,
            strength integer DEFAULT 1,
            dexterity integer DEFAULT 1,
            intellect integer DEFAULT 1,
            charisma integer DEFAULT 1
            )""")

class Player:
    def __init__(self, data):
        (self.id, self.name, self.petals, self.stems, self.leaves, self.flowers, self.credits, self.karma) = data
class Attributes:
    def __init__(self, data):
        (self.id, self.name, self.strength, self.dexerity, self.intellect, self.charisma) = data
class Global:
    def __init__(self, data):
        (self.season, self.entropy) = data

async def add_gather(ID, result, petals, leaves, stems):
    c.execute("SELECT * FROM players WHERE id=?", (ID,))
    in_database = c.fetchone()
    if not in_database:
        c.execute("INSERT INTO players (id, name) VALUES (:id, :name)", {'id': ID, 'name':result})
        c.execute("INSERT INTO attributes (id, name) VALUES (:id, :name)", {'id': ID, 'name':result})
        database.commit()
        c.execute("SELECT * FROM players WHERE id=?", (ID,))
        in_database = c.fetchone()
    player = Player(in_database)
    c.execute("UPDATE players SET petals = :petals, stems = :stems, leaves = :leaves WHERE id = :id", {'id': player.id, 'petals': player.petals + petals, 'stems': player.stems + stems, 'leaves': player.leaves + leaves})
    database.commit()
    del player

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="+help"))
    c.execute("SELECT * FROM globals WHERE season=?", (1,))
    in_database = c.fetchone()
    if not in_database:
        c.execute("INSERT INTO globals (season) VALUES (:season)", {'season': 1})
        database.commit()
    logging.info("Connected Bloom to Discord.")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        result = ''.join(filter(str.isalpha, message.author.name))
        await message.channel.send(f"Hello {result}.")

    await bot.process_commands(message)

@bot.command()
async def test(ctx):
    await ctx.send("Test.")


@bot.command()
async def gather(ctx):
    petals = random.randint(3, 5)
    leaves = random.randint(2, 4)
    stems = random.randint(0, 1)
    result = ''.join(filter(str.isalpha, ctx.author.name))
    if result == "Genin":
        result = "Axew"
    await add_gather(ctx.author.id, result, petals,leaves, stems)
    embed = discord.Embed(description=f"You gathered {petals} petals, {stems} stem(s), and {leaves} leaves.", color=0xd47fb9)
    embed.set_author(name=result, icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)


@bot.command()
async def materials(ctx):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM players WHERE id=?", (ctx.author.id,))
    temp = c.fetchone()
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
        return
    player = Player(temp)
    embed = discord.Embed(title="Materials", color=discord.Color(int(Color.get_hex(colors[player.karma - 1]).strip('#'), 16)))
    embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="Petals", value=player.petals)
    embed.add_field(name="Stems", value=player.stems)
    embed.add_field(name="Leaves", value=player.leaves)
    embed.add_field(name="Flowers", value=player.flowers)
    embed.add_field(name="Karma", value=player.karma)
    await ctx.send(embed=embed)
    del player

@bot.command()
async def craft(ctx):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM players WHERE id=?", (ctx.author.id,))
    temp = c.fetchone()
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
        return
    player = Player(temp)
    embed = discord.Embed(color=0xd47fb9)
    embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
    if player.petals >= 10 and player.leaves >= 4 and player.stems >= 1:
        await add_gather(ctx.author.id, player.name, -10, -4, -1)
        if player.karma + 1 > 100:
            player.karma = 100
        else:
            player.karma += 1
        c.execute("UPDATE players SET flowers = :flowers, karma = :karma WHERE id = :id",
                  {'id': player.id, 'flowers': player.flowers + 1, 'karma': player.karma})
        database.commit()
        embed.description = f"You crafted 1 camellia {result}. Gained 3 karma points."
        c.execute("SELECT COUNT(*) FROM players")
        people = len(c.fetchall())
        c.execute("SELECT * FROM globals WHERE season=?", (1,))
        globalvar = Global(c.fetchone())
        c.execute("UPDATE globals SET entropy = :entropy WHERE season = 1",
                  {'entropy': float(globalvar.entropy - 1 / people)})
        database.commit()
    else:
        embed.description = f"You don't have enough materials to craft a camellia."
    await ctx.send(embed=embed)
    del player

@bot.command()
async def crime(ctx):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM players WHERE id=?", (ctx.author.id,))
    temp = c.fetchone()
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
        return
    player = Player(temp)
    embed = discord.Embed(color=0x000000)
    embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
    credits = random.randint(10, 15)
    if player.karma > 20:
        player.karma -= 20
        embed.description = f"You stole {credits} credits from a local shop. You feel a sense of paranoia. Lost 20 karma points."
    else:
        embed.description = "No."
        await ctx.send(embed=embed)
        del player
        return
    if player.flowers > 0:
        player.flowers -= 1
        c.execute("SELECT COUNT(*) FROM players")
        people = len(c.fetchall())
        c.execute("SELECT * FROM globals WHERE season=?", (1,))
        globalvar = Global(c.fetchone())
        c.execute("UPDATE globals SET entropy = :entropy WHERE season = 1", {'entropy': float(globalvar.entropy + 1/people)})
        database.commit()
        embed.description = f"You stole {credits} credits from a local shop and a flower becomes corrupted. You feel a sense of paranoia. Lost 20 karma points."
        del globalvar
    c.execute("UPDATE players SET karma = :karma, flowers = :flowers, credits = :credits WHERE id = :id",
              {'id': player.id, 'karma': player.karma, 'flowers': player.flowers, 'credits': player.credits})
    database.commit()
    await ctx.send(embed=embed)
    del player

@bot.command()
async def sell(ctx):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM players WHERE id=?", (ctx.author.id,))
    temp = c.fetchone()
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
        return
    player = Player(temp)
    if player.flowers > 0:
        player.flowers -= 1
        player.credits += 1
        c.execute("UPDATE players SET flowers = :flowers, credits = :credits WHERE id = :id", {'flowers': player.flowers, 'credits': player.credits, 'id':player.id})
        database.commit()
        embed = discord.Embed(description="You sold a camellia for one credit.", color=discord.Color(0xd47fb9))
        embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description="You do not have any camellias to sell.", color=discord.Color(0xd47fb9))
        embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
    del player, embed, temp

@bot.command()
async def nickname(ctx, name):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM players WHERE id=?", (ctx.author.id,))
    temp = c.fetchone()
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
    c.execute("UPDATE players SET name = :name WHERE id = :id", {'id': ctx.author.id, 'name': name})
    database.commit()
    await ctx.send(embed=discord.Embed(description=f"Changed your name to {name}.", color=discord.Color(0xd47fb9)))

@bot.command()
async def entropy(ctx):
    c.execute("SELECT * FROM globals WHERE season=1")
    globalvar = Global(c.fetchone())
    if globalvar.entropy > 0:
        await ctx.send(embed=discord.Embed(description="There is positive entropy in the world, frightening the people.", color=discord.Color(0x000000)))
    elif globalvar.entropy < 0:
        await ctx.send(embed=discord.Embed(description="There is negative entropy in the world, creating happiness amongst the people.", color=discord.Color(0xd47fb9)))
    else:
        await ctx.send(embed=discord.Embed(description="There is entropy in the world, not positive, nor negative.", color=discord.Color(0xd47fb9)))
    del globalvar

@bot.command()
async def credits(ctx):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM players WHERE id=?", (ctx.author.id,))
    temp = c.fetchone()
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
        return
    player = Player(temp)
    embed = discord.Embed(description=f"You have {player.credits} credits.", color=discord.Color(0xd47fb9))
    embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
    if player.credits == 1:
        embed.description = "You have 1 credit."
    await ctx.send(embed=embed)
    del player, embed, temp

@bot.command()
async def attributes(ctx):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM attributes WHERE id=:id", {'id': ctx.author.id})
    temp = c.fetchone()
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
        return
    player = Attributes(temp)
    embed = discord.Embed(title="Attributes", color=discord.Color(0xd47fb9))
    embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="Strength", value=player.strength, inline=True)
    embed.add_field(name="Dexterity", value=player.dexerity, inline=True)
    embed.add_field(name="Intellect", value=player.intellect, inline=True)
    embed.add_field(name="Charisma", value=player.charisma, inline=True)
    await ctx.send(embed=embed)
    del player, embed, temp

@bot.command()
async def apply(ctx):
    result = ''.join(filter(str.isalpha, ctx.author.name))
    c.execute("SELECT * FROM attributes WHERE id=:id", {'id': ctx.author.id})
    temp = c.fetchone()
    applied = False
    if temp is None:
        await ctx.send(embed=discord.Embed(description=f"Wake up first {result}."))
        return
    attribute = Attributes(temp)
    page = 0
    embed = discord.Embed(title=f"Jobs {page + 1}/{len(jobs)}: {jobs[page][0]}", description="Test.", color=discord.Color(0xd47fb9))
    embed.set_author(name=attribute.name, icon_url=ctx.author.avatar_url)
    message = await ctx.send(embed=embed)
    await message.add_reaction("◀")
    await message.add_reaction("▶")
    await message.add_reaction("<:confirm:763798145263730768>")
    await asyncio.sleep(1)

    def check(reaction, author):
        return reaction.message.id == message.id and author == ctx.author and str(reaction) in ("◀", "▶", "<:confirm:763798145263730768>")

    while True:
        try:
            reaction, author = await ctx.bot.wait_for('reaction_add', check=check, timeout=15.0)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            embed.title, embed.description = "Timeout.", ""
            await message.edit(embed=embed)
            break
        if str(reaction) == "◀":
            page = (page - 1) if page != 0 else 0
        elif str(reaction) == "▶":
            page = (page + 1) if page != (len(jobs) - 1) else (len(jobs) - 1)
        elif str(reaction) == "<:confirm:763798145263730768>":
            applied = True
            await message.delete()
            break
        else:
            logging.error("Reaction broke in apply command.")
            break
        embed.title = f"Jobs {page + 1}/{len(jobs)}: {jobs[page][0]}"
        await message.edit(embed=embed)


    if applied:
        embed = discord.Embed(title=f"{jobs[page]}", description="Would you like to apply?", color=discord.Color(0xd47fb9))
        embed.set_author(name=attribute.name, icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)
        await message.add_reaction("<:confirm:763798145263730768>")
        await message.add_reaction("<:cancel:763804797916282940>")
        await asyncio.sleep(1)

        def check(reaction, author):
            return reaction.message.id == message.id and author == ctx.author and str(reaction) in ("<:confirm:763798145263730768>", "<:cancel:763804797916282940>")

        try:
            reaction, author = await ctx.bot.wait_for('reaction_add', check=check, timeout=15.0)
            if str(reaction) == "<:confirm:763798145263730768>":
                await message.delete()
                await ctx.send(
                    embed=discord.Embed(title=f"{jobs[page][0]}", description=f"You applied for to be a {jobs[page][0]}",
                                        color=discord.Color(0xd47fb9)))
            elif str(reaction) == "<:cancel:763804797916282940>":
                await message.delete()
                await ctx.send(
                    embed=discord.Embed(title=f"{jobs[page][0]}", description=f"You did not apply to be a {jobs[page][0]}",
                                        color=discord.Color(0xd47fb9)))
            else:
                logging.error("Reaction broke in apply (Apply verification) command.")
        except asyncio.TimeoutError:
            await message.clear_reactions()
            embed.title, embed.description = "Timeout.", ""
            await message.edit(embed=embed)

@bot.command()
async def delete(ctx):
    c.execute("DELETE FROM players WHERE id = :id", {'id': ctx.author.id})

bot.run(DiscordToken)