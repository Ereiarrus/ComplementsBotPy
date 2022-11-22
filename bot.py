# bot.py
import os
from twitchio.ext import commands
import random
from database import *


CMD_PREFIX = '!'

BOT_NICK = "complementsbot"
OWNER_NICK = 'ereiarrus'


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ['TMI_TOKEN'],
            client_id=os.environ['CLIENT_ID'],
            nick=BOT_NICK,
            prefix=CMD_PREFIX,
            initial_channels=get_joined_channels()+[BOT_NICK]
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

        print(get_chance(ctx.channel.name))
        user = ctx.author.name
        is_author_ignored = is_user_ignored(user)
        should_rng_choose = (random.random() * 100) <= DEFAULT_COMPLEMENT_CHANCE
        if is_channel_joined(ctx.channel.name):
            should_rng_choose = (random.random() * 100) <= get_chance(ctx.channel.name)
        is_author_bot = ignore_bots(user) and len(user) >= 3 and user[-3:] == 'bot'

        if ctx.content[:len(CMD_PREFIX)] == CMD_PREFIX:
            await self.handle_commands(ctx)
        elif should_rng_choose and (not is_author_ignored) and not is_author_bot:
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
            prefix = get_tts_ignore_prefix(who) + " " + prefix
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

        if is_user_ignored(who):
            return

        await ctx.channel.send(self.complement_msg(ctx.message, who, True))

    # -------------------- bot channel only commands --------------------

    @staticmethod
    def is_in_bot_channel(ctx):
        return ctx.channel.name == BOT_NICK or ctx.channel.name == OWNER_NICK

    @commands.command()
    async def joinme(self, ctx):
        # I will join your channel!
        if not Bot.is_in_bot_channel(ctx):
            return
        user = ctx.author.name

        if is_channel_joined(user):
            await ctx.channel.send("@" + user + " ComplementsBot has is already in your channel!")
        else:
            join_channel(user)
            await ctx.channel.send("@" + user + " ComplementsBot has joined your channel!")

    @commands.command()
    async def leaveme(self, ctx):
        # I will leave your channel
        if not Bot.is_in_bot_channel(ctx):
            return
        user = ctx.author.name
        if is_channel_joined(user):
            leave_channel(user)
            await ctx.channel.send("@" + user + " ComplementsBot has left your channel.")
        else:
            await ctx.channel.send("@" + user + " ComplementsBot has is not joined.")


    @commands.command()
    async def deleteme(self, ctx):
        # I will delete your channel information
        if not Bot.is_in_bot_channel(ctx):
            return
        user = ctx.author.name

        if channel_exists(user):
            delete_channel(user)
            await ctx.channel.send("@" + user + " ComplementsBot has deleted your channel.")
        else:
            await ctx.channel.send("@" + user + " your channel does not exists in my records.")


    @commands.command()
    async def about(self, ctx):
        # learn all about me
        if not Bot.is_in_bot_channel(ctx):
            return
        await ctx.channel.send(
            "For most up-to-date information on commands, please have a look at "
            "https://github.com/Ereiarrus/ComplementsBotPy#readme and for most up-to-date complements, "
            "have a look at https://github.com/Ereiarrus/ComplementsBotPy/blob/main/complements_list.txt")

    @commands.command()
    async def count(self, ctx):
        # see how many channels I'm in
        if not Bot.is_in_bot_channel(ctx):
            return
        await ctx.channel.send(
            "@" + ctx.message.author.name + " " + str(len(number_of_joined_channels())) + " channels and counting!")

    @commands.command()
    async def ignoreme(self, ctx):
        # no longer complement the user
        if not Bot.is_in_bot_channel(ctx):
            return

        user = ctx.author.name
        if is_user_ignored(user):
            await ctx.channel.send("@" + user + " ComplementsBot is already ignoring you.")
        else:
            ignore(user)
            await ctx.channel.send("@" + user + " ComplementsBot is now ignoring you.")

    @commands.command()
    async def unignoreme(self, ctx):
        # undo ignoreme
        if not Bot.is_in_bot_channel(ctx):
            return

        user = ctx.author.name
        if is_user_ignored(user):
            unignore(user)
            await ctx.channel.send("@" + user + " ComplementsBot is no longer ignoring you!")
        else:
            await ctx.channel.send("@" + user + " ComplementsBot is not ignoring you!")


    # -------------------- any channel, but must be by owner --------------------

    @staticmethod
    def is_by_channel_owner(ctx):
        return ctx.channel.name == ctx.author.name

    @commands.command()
    async def setchance(self, ctx):
        # TODO
        # change how likely it is that person sending message gets complemented
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def addcomplement(self, ctx):
        # TODO
        # add a custom complement for owner's channel
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def removecomplement(self, ctx):
        # TODO
        # remove a custom complement
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def listcomplements(self, ctx):
        # TODO
        # list all extra complements
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def setmutettsprefix(self, ctx):
        # TODO
        # the character/string to put in front of a message to mute tts
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def mutecmdcomplement(self, ctx):
        # TODO
        # mutes tts for complements sent with !complement command
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def muterandomcomplement(self, ctx):
        # TODO
        # mutes tts for complements randomly given out
        if not Bot.is_by_channel_owner(ctx):
            return

    # TODO: When a user calls a command on my channel, respond to tell them that command was done


if __name__ == "__main__":
    bot = Bot()
    bot.run()
