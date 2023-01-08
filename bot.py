# bot.py
from env_reader import *
from twitchio.ext import commands
import random
from database import *
import requests
import textwrap

# TODO:
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
DEFAULT_MAX_MSG_LEN = 500
MAX_COMPLEMENT_LENGTH = 350
F_USER = "{user}"

BOT_NICK = "complementsbot"
OWNER_NICK = 'ereiarrus'

SHOULD_LOG = True


class Bot(commands.Bot):
    def __init__(self):
        join_channel(BOT_NICK)
        super().__init__(
            token=TMI_TOKEN,
            client_id=CLIENT_ID,
            nick=BOT_NICK,
            prefix=CMD_PREFIX,
            initial_channels=get_joined_channels()
        )

        self.COMPLEMENTS_LIST = []
        with open("complements_list.txt", "r") as f:
            for line in f:
                self.COMPLEMENTS_LIST.append(line.strip())

    async def event_ready(self):
        """
        Called once when the bot goes online.
        """
        if SHOULD_LOG:
            print(f"{BOT_NICK} is online!")

    async def event_message(self, ctx):
        """

        :param ctx:
        :return:
        """
        # Runs every time a message is sent in chat.
        if ctx.echo:
            # make sure the bot ignores itself
            return
        if SHOULD_LOG:
            print(f"In channel {ctx.channel.name}, at {ctx.timestamp}, {ctx.author.name} said: {ctx.content}")

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
                if SHOULD_LOG:
                    print(f"In channel {ctx.channel.name}, at {ctx.timestamp}, {ctx.author.name} "
                          f"was complemented (randomly) with: {comp_msg}")

    def choose_complement(self, ctx):
        """
        :return complement: the chosen complement (if one exists)
        :return exists: whether there are any valid complements (for example, if  both custom and default complements
            are disabled, this would be False
        """
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

    def complement_msg(self, ctx: commands.Context, who: str = None, is_tts_muted: bool = True):
        """
        :return complement: the complement chosen, prepended with who it's aimed at and perhaps a TTS muting symbol
        :return exists: whether there are any valid complements (for example, if  both custom and default complements
            are disabled, this would be False
        """
        prefix = ""
        if who is None:
            who = ctx.author.name
        channel = ctx.channel.name
        prefix = f"@{prefix}"
        if is_tts_muted:
            prefix = f"{get_tts_ignore_prefix(channel)} {prefix}"
        complement, exists = self.choose_complement(ctx)
        return f"{prefix}{who} {complement}", exists

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
            if SHOULD_LOG:
                print(f"In channel {ctx.channel.name}, at {ctx.message.timestamp}, {ctx.message.author.name} "
                      f"was complemented (by command) with: {comp_msg}")

    # -------------------- bot channel only commands --------------------


    @staticmethod
    def is_in_bot_channel(ctx):
        return ctx.channel.name == BOT_NICK or ctx.channel.name == OWNER_NICK

    @staticmethod
    def bot_cmd_body(ctx
                     , if_check: callable
                     , do_true: callable
                     , true_msg: str
                     , do_false: callable
                     , false_msg: str) -> bool:
        """
        The main structure in which commands sent to the bot's channel need to be processed
        :param ctx: context from the original call
        :param if_check: what the condition for entering 'if' statement is
        :param do_true: what to do when the if_check succeeds (done before sending message to chat);
            if 'None', does nothing
        :param true_msg: what to send to chat when the 'if' if_check succeeds; any ocurrence of F_USER in the string is
            replaced with the name of the user in chat who called the original command
        :param do_false: what to do when if_check fails (done before sending message to chat);
            if 'None', does nothing
        :param false_msg: what to send to chat when the if_check fails; any ocurrence of F_USER in the string is
            replaced with the name of the user in chat who called the original command

        :return: True if in bot channel, False otherwise
        """

        if not Bot.is_in_bot_channel(ctx):
            return False

        user = ctx.author.name
        if do_true is None:
            do_true = (lambda ctx: None)
        if do_false is None:
            do_false = (lambda ctx: None)

        to_send = "!!!THIS SHOULD NOT GET SENT!!!"
        if if_check(ctx):
            do_true(ctx)
            to_send = true_msg.replace(F_USER, user)
        else:
            do_false(ctx)
            to_send = false_msg.replace(F_USER, user)
        await ctx.channel.send(to_send)
        if SHOULD_LOG:
            print(to_send)

        return True


    @commands.command()
    async def joinme(self, ctx):
        # I will join your channel!
        def do_false(ctx):
            join_channel(ctx.author.name)
            # TODO: follow the user
            await self.join_channels([ctx.author.name])
        self.bot_cmd_body(ctx
                          , (lambda ctx: is_channel_joined(ctx.author.name))
                          , None
                          , f"@{F_USER} I am already in your channel!"
                          , do_false
                          , f"@{F_USER} I have joined your channel!"
                          )

    @commands.command()
    async def leaveme(self, ctx):
        # I will leave your channel
        def do_true(ctx):
            leave_channel(ctx.author.name)
            # TODO: unfollow the user
            await self.part_channels([ctx.author.name])
        self.bot_cmd_body(ctx
                          , (lambda ctx: is_channel_joined(ctx.author.name))
                          , do_true
                          , f"@{F_USER} I have left your channel."
                          , None
                          , f"@{F_USER} I have not joined your channel."
                          )

    @commands.command()
    async def deleteme(self, ctx):
        # I will delete your channel information
        def do_true(ctx):
            delete_channel(ctx.author.name)
            # TODO: unfollow the user
            await self.part_channels([ctx.author.name])
        self.bot_cmd_body(ctx
                          , (lambda ctx: channel_exists(ctx.author.name))
                          , do_true
                          , f"@{F_USER} I have deleted your channel data."
                          , None
                          , f"@{F_USER} your channel does not exists in my records."
                          )

    @commands.command()
    async def ignoreme(self, ctx):
        # no longer complement the user
        self.bot_cmd_body(ctx
                          , (lambda ctx: is_user_ignored(ctx.author.name))
                          , None
                          , f"@{F_USER} I am already ignoring you."
                          , (lambda ctx: ignore(ctx.author.name))
                          , f"@{F_USER} I am now ignoring you."
                          )

    @commands.command()
    async def unignoreme(self, ctx):
        # undo ignoreme
        if not Bot.is_in_bot_channel(ctx):
            return

        user = ctx.author.name
        if is_user_ignored(user):
            unignore(user)
            to_send = f"@{user} I am no longer ignoring you!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{user} I am not ignoring you!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def count(self, ctx):
        # see how many channels I'm in
        if not Bot.is_in_bot_channel(ctx):
            return
        to_send = f"@{ctx.message.author.name} {str(number_of_joined_channels())} channels and counting!"
        await ctx.channel.send(to_send)
        if SHOULD_LOG:
            print(to_send)

    @commands.command()
    async def about(self, ctx):
        # learn all about me
        if not Bot.is_in_bot_channel(ctx):
            return
        to_send = f"@{ctx.author.name} " \
                  "For most up-to-date information on commands, please have a look at " \
                  "https://github.com/Ereiarrus/ComplementsBotPy#readme and for most up-to-date complements, " \
                  "have a look at https://github.com/Ereiarrus/ComplementsBotPy/blob/main/complements_list.txt"
        await ctx.channel.send(to_send)
        if SHOULD_LOG:
            print(to_send)

    # -------------------- any channel, but must be by owner --------------------

    @staticmethod
    def is_by_broadcaster_or_mod(ctx):
        return ctx.author.is_broadcaster \
               or ctx.author.is_mod \
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
            to_send = f"@{user} '{chance}' is an invalid number. Please try again."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
            return
        except IndexError:
            to_send = f"@{user} You did not enter a number. Please try again."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
            return
        set_complement_chance(user, chance)
        to_send = f"@{user} complement chance set to {str(get_complement_chance(user))}!"
        await ctx.channel.send(to_send)
        if SHOULD_LOG:
            print(to_send)

    @commands.command()
    async def disablecmdcomplement(self, ctx):
        # prevent users from being able to use the !complement command in your channel
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        user = ctx.channel.name
        if get_cmd_complement_enabled(user):
            disable_cmd_complement(user)
            to_send = f"@{user} your viewers will no longer be able to make use of the !complement command."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{user} your viewers already cannot make use of the !complement command."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def enablecmdcomplement(self, ctx):
        # undo !disablecmdcomplement
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        user = ctx.channel.name
        if get_cmd_complement_enabled(user):
            to_send = f"@{user} your viewers can already make use of the !complement command!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            enable_cmd_complement(user)
            to_send = f"@{user} your viewers will now be able to make use of the !complement command!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def disablerandomcomplement(self, ctx):
        # the bot will no longer randomly give out complements
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        user = ctx.channel.name
        if get_random_complement_enabled(user):
            disable_random_complement(user)
            to_send = f"@{user} your viewers will no longer randomly receive complements."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{user} your viewers already do not randomly receive complements."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def enablerandomcomplement(self, ctx):
        # undo !disablerandomcomplement
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        user = ctx.channel.name
        if get_random_complement_enabled(user):
            to_send = f"@{user} I already randomly send out complements!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            enable_random_complement(user)
            to_send = f"@{user} your viewers will now randomly receive complements!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def addcomplement(self, ctx):
        # add a custom complement for owner's channel
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        msg = ctx.message.content.strip()
        complement = msg[msg.find(" ") + 1:]
        user = ctx.channel.name
        if len(complement) > MAX_COMPLEMENT_LENGTH:
            to_send = f"@{user} complement is too long. It may not be over {MAX_COMPLEMENT_LENGTH} characters long."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
            return

        add_complement(user, complement)
        to_send = f"@{user} new complements added: '{complement}'"
        await ctx.channel.send(to_send)
        if SHOULD_LOG:
            print(to_send)

    @commands.command()
    async def listcomplements(self, ctx):
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        user = ctx.channel.name
        comps_msg = "'" + "', '".join(get_custom_complements(user)) + "'"

        to_send = f"@{user} complements: {comps_msg}"
        msgs = textwrap.wrap(to_send, DEFAULT_MAX_MSG_LEN)

        if len(msgs) > 0:
            for msg in msgs:
                await ctx.channel.send(msg)
                if SHOULD_LOG:
                    print(msg)
        else:
            msg = f"@{user} No complements found."
            await ctx.channel.send(msg)
            if SHOULD_LOG:
                print(msg)

    @commands.command()
    async def removecomplement(self, ctx):
        # remove a custom complement
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        msg = ctx.message.content.strip()
        phrase = remove_chars(msg[msg.find(" ") + 1:])
        user = ctx.channel.name
        to_remove_comps, to_keep_comps = complements_to_remove(get_custom_complements(user), phrase)
        remove_complements(user, to_keep_comps)

        removed_comps_msg = "'" + "', '".join(to_remove_comps) + "'"

        to_send = f"@{user} complement removed: {removed_comps_msg}"
        msgs = textwrap.wrap(to_send, DEFAULT_MAX_MSG_LEN)

        if len(msgs) > 0:
            for msg in msgs:
                await ctx.channel.send(msg)
                if SHOULD_LOG:
                    print(msg)
        else:
            msg = f"@{user} No complements with that phrase found."
            await ctx.channel.send(msg)
            if SHOULD_LOG:
                print(msg)

    @commands.command()
    async def removeallcomplements(self, ctx):
        # remove all custom complements a user has added
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        user = ctx.channel.name
        remove_all_complements(user)
        to_send = f"@{user} all of your custom complements have been removed."
        await ctx.channel.send(to_send)
        if SHOULD_LOG:
            print(to_send)

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
        to_send = f"@{channel} mute TTS prefix changed to '{prefix}'."
        await ctx.channel.send(to_send)
        if SHOULD_LOG:
            print(to_send)

    @commands.command()
    async def mutecmdcomplement(self, ctx):
        # mutes tts for complements sent with !complement command
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_cmd_complement_muted(channel):
            to_send = f"@{channel} command complements are already muted!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            mute_cmd_complement(channel)
            to_send = f"@{channel} command complements are now muted."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def muterandomcomplement(self, ctx):
        # mutes tts for complements randomly given out
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_random_complement_muted(channel):
            to_send = f"@{channel} random complements are already muted!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            mute_random_complement(channel)
            to_send = f"@{channel} random complements are now muted."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def unmutecmdcomplement(self, ctx):
        # unmutes tts for complements sent with !complement command
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_cmd_complement_muted(channel):
            unmute_cmd_complement(channel)
            to_send = f"@{channel} command complements are no longer muted!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} command complements are already unmuted!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def unmuterandomcomplement(self, ctx):
        # unmutes tts for complements randomly given out
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_random_complement_muted(channel):
            unmute_random_complement(channel)
            to_send = f"@{channel} random complements are no longer muted!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} random complements are already unmuted!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def enablecustomcomplements(self, ctx):
        # custom complements will now be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if not are_custom_complements_enabled(channel):
            enable_custom_complements(channel)
            to_send = f"@{channel} custom complements are now enabled!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} custom complements are already enabled!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def enabledefaultcomplements(self, ctx):
        # custom complements will now be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if not are_default_complements_enabled(channel):
            enable_default_complements(channel)
            to_send = f"@{channel} default complements are now enabled!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} default complements are already enabled!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def disablecustomcomplements(self, ctx):
        # custom complements will no longer be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if are_custom_complements_enabled(channel):
            disable_custom_complements(channel)
            to_send = f"@{channel} custom complements are now disabled."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} custom complements are already disabled."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def disabledefaultcomplements(self, ctx):
        # default complements will no longer be used to complement viewers
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if are_default_complements_enabled(channel):
            disable_default_complements(channel)
            to_send = f"@{channel} default complements are now disabled."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} default complements are already disabled!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def unignorebots(self, ctx):
        # bots will not get complements
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if is_ignoring_bots(channel):
            unignore_bots(channel)
            to_send = f"@{channel} bots have a chance of being complemented!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} bots can already get complements!"
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def ignorebots(self, ctx):
        # bots might get complements
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return
        channel = ctx.channel.name

        if not is_ignoring_bots(channel):
            ignore_bots(channel)
            to_send = f"@{channel} bots will no longer get complemented."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)
        else:
            to_send = f"@{channel} bots are already not getting complements."
            await ctx.channel.send(to_send)
            if SHOULD_LOG:
                print(to_send)

    @commands.command()
    async def compleave(self, ctx):
        await self.leaveme(ctx)


if __name__ == "__main__":
    bot = Bot()
    bot.run()
