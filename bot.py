# bot.py
import os  # for importing env vars for the bot to use
from twitchio.ext import commands
import random

CMD_PREFIX = os.environ['BOT_PREFIX']
TTS_IGNORE_PREFIX = os.environ['TTS_IGNORE_PREFIX']
COMPLEMENT_CHANCE = 5


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ['TMI_TOKEN'],
            client_id=os.environ['CLIENT_ID'],
            nick=os.environ['BOT_NICK'],
            prefix=CMD_PREFIX,
            initial_channels=[os.environ['CHANNEL']]
        )
        self.COMPLEMENTS_LIST = []
        with open("complements_list.txt", "r") as f:
            for line in f:
                self.COMPLEMENTS_LIST.append(line.strip())

    async def event_ready(self):
        # Called once when the bot goes online.
        print(f"{os.environ['BOT_NICK']} is online!")

    async def event_message(self, ctx):
        # Runs every time a message is sent in chat.
        if ctx.echo:
            # make sure the bot ignores itself
            return

        if ctx.content[:len(CMD_PREFIX)] == CMD_PREFIX:
            await self.handle_commands(ctx)
        elif (random.random() * 100) <= COMPLEMENT_CHANCE:
            await ctx.channel.send(self.complement_msg(ctx, ctx.author.name))

    def choose_complement(self):
        return random.choice(self.COMPLEMENTS_LIST)

    def complement_msg(self, ctx, who=None):
        split_msg = ctx.content.split()

        if not who:
            who = ctx.author.name

        should_at = who[0] != "@"
        atted_user = who
        if should_at:
            atted_user = "@" + who
        return TTS_IGNORE_PREFIX + atted_user + " " + self.choose_complement()

    @commands.command()
    async def complement(self, ctx):
        msg = ctx.message.content.strip()
        args = msg.split()
        who = ctx.message.author.name
        if len(args) > 1:
            who = args[1]
        await ctx.channel.send(self.complement_msg(ctx.message, who))

    # -------------------- bot channel only commands --------------------
    @commands.command()
    async def joinme(self, ctx):
        # I will join your channel!
        pass

    @commands.command()
    async def leaveme(self, ctx):
        # I will leave your channel
        pass

    @commands.command()
    async def about(self, ctx):
        # learn all about me
        pass

    @commands.command()
    async def count(self, ctx):
        # see how many channels I'm in
        pass

    @commands.command()
    async def ignoreme(self, ctx):
        # no longer complement the user
        pass

    @commands.command()
    async def unignoreme(self, ctx):
        # undo ignoreme
        pass

    # -------------------- any channel, but must be by owner --------------------

    @commands.command()
    async def setchance(self, ctx):
        # change how likely it is that person sending message gets complemented
        pass

    @commands.command()
    async def addcomplement(self, ctx):
        # add a custom complement for owner's channel
        pass

    @commands.command()
    async def removecomplement(self, ctx):
        # remove a custom comple
        pass

    @commands.command()
    async def listcomplements(self, ctx):
        # see how many channels I'm in
        pass


if __name__ == "__main__":
    bot = Bot()
    bot.run()
