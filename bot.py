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

    @staticmethod
    def is_bot(username):
        return len(username) >= 3 and username[-3:] == 'bot' \
               or username == "streamlabs"

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
        is_author_bot = is_ignoring_bots(channel) and Bot.is_bot(sender)

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
    def send_and_log(ctx, msg: str):
        await ctx.channel.send(msg)
        if SHOULD_LOG:
            print(msg)

    class DoIfElse:
        def __init__(self
                     , if_check: callable
                     , true_msg: str
                     , false_msg: str
                     , do_true: callable = (lambda ctx: None)
                     , do_false: callable = (lambda ctx: None)):
            """
            :param if_check: what the condition for entering 'if' statement is
            :param do_true: what to do when the if_check succeeds (done before sending message to chat);
                if 'None', does nothing
            :param true_msg: what to send to chat when the 'if' if_check succeeds; any occurrence of F_USER in the string is
                replaced with the name of the user in chat who called the original command
            :param do_false: what to do when if_check fails (done before sending message to chat);
                if 'None', does nothing
            :param false_msg: what to send to chat when the if_check fails; any occurrence of F_USER in the string is
                replaced with the name of the user in chat who called the original command
            """

            self.if_check = if_check
            self.true_msg = true_msg
            self.false_msg = false_msg
            self.do_true = do_true or (lambda ctx: None)
            self.do_false = do_false or (lambda ctx: None)

    @staticmethod
    def cmd_body(ctx
                 , permission_check: callable
                 , do_before_if: callable = (lambda ctx: None)
                 , do_if_else: DoIfElse = None
                 , always_msg: str = None) -> bool:
        """
        The main structure in which commands sent to the bot's channel need to be processed
        :param ctx: context from the original call
        :param permission_check: who is allowed to run the command in question
        :param do_before_if: this is always called if permission_check passes; if 'None', does nothing
        :param do_if_else: specifies the if condition on which to enter the if block, what to do in the if and else
            blocks, and the messages to send in either block; if None, all if/else logic is skipped
        :param always_msg: message to always send to chat (after do_before_if and do_if_else); if None, send nothing;
            any occurrence of F_USER in the string is replaced with the name of the user in chat who called the
            original command
        :return: True if permission_check passes, False otherwise
        """

        if not permission_check(ctx):
            return False

        do_before_if = do_before_if or (lambda ctx: None)
        do_before_if(ctx)

        user = ctx.author.name

        if do_if_else is not None:
            to_send = ""
            if do_if_else.if_check(ctx):
                do_if_else.do_true(ctx)
                to_send = do_if_else.true_msg.replace(F_USER, user)
            else:
                do_if_else.do_false(ctx)
                to_send = do_if_else.false_msg.replace(F_USER, user)
            Bot.send_and_log(ctx, to_send)

        if always_msg is not None:
            to_send = always_msg.replace(F_USER, user)
            Bot.send_and_log(ctx, to_send)

        return True

    @commands.command()
    async def joinme(self, ctx):
        # I will join your channel!
        def do_false(ctx):
            join_channel(ctx.author.name)
            # TODO: follow the user
            await self.join_channels([ctx.author.name])

        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , None
                     , Bot.DoIfElse((lambda ctx: is_channel_joined(ctx.author.name))
                                    , f"@{F_USER} I am already in your channel!"
                                    , f"@{F_USER} I have joined your channel!"
                                    , None
                                    , do_false
                                    )
                     )

    @commands.command()
    async def leaveme(self, ctx):
        # I will leave your channel
        def do_true(ctx):
            leave_channel(ctx.author.name)
            # TODO: unfollow the user
            await self.part_channels([ctx.author.name])

        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , None
                     , Bot.DoIfElse((lambda ctx: is_channel_joined(ctx.author.name))
                                    , f"@{F_USER} I have left your channel."
                                    , f"@{F_USER} I have not joined your channel."
                                    , do_true
                                    , None
                                    )
                     )

    @commands.command()
    async def deleteme(self, ctx):
        # I will delete your channel information
        def do_true(ctx):
            delete_channel(ctx.author.name)
            # TODO: unfollow the user
            await self.part_channels([ctx.author.name])

        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , None
                     , Bot.DoIfElse((lambda ctx: channel_exists(ctx.author.name))
                                    , f"@{F_USER} I have deleted your channel data."
                                    , f"@{F_USER} your channel does not exists in my records."
                                    , do_true
                                    , None
                                    )
                     )

    @commands.command()
    async def ignoreme(self, ctx):
        # no longer complement the user
        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , None
                     , Bot.DoIfElse((lambda ctx: is_user_ignored(ctx.author.name))
                                    , f"@{F_USER} I am already ignoring you."
                                    , f"@{F_USER} I am now ignoring you."
                                    , None
                                    , (lambda ctx: ignore(ctx.author.name))
                                    )
                     )

    @commands.command()
    async def unignoreme(self, ctx):
        # undo ignoreme
        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , None
                     , Bot.DoIfElse((lambda ctx: is_user_ignored(ctx.author.name))
                                    , f"@{F_USER} I am no longer ignoring you!"
                                    , f"@{F_USER} I am not ignoring you!"
                                    , (lambda ctx: unignore(ctx.author.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def count(self, ctx):
        # see how many channels I'm in
        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , always_msg=f"@{F_USER} {str(number_of_joined_channels())} channels and counting!"
                     )

    @commands.command()
    async def about(self, ctx):
        # learn all about me
        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , always_msg=f"@{F_USER} "
                                  "For most up-to-date information on commands, please have a look at "
                                  "https://github.com/Ereiarrus/ComplementsBotPy#readme "
                                  "and for most up-to-date complements, have a look at "
                                  "https://github.com/Ereiarrus/ComplementsBotPy/blob/main/complements_list.txt"
                     )

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

        channel = ctx.channel.name
        msg = ctx.message.content.strip()
        chance = ""
        to_send = ""
        exception = False
        try:
            chance = (msg.split())[1]
            chance = float(chance)
        except ValueError:
            to_send = f"@{channel} '{chance}' is an invalid number. Please try again."
            exception = True
        except IndexError:
            to_send = f"@{channel} You did not enter a number. Please try again."
            exception = True
        if exception:
            Bot.send_and_log(ctx, to_send)
            return

        set_complement_chance(channel, chance)
        to_send = f"@{channel} complement chance set to {str(get_complement_chance(channel))}!"
        Bot.send_and_log(ctx, to_send)

    @commands.command()
    async def disablecmdcomplement(self, ctx):
        # prevent users from being able to use the !complement command in your channel
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: get_cmd_complement_enabled(ctx.channel.name))
                                    , f"@{F_USER} your viewers will no longer be able to make use of the "
                                      f"!complement command."
                                    , f"@{F_USER} your viewers already cannot make use of the !complement command."
                                    , (lambda ctx: disable_cmd_complement(ctx.channel.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def enablecmdcomplement(self, ctx):
        # undo !disablecmdcomplement
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: get_cmd_complement_enabled(ctx.channel.name))
                                    , f"@{F_USER} your viewers can already make use of the !complement command!"
                                    , f"@{F_USER} your viewers will now be able to make use of the !complement command!"
                                    , None
                                    , (lambda ctx: enable_cmd_complement(ctx.channel.name))
                                    )
                     )

    @commands.command()
    async def disablerandomcomplement(self, ctx):
        # the bot will no longer randomly give out complements
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: get_random_complement_enabled(ctx.channel.name))
                                    , f"@{F_USER} your viewers will no longer randomly receive complements."
                                    , f"@{F_USER} your viewers already do not randomly receive complements."
                                    , (lambda ctx: disable_random_complement(ctx.channel.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def enablerandomcomplement(self, ctx):
        # undo !disablerandomcomplement
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: get_random_complement_enabled(ctx.channel.name))
                                    , f"@{F_USER} I already randomly send out complements!"
                                    , f"@{F_USER} your viewers will now randomly receive complements!"
                                    , None
                                    , (lambda ctx: enable_random_complement(ctx.channel.name))
                                    )
                     )

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
            Bot.send_and_log(ctx, to_send)
            return

        add_complement(user, complement)
        to_send = f"@{user} new complements added: '{complement}'"
        Bot.send_and_log(ctx, to_send)

    @commands.command()
    async def listcomplements(self, ctx):
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        user = ctx.channel.name
        comps_msg = '"' + '", "'.join(get_custom_complements(user)) + '"'

        to_send = f"@{user} complements: {comps_msg}"
        msgs = textwrap.wrap(to_send, DEFAULT_MAX_MSG_LEN)

        if len(msgs) > 0:
            for msg in msgs:
                Bot.send_and_log(ctx, msg)
        else:
            msg = f"@{user} No complements found."
            Bot.send_and_log(ctx, msg)

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

        removed_comps_msg = '"' + '", "'.join(to_remove_comps) + '"'

        to_send = f"@{user} complement removed: {removed_comps_msg}"
        msgs = textwrap.wrap(to_send, DEFAULT_MAX_MSG_LEN)

        if len(msgs) > 0:
            for msg in msgs:
                Bot.send_and_log(ctx, msg)
        else:
            msg = f"@{user} No complements with that phrase found."
            Bot.send_and_log(ctx, msg)

    @commands.command()
    async def removeallcomplements(self, ctx):
        # remove all custom complements a user has added
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , (lambda ctx: remove_all_complements(ctx.channel.name))
                     , None
                     , f"@{F_USER} all of your custom complements have been removed.")

    @commands.command()
    async def setmutettsprefix(self, ctx):
        # the character/string to put in front of a message to mute tts
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        msg = ctx.message.content
        msg = msg.strip()
        prefix = msg[msg.find(" ") + 1:]
        set_mute_prefix(ctx.channel.name, prefix)
        to_send = f"@{ctx.author.name} mute TTS prefix changed to '{prefix}'."
        Bot.send_and_log(ctx, to_send)

    @commands.command()
    async def mutecmdcomplement(self, ctx):
        # mutes tts for complements sent with !complement command
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: is_cmd_complement_muted(ctx.channel.name))
                                    , f"@{F_USER} command complements are already muted!"
                                    , f"@{F_USER} command complements are now muted."
                                    , None
                                    , (lambda ctx: mute_cmd_complement(ctx.channel.name))
                                    )
                     )

    @commands.command()
    async def muterandomcomplement(self, ctx):
        # mutes tts for complements randomly given out
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: is_random_complement_muted(ctx.channel.name))
                                    , f"@{F_USER} random complements are already muted!"
                                    , f"@{F_USER} random complements are now muted."
                                    , None
                                    , (lambda ctx: mute_random_complement(ctx.channel.name))
                                    )
                     )

    @commands.command()
    async def unmutecmdcomplement(self, ctx):
        # unmutes tts for complements sent with !complement command
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: is_cmd_complement_muted(ctx.channel.name))
                                    , f"@{F_USER} command complements are no longer muted!"
                                    , f"@{F_USER} command complements are already unmuted!"
                                    , (lambda ctx: unmute_cmd_complement(ctx.channel.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def unmuterandomcomplement(self, ctx):
        # unmutes tts for complements randomly given out
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: is_random_complement_muted(ctx.channel.name))
                                    , f"@{F_USER} random complements are no longer muted!"
                                    , f"@{F_USER} random complements are already unmuted!"
                                    , (lambda ctx: unmute_random_complement(ctx.channel.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def enablecustomcomplements(self, ctx):
        # custom complements will now be used to complement viewers
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: are_custom_complements_enabled(ctx.channel.name))
                                    , f"@{F_USER} custom complements are already enabled!"
                                    , f"@{F_USER} custom complements are now enabled!"
                                    , None
                                    , (lambda ctx: enable_custom_complements(ctx.channel.name))
                                    )
                     )

    @commands.command()
    async def enabledefaultcomplements(self, ctx):
        # custom complements will now be used to complement viewers
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: are_default_complements_enabled(ctx.channel.name))
                                    , f"@{F_USER} default complements are already enabled!"
                                    , f"@{F_USER} default complements are now enabled!"
                                    , None
                                    , (lambda ctx: enable_default_complements(ctx.channel.name))
                                    )
                     )

    @commands.command()
    async def disablecustomcomplements(self, ctx):
        # custom complements will no longer be used to complement viewers
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: are_custom_complements_enabled(ctx.channel.name))
                                    , f"@{F_USER} custom complements are now disabled."
                                    , f"@{F_USER} custom complements are already disabled."
                                    , (lambda ctx: disable_custom_complements(ctx.channel.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def disabledefaultcomplements(self, ctx):
        # default complements will no longer be used to complement viewers
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: are_default_complements_enabled(ctx.channel.name))
                                    , f"@{F_USER} default complements are now disabled."
                                    , f"@{F_USER} default complements are already disabled!"
                                    , (lambda ctx: disable_default_complements(ctx.channel.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def unignorebots(self, ctx):
        # bots will not get complements
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: is_ignoring_bots(ctx.channel.name))
                                    , f"@{F_USER} bots have a chance of being complemented!"
                                    , f"@{F_USER} bots can already get complements!"
                                    , (lambda ctx: unignore_bots(ctx.channel.name))
                                    , None
                                    )
                     )

    @commands.command()
    async def ignorebots(self, ctx):
        # bots might get complements
        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , None
                     , Bot.DoIfElse((lambda ctx: is_ignoring_bots(ctx.channel.name))
                                    , f"@{F_USER} bots are already not getting complements."
                                    , f"@{F_USER} bots will no longer get complemented."
                                    , None
                                    , (lambda ctx: ignore_bots(ctx.channel.name))
                                    )
                     )

    @commands.command(aliases=["compleaveme"])
    async def compleave(self, ctx):
        await self.leaveme(ctx)


if __name__ == "__main__":
    bot = Bot()
    bot.run()
