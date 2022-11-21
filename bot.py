# bot.py
import os  # for importing env vars for the bot to use
from twitchio.ext import commands
import random
from ReadWriteLock import ReadWriteLock
from threading import RLock
import json  # json.dumps(dictionary, separators=(',', ':'))

DEFAULT_CMD_PREFIX = '!'
DEFAULT_TTS_IGNORE_PREFIX = "!"
OWNER_NICK = 'ereiarrus'
BOT_NICK = "complementsbot"
DEFAULT_COMPLEMENT_CHANCE = 10.0 / 3.0

custom_data = {"channel_name":
                   {"cmd_prefix": "!", "tts_ignore_prefix": "! ", "complement_chance": 10.0 / 3.0,
                    "extra_complements": []}}

channels_to_join_lock = RLock()
CHANNELS_TO_JOIN = set(os.environ['CHANNELS'].split(':'))

ignored_users_lock = RLock()
IGNORED_USERS = set(os.environ['IGNORED_USERS'].split(':'))
IGNORED_USERS.remove('')  # for some reason the empty string can make its way in if IGNORED_USERS is empty


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ['TMI_TOKEN'],
            client_id=os.environ['CLIENT_ID'],
            nick=BOT_NICK,
            prefix=DEFAULT_CMD_PREFIX,
            initial_channels=list(CHANNELS_TO_JOIN)
        )
        self.COMPLEMENTS_LIST = []
        with open("complements_list.txt", "r") as f:
            for line in f:
                self.COMPLEMENTS_LIST.append(line.strip())

    async def event_ready(self):
        # Called once when the bot goes online.
        print(f"{BOT_NICK} is online!")

    async def event_message(self, ctx):
        # Runs every time a message is sent in chat.
        if ctx.echo:
            # make sure the bot ignores itself
            return

        if ctx.content[:len(DEFAULT_CMD_PREFIX)] == DEFAULT_CMD_PREFIX:
            await self.handle_commands(ctx)
        elif (random.random() * 100) <= DEFAULT_COMPLEMENT_CHANCE and (not (ctx.author.name in IGNORED_USERS)):
            await ctx.channel.send(self.complement_msg(ctx, ctx.author.name, False))

    def choose_complement(self):
        return random.choice(self.COMPLEMENTS_LIST)

    def complement_msg(self, ctx, who=None, mute_tts=True):
        split_msg = ctx.content.split()
        prefix = ""
        if not who:
            who = ctx.author.name
        prefix = "@" + prefix
        if mute_tts:
            prefix = DEFAULT_TTS_IGNORE_PREFIX + " " + prefix
        return prefix + who + " " + self.choose_complement()

    @commands.command()
    async def complement(self, ctx):
        msg = ctx.message.content.strip()
        args = msg.split(" ")
        who = ctx.message.author.name
        if len(args) > 1:
            who = " ".join(args[1:])
            if who[0] == "@":
                who = who[1:]
        if who in IGNORED_USERS:
            return
        await ctx.channel.send(self.complement_msg(ctx.message, who, True))

    # -------------------- bot channel only commands --------------------

    @staticmethod
    def is_in_bot_channel(ctx):
        return ctx.channel.name == BOT_NICK or ctx.channel.name == OWNER_NICK

    @commands.command()
    async def joinme(self, ctx):
        # I will join your channel!
        if not self.is_in_bot_channel(ctx):
            return
        try:
            channels_to_join_lock.acquire()
        except Exception as e:
            raise e
        finally:
            channels_to_join_lock.release()

    @commands.command()
    async def leaveme(self, ctx):
        # I will leave your channel
        if not self.is_in_bot_channel(ctx):
            return
        try:
            channels_to_join_lock.acquire()
        except Exception as e:
            raise e
        finally:
            channels_to_join_lock.release()

    @commands.command()
    async def about(self, ctx):
        # learn all about me
        if not self.is_in_bot_channel(ctx):
            return

    @commands.command()
    async def count(self, ctx):
        # see how many channels I'm in
        if not self.is_in_bot_channel(ctx):
            return
        await ctx.channel.send(
            "@" + ctx.message.author.name + " " + str(len(CHANNELS_TO_JOIN)) + " channels and counting!")

    @commands.command()
    async def ignoreme(self, ctx):
        # no longer complement the user
        if not self.is_in_bot_channel(ctx):
            return
        try:
            ignored_users_lock.acquire()
            user = ctx.author.name
            IGNORED_USERS.add(user)
            # TODO: the line below can probably be ran periodically instead of on every !ignoreme
            os.environ["IGNORED_USERS"] = ':'.join(IGNORED_USERS)
        except Exception as e:
            raise e
        finally:
            ignored_users_lock.release()

    @commands.command()
    async def unignoreme(self, ctx):
        # undo ignoreme
        if not self.is_in_bot_channel(ctx):
            return
        try:
            ignored_users_lock.acquire()
            IGNORED_USERS.remove(ctx.author.name)
            # TODO: the line below can probably be ran periodically instead of on every !unignoreme
            os.environ["IGNORED_USERS"] = ':'.join(IGNORED_USERS)
        except Exception as e:
            raise e
        finally:
            ignored_users_lock.release()

    # -------------------- any channel, but must be by owner --------------------

    @staticmethod
    def is_by_channel_owner(ctx):
        return ctx.channel.name == ctx.author.name

    @commands.command()
    async def setchance(self, ctx):
        # change how likely it is that person sending message gets complemented
        if not self.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def addcomplement(self, ctx):
        # add a custom complement for owner's channel
        if not self.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def removecomplement(self, ctx):
        # remove a custom complement
        if not self.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def listcomplements(self, ctx):
        # list all extra complements
        if not self.is_by_channel_owner(ctx):
            return


if __name__ == "__main__":
    bot = Bot()
    bot.run()
