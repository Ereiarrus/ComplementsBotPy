# bot.py
import os  # for importing env vars for the bot to use
from twitchio.ext import commands

bot = commands.Bot(
    # bot setup
    token=os.environ['TMI_TOKEN'],
    client_id=os.environ['CLIENT_ID'],
    nick=os.environ['BOT_NICK'],
    prefix=os.environ['BOT_PREFIX'],
    initial_channels=[os.environ['CHANNEL']]
)


@bot.event
async def event_ready():
    # Called once when the bot goes online.
    print(f"{os.environ['BOT_NICK']} is online!")
    ws = bot._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(os.environ['CHANNEL'], f"/me has landed!")


@bot.event
async def event_message(ctx):
    # Runs every time a message is sent in chat.

    # make sure the bot ignores itself and the streamer
    if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
        return

    print(ctx.content)
    await ctx.send(ctx.content)
    # await bot.handle_commands(ctx)


# @bot.command(name='test')
# async def test(ctx):
#     print("woot!")
#     await ctx.send('test passed!')
#
#
# @bot.command(name='asdf')
# async def asdf(ctx):
#     print("asdf!")
#     await ctx.send('asdf passed!')


if __name__ == "__main__":
    bot.run()
