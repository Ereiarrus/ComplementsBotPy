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
            await ctx.channel.send(self.complement_msg(ctx))

    def choose_complement(self):
        return random.choice(self.COMPLEMENTS_LIST)

    def complement_msg(self, ctx):
        split_msg = ctx.content.split()
        who = ctx.author.name
        if len(split_msg) > 1:
            who = split_msg[1].strip()

        should_at = who[0] != "@"
        atted_user = who
        if should_at:
            atted_user = "@" + who
        return TTS_IGNORE_PREFIX + atted_user + " " + self.choose_complement()

    @commands.command()
    async def complement(self, ctx):
        await ctx.channel.send(self.complement_msg(ctx.message))


if __name__ == "__main__":
    bot = Bot()
    bot.run()
