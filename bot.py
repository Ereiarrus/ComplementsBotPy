# bot.py
from twitchio.ext import commands
import random
from database import *

#TODO:
# allow streamers to toggle which commands can/cannot be used by mods/VIPs/subs/everyone.
# allow streamers to control which user groups can receive which complements
# when people try complementing the bot, say something different
# when people reply to bot (e.g. say thank you), say something different
# |
# make a website where users can see all of their info
# make a docker container for app
# deploy app to firebase
# set up database with data type rules

CMD_PREFIX = '!'

BOT_NICK = "complementsbot"
OWNER_NICK = 'ereiarrus'

SHOULD_LOG = False


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
        # Called once when the bot goes online.]
        if SHOULD_LOG:
            print(f"{BOT_NICK} is online!")

    async def event_message(self, ctx):
        # Runs every time a message is sent in chat.
        if ctx.echo:
            # make sure the bot ignores itself
            return

        sender = ctx.author.name
        channel = ctx.channel.name
        is_author_ignored = is_user_ignored(sender)
        should_rng_choose = (random.random() * 100) <= get_complement_chance(ctx.channel.name)
        is_author_bot = is_ignoring_bots(channel) and len(sender) >= 3 and sender[-3:] == 'bot'

        if ctx.content[:len(CMD_PREFIX)] == CMD_PREFIX:
            await self.handle_commands(ctx)
        if should_rng_choose \
                and (not is_author_ignored) \
                and not is_author_bot \
                and get_random_complement_enabled(ctx.channel.name):
            comp_msg, exists = self.complement_msg(ctx, ctx.author.name, is_random_complement_muted(channel))
            if exists:
                await ctx.channel.send(comp_msg)

    def choose_complement(self, ctx):
        channel = ctx.channel.name
        custom_complements = []
        if are_custom_complements_enabled(channel):
            custom_complements = get_custom_complements(channel)
        default_complements = []
        if are_default_complements_enabled(channel):
            default_complements = self.COMPLEMENTS_LIST

        if len(custom_complements) == 0 and len(default_complements) == 0:
            return "", False

        default_complements_length = len(default_complements)
        index = random.randint(0, default_complements_length + len(custom_complements) - 1)
        if index < default_complements_length:
            return default_complements[index], True
        return custom_complements[index - default_complements_length], True

    def complement_msg(self, ctx, who=None, is_tts_muted=True):
        prefix = ""
        if who is None:
            who = ctx.author.name
        channel = ctx.channel.name
        prefix = "@" + prefix
        if is_tts_muted:
            prefix = get_tts_ignore_prefix(channel) + " " + prefix
        complement, exists = self.choose_complement(ctx)
        return prefix + who + " " + complement, exists

    @commands.command()
    async def complement(self, ctx):
        msg = ctx.message.content.strip()
        args = msg.split(" ")
        who = ctx.message.author.name
        if len(args) > 1:
            who = " ".join(args[1:])
            if who[0] == "@":
                who = who[1:]

        channel = ctx.channel.name
        if is_user_ignored(who) or not get_cmd_complement_enabled(channel):
            return

        comp_msg, exists = self.complement_msg(ctx.message, who, is_cmd_complement_muted(channel))
        if exists:
            await ctx.channel.send(comp_msg)

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
    def is_by_broadcaster_or_mod(ctx):
        return ctx.author.is_broadcaster \
               or ctx.author.is_mod() \
               or ctx.author.name == BOT_NICK \
               or ctx.author.name == OWNER_NICK

    @commands.command()
    async def setchance(self, ctx):
        # change how likely it is that person sending message gets complemented
        if not Bot.is_by_broadcaster_or_mod(ctx):
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
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        user = ctx.channel.name
        if get_cmd_complement_enabled(user):
            disable_cmd_complement(user)
            await ctx.channel.send(
                "@" + user + " your viewers will no longer be able to make use of the !complement command.")
        else:
            await ctx.channel.send("@" + user + " your viewers already cannot make use of the !complement command.")

    @commands.command()
    async def enablecmdcomplement(self, ctx):
        # undo !disablecmdcomplement
        if not Bot.is_by_broadcaster_or_mod(ctx):
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
        if not Bot.is_by_broadcaster_or_mod(ctx):
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
        if not Bot.is_by_broadcaster_or_mod(ctx):
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
        if not Bot.is_by_broadcaster_or_mod(ctx):
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
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

    @commands.command()
    async def removecomplement(self, ctx):
        # TODO
        # remove a custom complement
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

    @commands.command()
    async def removeallcomplements(self, ctx):
        # remove all custom complements a user has added
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        user = ctx.channel.name
        remove_all_complements(user)
        await ctx.channel.send("@" + user + " all of your custom complements have been removed.")

    @commands.command()
    async def setmutettsprefix(self, ctx):
        # the character/string to put in front of a message to mute tts
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name
        msg = ctx.message.content
        msg = msg.strip()
        prefix = msg[msg.find(" ") + 1:]
        set_mute_prefix(channel, prefix)
        await ctx.channel.send("@" + channel + " mute TTS prefix changed to '" + prefix + "'.")

    @commands.command()
    async def mutecmdcomplement(self, ctx):
        # mutes tts for complements sent with !complement command
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_cmd_complement_muted(channel):
            await ctx.channel.send("@" + channel + " command complements are already muted!")
        else:
            mute_cmd_complement(channel)
            await ctx.channel.send("@" + channel + " command complements are now muted.")

    @commands.command()
    async def muterandomcomplement(self, ctx):
        # mutes tts for complements randomly given out
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_random_complement_muted(channel):
            await ctx.channel.send("@" + channel + " random complements are already muted!")
        else:
            mute_random_complement(channel)
            await ctx.channel.send("@" + channel + " random complements are now muted.")

    @commands.command()
    async def unmutecmdcomplement(self, ctx):
        # unmutes tts for complements sent with !complement command
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_cmd_complement_muted(channel):
            unmute_cmd_complement(channel)
            await ctx.channel.send("@" + channel + " command complements are no longer muted!")
        else:
            await ctx.channel.send("@" + channel + " command complements are already unmuted!")

    @commands.command()
    async def unmuterandomcomplement(self, ctx):
        # unmutes tts for complements randomly given out
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_random_complement_muted(channel):
            unmute_random_complement(channel)
            await ctx.channel.send("@" + channel + " random complements are no longer muted!")
        else:
            await ctx.channel.send("@" + channel + " random complements are already unmuted!")

    @commands.command()
    async def enablecustomcomplements(self, ctx):
        # custom complements will now be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if not are_custom_complements_enabled(channel):
            enable_custom_complements(channel)
            await ctx.channel.send("@" + channel + " custom complements are now enabled!")
        else:
            await ctx.channel.send("@" + channel + " custom complements are already enabled!")

    @commands.command()
    async def enabledefaultcomplements(self, ctx):
        # custom complements will now be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if not are_default_complements_enabled(channel):
            enable_default_complements(channel)
            await ctx.channel.send("@" + channel + " default complements are now enabled!")
        else:
            await ctx.channel.send("@" + channel + " default complements are already enabled!")

    @commands.command()
    async def disablecustomcomplements(self, ctx):
        # custom complements will no longer be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if are_custom_complements_enabled(channel):
            disable_custom_complements(channel)
            await ctx.channel.send("@" + channel + " custom complements are now disabled.")
        else:
            await ctx.channel.send("@" + channel + " custom complements are already disabled.")

    @commands.command()
    async def disabledefaultcomplements(self, ctx):
        # default complements will no longer be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if are_default_complements_enabled(channel):
            disable_default_complements(channel)
            await ctx.channel.send("@" + channel + " default complements are now disabled.")
        else:
            await ctx.channel.send("@" + channel + " default complements are already disabled!")

    @commands.command()
    async def unignorebots(self, ctx):
        # bots will not get complements
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_ignoring_bots(channel):
            unignore_bots(channel)
            await ctx.channel.send("@" + channel + " bots have a chance of being complemented!")
        else:
            await ctx.channel.send("@" + channel + " bots can already get complements!")

    @commands.command()
    async def ignorebots(self, ctx):
        # bots might get complements
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if not is_ignoring_bots(channel):
            ignore_bots(channel)
            await ctx.channel.send("@" + channel + " bots will no longer get complemented.")
        else:
            await ctx.channel.send("@" + channel + " bots are already not getting complements.")

    @commands.command()
    async def compleave(self, ctx):
        await self.leaveme(ctx)


if __name__ == "__main__":
    bot = Bot()
    bot.run()
