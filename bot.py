# bot.py
import os  # for importing env vars for the bot to use
from twitchio.ext import commands
import random

TTS_IGNORE_PREFIX = os.environ['TTS_IGNORE_PREFIX']


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ['TMI_TOKEN'],
            client_id=os.environ['CLIENT_ID'],
            nick=os.environ['BOT_NICK'],
            prefix=os.environ['BOT_PREFIX'],
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
        print("in msg")

        # make sure the bot ignores itself
        if ctx.echo:
            return

        print(ctx.content)
        await self.handle_commands(ctx)

    def choose_complement(self):
        return random.choice(self.COMPLEMENTS_LIST)

    @commands.command()
    async def complement(self, ctx):
        split_msg = ctx.message.content.split()
        who = ctx.author.name
        if len(split_msg) > 1:
            who = split_msg[1].strip()

        should_at = who[0] != "@"
        atted_user = who
        if should_at:
            atted_user = "@" + who
        await ctx.send(TTS_IGNORE_PREFIX + atted_user + " " + self.choose_complement())


if __name__ == "__main__":
    bot = Bot()
    bot.run()
