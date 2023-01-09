# bot.py
from env_reader import *
from twitchio.ext import commands
from twitchio import Message
import random
from database import *
import requests
from typing import Callable, Optional, Union
import textwrap

#TODO:
# allow streamers to toggle which commands can/cannot be used by mods/VIPs/subs/everyone.
# allow streamers to control which user groups can receive which complements
# when people try complementing the bot, say something different
# when people reply to bot (e.g. say thank you), say something different
# |
# make a website where users can see all of their info
# make a docker container for app
# Change primary key for users - from username to user id
# deploy app to server
# set up database with data type rules

CMD_PREFIX: str = '!'
DEFAULT_MAX_MSG_LEN: int = 500
MAX_COMPLEMENT_LENGTH: int = 350
F_USER: str = "{user}"

BOT_NICK: str = "complementsbot"
OWNER_NICK: str = 'ereiarrus'

SHOULD_LOG: bool = True


def custom_log(msg) -> None:
    print(msg)


class Bot(commands.Bot):
    def __init__(self) -> None:
        join_channel(BOT_NICK)
        super().__init__(
            token=TMI_TOKEN,
            client_id=CLIENT_ID,
            nick=BOT_NICK,
            prefix=CMD_PREFIX,
            initial_channels=get_joined_channels()
        )

        # Read the default complements from file
        self.COMPLEMENTS_LIST: list[str] = []
        with open("complements_list.txt", "r") as f:
            for line in f:
                self.COMPLEMENTS_LIST.append(line.strip())

    async def event_ready(self) -> None:
        """
        Called once when the bot goes online; purely informational
        """
        if SHOULD_LOG:
            custom_log(f"{BOT_NICK} is online!")

    @staticmethod
    def is_bot(username) -> bool:
        """
        checks if a username matches that of a known or assumed bot; currently the following count as bots:
            - any username ending in 'bot'
            - streamlabs
        """
        return len(username) >= 3 and username[-3:] == 'bot' \
               or username == "streamlabs"

    async def event_message(self, ctx: Message) -> None:
        """
        Runs every time a message is sent in chat. This also includes any commands.
        Decides if the person who sent the message in chat should be complemented based on: complement chance, their
            ignored status, whether they are a bot, if random complements are enabled in the channel.
            Depending on mute status of random complements, the complement might be prepended with a mute prefix.
        """

        if ctx.echo:
            # make sure the bot ignores itself
            return
        if SHOULD_LOG:
            custom_log(f"In channel {ctx.channel.name}, at {ctx.timestamp}, {ctx.author.name} said: {ctx.content}")

        sender: str = ctx.author.name
        channel: str = ctx.channel.name
        is_author_ignored: bool = is_user_ignored(sender)
        should_rng_choose: bool = (random.random() * 100) <= get_complement_chance(ctx.channel.name)
        is_author_bot: bool = is_ignoring_bots(channel) and Bot.is_bot(sender)

        if ctx.content[:len(CMD_PREFIX)] == CMD_PREFIX:
            # Handle commands
            await self.handle_commands(ctx)
        if should_rng_choose \
                and (not is_author_ignored) \
                and (not is_author_bot) \
                and get_random_complement_enabled(ctx.channel.name):
            comp_msg, exists = self.complement_msg(ctx, ctx.author.name, is_random_complement_muted(channel))
            if exists:
                await ctx.channel.send(comp_msg)
                if SHOULD_LOG:
                    custom_log(f"In channel {ctx.channel.name}, at {ctx.timestamp}, {ctx.author.name} "
                               f"was complemented (randomly) with: {comp_msg}")

    def choose_complement(self, ctx: commands.Context) -> (str, bool):
        """
        Chooses a complement with which to complement a user. This is based on the default complements, custom
            complements, and the status of whether either of these two are enabled or disabled for that channel.
        :return complement: the chosen complement (if one exists - otherwise an empty string)
        :return exists: whether there are any valid complements (for example, if  both custom and default complements
            are disabled, this would be False)
        """

        channel: str = ctx.channel.name
        custom_complements: list[str] = []
        if are_custom_complements_enabled(channel):
            custom_complements = get_custom_complements(channel)
        default_complements: list[str] = []
        if are_default_complements_enabled(channel):
            default_complements = self.COMPLEMENTS_LIST

        if len(custom_complements) == 0 and len(default_complements) == 0:
            # No complements to dish out
            return "", False

        default_complements_length: int = len(default_complements)
        index: int = random.randint(0, default_complements_length + len(custom_complements) - 1)
        if index < default_complements_length:
            return default_complements[index], True
        return custom_complements[index - default_complements_length], True

    def complement_msg(self, ctx: Union[commands.Context, Message], who: str = None, is_tts_muted: bool = True) -> (str, bool):
        """
        Format the complement message correctly. This includes any TTS mute prefixes and an '@' in front of the user's
            name if not included to notify them of the complement.
        :param who: the name of the person that the complement is aimed at
        :param is_tts_muted: whether the channel mutes TTS for this complement
        :return complement: the complement chosen, prepended with who it's aimed at and perhaps a TTS muting symbol
        :return exists: whether there are any valid complements (for example, if  both custom and default complements
            are disabled, this would be False
        """

        if who is None:
            who = ctx.author.name
        channel: str = ctx.channel.name
        prefix: str = "@"
        if is_tts_muted:
            prefix = f"{get_tts_ignore_prefix(channel)} {prefix}"
        complement, exists = self.choose_complement(ctx)
        return f"{prefix}{who} {complement}", exists

    @commands.command()
    async def complement(self, ctx: commands.Context) -> None:
        """
        Users can get a complement themselves or complement others with this command assuming the user is not ignored by
            the bot and the channel owner has not disabled command complements.
        Assumes that anything typed after the command is a username, even if it has spaces in it.
        The user of this command is allowed to prepend an optional '@' to the user's name with no change to the
            behaviour of the command.
        """
        msg: str = ctx.message.content.strip()
        args: list[str] = msg.split(" ")
        who: str = ctx.message.author.name
        if len(args) > 1:
            who = " ".join(args[1:])
            if who[0] == "@":
                who = who[1:]

        channel: str = ctx.channel.name
        if is_user_ignored(who) or not get_cmd_complement_enabled(channel):
            return

        comp_msg, exists = self.complement_msg(ctx.message, who, is_cmd_complement_muted(channel))
        if exists:
            await ctx.channel.send(comp_msg)
            if SHOULD_LOG:
                custom_log(f"In channel {ctx.channel.name}, at {ctx.message.timestamp}, {ctx.message.author.name} "
                           f"was complemented (by command) with: {comp_msg}")

    # -------------------- bot channel only commands --------------------

    @staticmethod
    def is_in_bot_channel(ctx: commands.Context) -> bool:
        return ctx.channel.name == BOT_NICK or ctx.channel.name == OWNER_NICK

    @staticmethod
    def send_and_log(ctx: commands.Context, msg: str) -> None:
        """
        Send the message to the channel of ctx and also logs it
        """
        await ctx.channel.send(msg)
        if SHOULD_LOG:
            custom_log(msg)

    class DoIfElse:
        def __init__(self
                     , if_check: Callable[[commands.Context], bool]
                     , true_msg: str
                     , false_msg: str
                     , do_true: Optional[Callable[[commands.Context], None]] = (lambda ctx: None)
                     , do_false: Optional[Callable[[commands.Context], None]] = (lambda ctx: None)) -> None:
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

            self.if_check: Callable[[commands.Context], bool] = if_check
            self.true_msg: str = true_msg
            self.false_msg: str = false_msg
            self.do_true: Callable[[commands.Context], None] = do_true or (lambda ctx: None)
            self.do_false: Callable[[commands.Context], None] = do_false or (lambda ctx: None)

    @staticmethod
    def cmd_body(ctx: commands.Context
                 , permission_check: Optional[Callable[[commands.Context], bool]]
                 , do_before_if: Optional[Callable[[commands.Context], None]] = (lambda ctx: None)
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

        do_before_if: Callable[[commands.Context], None] = do_before_if or (lambda ctx: None)
        do_before_if(ctx)

        user: str = ctx.author.name

        if do_if_else is not None:
            to_send: str
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
    async def joinme(self, ctx: commands.Context) -> None:
        """
        Get the bot to join the user's channel and start complementing people in their channel.
        """

        def do_false(ctx: commands.Context) -> None:
            # Have to save to database and update in memory so bot starts working straight away
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
    async def leaveme(self, ctx: commands.Context) -> None:
        """
        Bot leaves the user's channel and no longer complements chatters there.
        """

        def do_true(ctx: commands.Context) -> None:
            # Update database and in realtime for "instant" effect
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
    async def deleteme(self, ctx: commands.Context) -> None:
        """
        Same as the 'leaveme' command, but on top, also delete any records of the user (e.g. custom complements)
        """

        def do_true(ctx: commands.Context) -> None:
            # Remove any user records from database and leave their channel NOW
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
    async def ignoreme(self, ctx: commands.Context) -> None:
        """
        The user of this command will not get any complements sent their way from ComplementsBot
        """
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
    async def unignoreme(self, ctx: commands.Context) -> None:
        """
        Undoes the 'ignoreme' command; the user of the command will occasionally receive complements, and a direct
        complement using the 'complement' command will work.
        """
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
    async def count(self, ctx: commands.Context) -> None:
        """
        Shows the number of channels that the bot is active in
        """
        Bot.cmd_body(ctx
                     , Bot.is_in_bot_channel
                     , always_msg=f"@{F_USER} {str(number_of_joined_channels())} channels and counting!"
                     )

    @commands.command()
    async def about(self, ctx: commands.Context) -> None:
        """
        Shows some information about the bot
        """
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
    def is_by_broadcaster_or_mod(ctx: commands.Context) -> bool:
        return ctx.author.is_broadcaster \
               or ctx.author.is_mod \
               or ctx.author.name == BOT_NICK \
               or ctx.author.name == OWNER_NICK

    @commands.command()
    async def setchance(self, ctx: commands.Context) -> None:
        """
        Change how likely it is that person sending message gets complemented by random.
        The number given can be any valid float number, with anything 100 or above guaranteeing a complement, and 0 and
            below guaranteeing no complement.
        """

        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        channel: str = ctx.channel.name
        msg: str = ctx.message.content.strip()
        to_send: str = ""
        exception: bool = False
        chance: float = 0
        try:
            chance: float = float((msg.split())[1])
        except ValueError:
            # user tried putting a non-float after '!setchance'
            to_send = f"@{channel} '{chance}' is an invalid number. Please try again."
            exception = True
        except IndexError:
            # user didn't provide anything after '!setchance'
            to_send = f"@{channel} You did not enter a number. Please try again."
            exception = True
        if exception:
            Bot.send_and_log(ctx, to_send)
            return

        set_complement_chance(channel, chance)
        Bot.send_and_log(ctx, f"@{channel} complement chance set to {str(get_complement_chance(channel))}!")

    @commands.command()
    async def disablecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Prevent chatter from being able to use the !complement command in user's channel
        """

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
    async def enablecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Allow chatters in user's chat to use the !complement command
        """
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
    async def disablerandomcomplement(self, ctx: commands.Context) -> None:
        """
        Prevent the bot from randomly complementing chatters in user's chat
        """

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
    async def enablerandomcomplement(self, ctx: commands.Context) -> None:
        """
        Allow the bot to randomly complement chatters in user's chat
        """

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
    async def addcomplement(self, ctx: commands.Context) -> None:
        """
        Add a complement for user's chat only that might be chosen to complement the user's chatters
        """

        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        msg: str = ctx.message.content.strip()
        # Anything after the space after '!addcomplement' is counted as being the complement
        complement: str = msg[msg.find(" ") + 1:]
        user: str = ctx.channel.name
        if len(complement) > MAX_COMPLEMENT_LENGTH:
            to_send: str = f"@{user} complement is too long. It may not be over {MAX_COMPLEMENT_LENGTH} characters long."
            Bot.send_and_log(ctx, to_send)
            return

        add_complement(user, complement)
        Bot.send_and_log(ctx, f"@{user} new complements added: '{complement}'")

    @commands.command()
    async def listcomplements(self, ctx: commands.Context) -> None:
        """
        Show the user all of their custom complements.
        Due to Twitch having a maximum message length, these might have to be sent over more than one message, so it is
            split to make sure all complements are visible.
        """
        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        user: str = ctx.channel.name
        comps_msg: str = '"' + '", "'.join(get_custom_complements(user)) + '"'

        msgs: list[str] = textwrap.wrap(f"@{user} complements: {comps_msg}", DEFAULT_MAX_MSG_LEN)

        if len(msgs) > 0:
            for msg in msgs:
                Bot.send_and_log(ctx, msg)
        else:
            msg: str = f"@{user} No complements found."
            Bot.send_and_log(ctx, msg)

    @commands.command()
    async def removecomplement(self, ctx: commands.Context) -> None:
        """
        Remove a custom complement, and show the ones that were removed (similarly to !listallcomplements, this might
            require splitting the message into multiple messages due to length limit).
        all non-alphanumeric symbols are removed from anything coming after '!removecomplement ' and compared to all
            the user's custom complements after having all non-alphanumeric symbols removed from them also. All custom
            complements containing as a substring what the user wanted to remove are removed from the user's custom
            complements list.
        """

        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        msg: str = ctx.message.content.strip()
        phrase: str = remove_chars(msg[msg.find(" ") + 1:])
        user: str = ctx.channel.name
        to_remove_comps, to_keep_comps = complements_to_remove(get_custom_complements(user), phrase)
        remove_complements(user, to_keep=to_keep_comps)

        removed_comps_msg: str = '"' + '", "'.join(to_remove_comps) + '"'

        # if message goes over length limit, send it over multiple messages
        msgs: list[str] = textwrap.wrap(f"@{user} complement/s removed: {removed_comps_msg}", DEFAULT_MAX_MSG_LEN)

        if len(to_remove_comps) > 0:
            for msg in msgs:
                Bot.send_and_log(ctx, msg)
        else:
            msg: str = f"@{user} No complements with that phrase found."
            Bot.send_and_log(ctx, msg)

    @commands.command()
    async def removeallcomplements(self, ctx: commands.Context) -> None:
        """
        Remove all custom complements a user has added
        """

        Bot.cmd_body(ctx
                     , Bot.is_by_broadcaster_or_mod
                     , (lambda ctx: remove_all_complements(ctx.channel.name))
                     , None
                     , f"@{F_USER} all of your custom complements have been removed.")

    @commands.command()
    async def setmutettsprefix(self, ctx: commands.Context) -> None:
        """
        Set the character/string to put in front of a message to mute TTS
        """

        if not Bot.is_by_broadcaster_or_mod(ctx):
            return

        msg: str = ctx.message.content
        msg: str = msg.strip()
        prefix: str = msg[msg.find(" ") + 1:]
        set_mute_prefix(ctx.channel.name, prefix)
        Bot.send_and_log(ctx, f"@{ctx.author.name} mute TTS prefix changed to '{prefix}'.")

    @commands.command()
    async def mutecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Mutes TTS for complements sent with !complement command
        """

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
    async def muterandomcomplement(self, ctx: commands.Context) -> None:
        """
        Mutes TTS for complements given out randomly
        """

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
    async def unmutecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Unmutes TTS for complements sent with !complement command
        """

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
    async def unmuterandomcomplement(self, ctx: commands.Context) -> None:
        """
        Unmutes TTS for complements given out randomly
        """

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
    async def enablecustomcomplements(self, ctx: commands.Context) -> None:
        """
        All custom complements will be added to the pool that we choose complements for chatters from
        """

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
    async def enabledefaultcomplements(self, ctx: commands.Context) -> None:
        """
        All default complements will be added to the pool that we choose complements for chatters from
        """

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
    async def disablecustomcomplements(self, ctx: commands.Context) -> None:
        """
        All custom complements will be removed from the pool that we choose complements for chatters from; this does NOT
            delete the custom complements.
        """
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
    async def disabledefaultcomplements(self, ctx: commands.Context) -> None:
        """
        All default complements will be removed from the pool that we choose complements for chatters from
        """

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
    async def unignorebots(self, ctx: commands.Context) -> None:
        """
        Chatters that count as bots might be complemented by ComplementsBot
        """
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
    async def ignorebots(self, ctx: commands.Context) -> None:
        """
        Chatters that count as bots will not be complemented by ComplementsBot
        """

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
    async def compleave(self, ctx: commands.Context) -> None:
        """
        Allows the user to kick ComplementsBot out of their channel from their own channel chat
        """
        await self.leaveme(ctx)


if __name__ == "__main__":
    bot: Bot = Bot()
    bot.run()
