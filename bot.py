# bot.py
from twitchio.ext import commands
import random
from database import *

CMD_PREFIX = '!'

BOT_NICK = "complementsbot"
OWNER_NICK = 'ereiarrus'


class Bot(commands.Bot):
    def __init__(self):
        join_channel(BOT_NICK)
        super().__init__(
            token=os.environ['TMI_TOKEN'],
            client_id=os.environ['CLIENT_ID'],
            nick=BOT_NICK,
            prefix=CMD_PREFIX,
            initial_channels=get_joined_channels()
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

        sender = ctx.author.name
        is_author_ignored = is_user_ignored(sender)
        should_rng_choose = (random.random() * 100) <= get_complement_chance(ctx.channel.name)
        is_author_bot = ignore_bots(sender) and len(sender) >= 3 and sender[-3:] == 'bot'

        if ctx.content[:len(CMD_PREFIX)] == CMD_PREFIX:
            await self.handle_commands(ctx)
        elif should_rng_choose \
                and (not is_author_ignored) \
                and not is_author_bot \
                and get_random_complement_enabled(ctx.channel.name):
            await ctx.channel.send(self.complement_msg(ctx, ctx.author.name, False))

    def choose_complement(self, ctx):
        channel = ctx.channel.name
        custom_complements = get_custom_complements(channel)
        if len(custom_complements) == 0 and len(self.COMPLEMENTS_LIST) == 0:
            return "", False

        default_complements_length = len(self.COMPLEMENTS_LIST)
        index = random.randint(0, default_complements_length + len(custom_complements) - 1)
        if index < default_complements_length:
            return self.COMPLEMENTS_LIST[index], True
        return custom_complements[index - default_complements_length], True

    def complement_msg(self, ctx, who=None, mute_tts=True):
        prefix = ""
        if who is None:
            who = ctx.author.name
        channel = ctx.channel.name
        prefix = "@" + prefix
        if mute_tts:
            prefix = get_tts_ignore_prefix(channel) + " " + prefix
        complement, exists = self.choose_complement(ctx)
        if exists:
            return prefix + who + " " + complement

    @commands.command()
    async def complement(self, ctx):
        msg = ctx.message.content.strip()
        args = msg.split(" ")
        who = ctx.message.author.name
        if len(args) > 1:
            who = " ".join(args[1:])
            if who[0] == "@":
                who = who[1:]

        if is_user_ignored(who) or not get_cmd_complement_enabled(ctx.channel.name):
            return

        await ctx.channel.send(self.complement_msg(ctx.message, who, True))

    # -------------------- bot channel only commands --------------------

    def make_sure_channel_joined(self):
        return


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
            await ctx.channel.send("@" + user + " I am already in your channel!")
        else:
            join_channel(user)
            await self.join_channels([user])
            await ctx.channel.send("@" + user + " I have joined your channel!")

    @commands.command()
    async def leaveme(self, ctx):
        # I will leave your channel
        if not Bot.is_in_bot_channel(ctx):
            return
        user = ctx.author.name
        if is_channel_joined(user):
            leave_channel(user)
            await self.part_channels([user])
            await ctx.channel.send("@" + user + " I have left your channel.")
        else:
            await ctx.channel.send("@" + user + " I have not joined your channel.")

    @commands.command()
    async def deleteme(self, ctx):
        # I will delete your channel information
        if not Bot.is_in_bot_channel(ctx):
            return
        user = ctx.author.name

        if channel_exists(user):
            delete_channel(user)
            await self.part_channels([user])
            await ctx.channel.send("@" + user + " I have deleted your channel data.")
        else:
            await ctx.channel.send("@" + user + " your channel does not exists in my records.")

    @commands.command()
    async def ignoreme(self, ctx):
        # no longer complement the user
        if not Bot.is_in_bot_channel(ctx):
            return

        user = ctx.author.name
        if is_user_ignored(user):
            await ctx.channel.send("@" + user + " I am already ignoring you.")
        else:
            ignore(user)
            await ctx.channel.send("@" + user + " I am now ignoring you.")

    @commands.command()
    async def unignoreme(self, ctx):
        # undo ignoreme
        if not Bot.is_in_bot_channel(ctx):
            return

        user = ctx.author.name
        if is_user_ignored(user):
            unignore(user)
            await ctx.channel.send("@" + user + " I am no longer ignoring you!")
        else:
            await ctx.channel.send("@" + user + " I am not ignoring you!")

    @commands.command()
    async def count(self, ctx):
        # see how many channels I'm in
        if not Bot.is_in_bot_channel(ctx):
            return
        await ctx.channel.send(
            "@" + ctx.message.author.name + " " + str(number_of_joined_channels()) + " channels and counting!")

    @commands.command()
    async def about(self, ctx):
        # learn all about me
        if not Bot.is_in_bot_channel(ctx):
            return
        await ctx.channel.send(
            "For most up-to-date information on commands, please have a look at "
            "https://github.com/Ereiarrus/ComplementsBotPy#readme and for most up-to-date complements, "
            "have a look at https://github.com/Ereiarrus/ComplementsBotPy/blob/main/complements_list.txt")

    # -------------------- any channel, but must be by owner --------------------

    @staticmethod
    def is_by_channel_owner(ctx):
        return ctx.channel.name == ctx.author.name

    @commands.command()
    async def setchance(self, ctx):
        # change how likely it is that person sending message gets complemented
        if not Bot.is_by_channel_owner(ctx):
            return

        user = ctx.channel.name
        msg = ctx.message.content.strip()
        chance = ""
        try:
            chance = (msg.split())[1]
            chance = float(chance)
        except ValueError:
            await ctx.channel.send("@" + user + " " + chance + " is an invalid number. Please try again.")
            return
        except IndexError:
            await ctx.channel.send("@" + user + " You did not enter a number. Please try again.")
            return
        set_complement_chance(user, chance)
        await ctx.channel.send("@" + user + " complement chance set to " + str(get_complement_chance(user)) + "!")

    @commands.command()
    async def disablecmdcomplement(self, ctx):
        # prevent users from being able to use the !complement command in your channel
        if not Bot.is_by_channel_owner(ctx):
            return
        user = ctx.channel.name
        if get_cmd_complement_enabled(user):
            disable_cmd_complement(user)
            await ctx.channel.send("@" + user + " your viewers will no longer be able to make use of the !complement command.")
        else:
            await ctx.channel.send("@" + user + " your viewers already cannot make use of the !complement command.")

    @commands.command()
    async def enablecmdcomplement(self, ctx):
        # undo !disablecmdcomplement
        if not Bot.is_by_channel_owner(ctx):
            return
        user = ctx.channel.name
        if get_cmd_complement_enabled(user):
            await ctx.channel.send("@" + user + " your viewers can already make use of the !complement command!")
        else:
            enable_cmd_complement(user)
            await ctx.channel.send(
                "@" + user + " your viewers will now be able to make use of the !complement command!")

    @commands.command()
    async def disablerandomcomplement(self, ctx):
        # the bot will no longer randomly give out complements
        if not Bot.is_by_channel_owner(ctx):
            return
        user = ctx.channel.name
        if get_random_complement_enabled(user):
            disable_random_complement(user)
            await ctx.channel.send("@" + user + " your viewers will no longer randomly receive complements.")
        else:
            await ctx.channel.send("@" + user + " your viewers already do not randomly receive complements.")

    @commands.command()
    async def enablerandomcomplement(self, ctx):
        # undo !disablerandomcomplement
        if not Bot.is_by_channel_owner(ctx):
            return
        user = ctx.channel.name
        if get_random_complement_enabled(user):
            await ctx.channel.send("@" + user + " I already randomly send out complements!")
        else:
            enable_random_complement(user)
            await ctx.channel.send(
                "@" + user + " your viewers will now randomly receive complements!")

    @commands.command()
    async def addcomplement(self, ctx):
        # add a custom complement for owner's channel
        if not Bot.is_by_channel_owner(ctx):
            return
        msg = ctx.message.content.strip()
        complement = msg[msg.find(" ") + 1:]
        user = ctx.channel.name
        add_complement(user, complement)
        await ctx.channel.send("@" + user + " new complements added: '" + complement + "'")

    @commands.command()
    async def listcomplements(self, ctx):
        # TODO
        # list all extra complements
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def removecomplement(self, ctx):
        # TODO
        # remove a custom complement
        if not Bot.is_by_channel_owner(ctx):
            return

    @commands.command()
    async def removeallcomplements(self, ctx):
        # TODO
        # remove all custom complements a user has added
        if not Bot.is_by_channel_owner(ctx):
            return
        user = ctx.channel.name
        remove_all_complements(user)
        await ctx.channel.send("@" + user + " all of your custom complements have been removed.")


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


if __name__ == "__main__":
    bot = Bot()
    bot.run()
