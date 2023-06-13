"""
Holds all commands (and their logic) for how ComplementsBot should complement Twitch chatters
"""
import asyncio
import time
import itertools
import os
import random
import textwrap
from typing import Awaitable, Callable, Optional, Tuple, Union
import aiofiles

from twitchio import Message
from twitchio.ext import commands, routines

from . import database
from .utilities import Awaitables, remove_chars, run_with_appropriate_awaiting
from ..env_reader import CLIENT_SECRET, TMI_TOKEN, STATUS_FILE


# TODO:
#  why does complements bot crash every now and then? currently have it set up so that if no activity is detected after an
#       hour, it restarts itself
#  Write tests
#  If failed to join channel (or left channel due to lost connection?), try rejoining it every few hours
#  (paid feature - paid per message that has to go through the OpenAI API) integrate OpenAI API calls that generate
#       complements based on streamer's existing complements (or default ones) + last few messages from chat
#  Disabled for first x-hundred users; post advert every some amount of time (that they can pay to get rid of); advert can be
#       either from some sponsor that perhaps wants to advertise through the bot, or advertising my stream/the bot itself
#  Make all dates be stored explicitly in UTC
#  allow streamers to toggle which commands can/cannot be used by mods/VIPs/subs/everyone -
#       broadcaster and me can do anything; need lists for commands that certain user groups can use:
#       - list for viewers
#       - list for VIPs
#       - list for Mods (mods can do anything VIPs can, plus extra)
#       - list for subs (+ 2 extra lists for sub tiers?)
#       once this is implemented, can I merge the logic for commands like 'compleaveme' and 'leaveme'?
#  when people try complementing the bot, say something different/thank them
#  test if an error in building/running the docker container on the VPS causes github actions to fail
#  use asyncio.create_task() instead of calling a coroutine as if it is a function - create_task() starts the task up straight
#       away, whereas calling it as a function only creates a coroutine that will start only once awaited
#  add caching when random complement gets generated - create a stream of n random complements from the user's list;
#       this is in case twitch API usage goes too high
#  create discord integration, so the bot can be used on discord as well
#  |
#  make a website where users can see all of their info
#  get the website to also have a tool to convert between userid and username
#  set up database with data type rules - on DynamoDB(?)
#  allow users to make complement redeems in their channel


def custom_log(msg: str) -> None:
    """
    Any messages which we want to log should be passed through this method
    """

    print(msg)


class ComplementsBot(commands.Bot):
    """
    Inherits from TwitchIO's commands.Bot class, and adds twitch chat commands for using the bot
    """

    CMD_PREFIX: str = '!'
    DEFAULT_MAX_MSG_LEN: int = 500
    MAX_COMPLEMENT_LENGTH: int = 350
    F_USER: str = "{user}"
    SHOULD_LOG: bool = True
    OWNER_NICK: str = 'ereiarrus'
    OWNER_ID: str = "118034879"

    def __init__(self) -> None:
        super().__init__(
                token=TMI_TOKEN,
                client_secret=CLIENT_SECRET,
                prefix=ComplementsBot.CMD_PREFIX
        )

        # Read the default complements from file
        self.complements_list: list[str] = []
        with open(os.path.join(os.path.dirname(__file__), "complements_list.txt"), "r",
                  encoding="utf-8") as complements_file:
            for line in complements_file:
                self.complements_list.append(line.strip())

    async def name_to_id(self, username: str) -> Optional[str]:
        """
        :param username: the username of the user whose user id we want
        :return: the user id of the specified user, if the user exists; otherwise 'None'
        """
        res = await self.fetch_users(names=[username])
        if len(res) > 0:
            return str(res[0].id)
        return None

    async def id_to_name(self, uid: str) -> Optional[str]:
        """
        :param uid: the user id of the user whose username we want
        :return: the username of the specified user, if the user exists; otherwise 'None'
        """
        res = await self.fetch_users(ids=[int(uid)])
        if len(res) > 0:
            return res[0].name
        return None

    async def event_ready(self) -> None:
        """
        Called once when the bot goes online; purely informational
        """

        joined_channels: list[int] = list(map(int, await database.get_joined_channels()))
        # joined_channels = [118034879, 845759020]
        max_num_user_reqs: int = 100
        awaitables: Awaitables = Awaitables([])
        chunks = [joined_channels[i: i + max_num_user_reqs] for i in range(0, len(joined_channels), max_num_user_reqs)]
        for chunk in chunks:
            awaitables.add_task(self.fetch_channels(broadcaster_ids=chunk))

        channels: list = list(itertools.chain.from_iterable(await awaitables.gather()))
        channel_names: list[str] = list(map(lambda x: x.user.name, channels))
        await asyncio.gather(self.join_channels(channel_names),
                             database.join_channel(username=self.nick, name_to_id=self.name_to_id))

        self.write_status.start()

        if ComplementsBot.SHOULD_LOG:
            custom_log(f"{self.nick} is online!")

    @staticmethod
    @routines.routine(minutes=1)
    async def write_status():
        """
        write status of the bot - outside program checks to make sure it writes something, and
        if it doesn't the docker container gets restarted
        """
        async with aiofiles.open(STATUS_FILE, mode='w') as file:
            await file.write(str(time.time()))

    @staticmethod
    def is_bot(username: str) -> bool:
        """
        checks if a username matches that of a known or assumed bot; currently the following count as bots:
            - any username ending in 'bot'
            - streamlabs
        """

        return (len(username) >= 3 and username[-3:].lower() == 'bot' or
                username in ("streamlabs", "streamelements"))

    async def event_message(self, message: Message) -> None:
        """
        Runs every time a message is sent in chat. This also includes any commands.
        Decides if the person who sent the message in chat should be complemented based on: complement chance, their
            ignored status, whether they are a bot, if random complements are enabled in the channel.
            Depending on mute status of random complements, the complement might be prepended with a mute prefix.
        """

        if message.echo:
            # make sure the bot ignores itself
            return
        if ComplementsBot.SHOULD_LOG:
            custom_log(
                    f"In channel {message.channel.name}, at {message.timestamp}, "
                    f"{message.author.name} said: {message.content}")

        sender_id_raw: Optional[str]
        channel_id_raw: Optional[str]
        sender_id_raw, channel_id_raw = await asyncio.gather(self.name_to_id(message.author.name),
                                                             self.name_to_id(message.channel.name))
        assert sender_id_raw
        assert channel_id_raw
        sender_id: str
        channel_id: str
        sender_id, channel_id = str(sender_id_raw), str(channel_id_raw)

        sender: str = message.author.name
        awaitables: Awaitables = Awaitables([database.is_user_ignored(userid=sender_id),
                                             database.get_complement_chance(userid=channel_id),
                                             database.is_ignoring_bots(userid=channel_id),
                                             database.get_random_complement_enabled(userid=channel_id)
                                             ])
        is_author_ignored: bool
        chance: float
        is_ignoring_bots: bool
        random_complements_enabled: bool

        if message.content[:len(ComplementsBot.CMD_PREFIX)] == ComplementsBot.CMD_PREFIX:
            # Handle commands
            awaitables.add_task(self.handle_commands(message))
            is_author_ignored, chance, is_ignoring_bots, random_complements_enabled, _ = await awaitables.gather()
        else:
            is_author_ignored, chance, is_ignoring_bots, random_complements_enabled = await awaitables.gather()
        should_rng_choose: bool = (random.random() * 100) <= chance
        is_author_bot: bool = is_ignoring_bots and ComplementsBot.is_bot(sender)

        if (should_rng_choose
                and (not is_author_ignored)
                and (not is_author_bot)
                and random_complements_enabled):
            random_complements_muted: bool = await database.are_random_complements_muted(userid=channel_id)
            comp_msg, exists = await self.complement_msg(message, message.author.name, random_complements_muted)
            if exists:
                await message.channel.send(comp_msg)
                if ComplementsBot.SHOULD_LOG:
                    custom_log(f"In channel {message.channel.name}, at {message.timestamp}, {message.author.name} "
                               f"was complemented (randomly) with: {comp_msg}")

    async def choose_complement(self, ctx: Message) -> Tuple[str, bool]:
        """
        Chooses a complement with which to complement a user. This is based on the default complements, custom
            complements, and the status of whether either of these two are enabled or disabled for that channel.
        :return complement: the chosen complement (if one exists - otherwise an empty string)
        :return exists: whether there are any valid complements (for example, if  both custom and default complements
            are disabled, this would be False)
        """

        custom_complements: list[str] = []
        custom_complements_enabled: bool
        default_complements_enabled: bool
        channel_id: str = str(await self.name_to_id(ctx.channel.name))
        custom_complements_enabled, default_complements_enabled = \
            await asyncio.gather(database.are_custom_complements_enabled(userid=channel_id),
                                 database.are_default_complements_enabled(userid=channel_id))

        if custom_complements_enabled:
            custom_complements = await database.get_custom_complements(userid=channel_id)
        default_complements: list[str] = []
        if default_complements_enabled:
            default_complements = self.complements_list

        if len(custom_complements) == 0 and len(default_complements) == 0:
            # No complements to dish out
            return "", False

        default_complements_length: int = len(default_complements)
        index: int = random.randint(0, default_complements_length + len(custom_complements) - 1)
        if index < default_complements_length:
            return default_complements[index], True
        return custom_complements[index - default_complements_length], True

    async def complement_msg(self, ctx: Message, who: Optional[str] = None,
                             is_tts_muted: bool = True) -> \
            Tuple[str, bool]:
        """
        Format the complement message correctly. This includes any TTS mute prefixes and an '@' in front of the user's
            name if not included to notify them of the complement.
        :param ctx: contains the message and all info (such as the sender)
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

        awaitables: Awaitables = Awaitables([self.choose_complement(ctx)])
        complement: str
        exists: bool
        if is_tts_muted:
            tts_mute_prefix: str
            awaitables.add_task(database.get_tts_mute_prefix(channel, name_to_id=self.name_to_id))
            (complement, exists), tts_mute_prefix = await awaitables.gather()
            prefix = f"{tts_mute_prefix} {prefix}"
        else:
            complement, exists = (await awaitables.gather())[0]
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

        who: str = self.isolate_args(ctx.message.content)
        if who[0] == "@":
            who = who[1:]

        sender_id_raw: Optional[str]
        channel_id_raw: Optional[str]
        sender_id_raw, channel_id_raw = await asyncio.gather(self.name_to_id(ctx.author.name),
                                                             self.name_to_id(ctx.channel.name))
        assert sender_id_raw
        assert channel_id_raw
        sender_id: str
        channel_id: str
        sender_id, channel_id = str(sender_id_raw), str(channel_id_raw)

        awaitables: Awaitables = Awaitables([database.is_user_ignored(userid=sender_id),
                                             database.get_cmd_complement_enabled(userid=channel_id)])
        is_user_ignored: bool
        cmd_complement_enabled: bool
        is_user_ignored, cmd_complement_enabled = await awaitables.gather()

        if is_user_ignored or not cmd_complement_enabled:
            return

        comp_msg, exists = await self.complement_msg(
                ctx.message, who, await database.is_cmd_complement_muted(userid=channel_id))
        if exists:
            await ctx.channel.send(comp_msg)
            if ComplementsBot.SHOULD_LOG:
                custom_log(f"In channel {ctx.channel.name}, at {ctx.message.timestamp}, {ctx.message.author.name} "
                           f"was complemented (by command) with: {comp_msg}")

    @commands.command()
    async def compunignoreme(self, ctx: commands.Context) -> None:
        """
        Undoes the 'ignoreme' command; the user of the command will occasionally receive complements, and a direct
        complement using the 'complement' command will work.
        """

        userid: str = str(await self.name_to_id(ctx.author.name))

        await ComplementsBot.cmd_body(
                ctx,
                lambda x: True,
                None,
                ComplementsBot.DoIfElse((lambda ctx: database.is_user_ignored(userid=userid)),
                                        None,
                                        None,
                                        (lambda ctx: database.unignore(userid=userid)),
                                        None)
        )

    @commands.command()
    async def compignoreme(self, ctx: commands.Context) -> None:
        """
        The user of this command will not get any complements sent their way from ComplementsBot
        """

        userid: str = str(await self.name_to_id(ctx.author.name))

        await ComplementsBot.cmd_body(
                ctx,
                lambda x: True,
                None,
                ComplementsBot.DoIfElse((lambda ctx: database.is_user_ignored(userid=userid)),
                                        None,
                                        None,
                                        None,
                                        (lambda ctx: database.ignore(userid=userid)))
        )

    # -------------------- bot channel only commands --------------------

    async def is_in_bot_channel(self, ctx: commands.Context) -> bool:
        """
        Checks if the context was created in the bot's channel (or the creator's)
        """

        return await self.name_to_id(ctx.channel.name) in (str(self.user_id), ComplementsBot.OWNER_ID)

    @staticmethod
    async def send_and_log(ctx: commands.Context, msg: Optional[str]) -> None:
        """
        Send the message to the channel of ctx and also logs it
        """

        if msg is None:
            return

        await ctx.channel.send(msg)
        if ComplementsBot.SHOULD_LOG:
            custom_log(msg)

    class DoIfElse:
        """
        Serves as a way to store what to do in an  if/else block of a lot of the bodies of the commands
        """

        def __init__(self,
                     if_check: Union[Callable[[commands.Context], Awaitable[bool]], Callable[[commands.Context], bool]],
                     true_msg: Optional[str],
                     false_msg: Optional[str],
                     do_true: Optional[Union[
                         Callable[[commands.Context], Awaitable[None]], Callable[[commands.Context], None]]] = None,
                     do_false: Optional[Union[Callable[[commands.Context], Awaitable[None]], Callable[
                         [commands.Context], None]]] = None) -> None:
            """
            :param if_check: what the condition for entering 'if' statement is
            :param do_true: what to do when the if_check succeeds (done before sending message to chat);
                if 'None', does nothing
            :param true_msg: what to send to chat when the 'if' if_check succeeds; any occurrence of
                complements_bot.F_USER in the string is replaced with the name of the user in chat who called the
                original command
            :param do_false: what to do when if_check fails (done before sending message to chat);
                if 'None', does nothing
            :param false_msg: what to send to chat when the if_check fails; any occurrence of complements_bot.F_USER
                in the string is replaced with the name of the user in chat who called the original command
            """

            self.if_check: Union[Callable[[commands.Context], Awaitable[bool]], Callable[[commands.Context], bool]] \
                = if_check
            self.true_msg: Optional[str] = true_msg
            self.false_msg: Optional[str] = false_msg

            self.do_true: Union[Callable[[commands.Context], Awaitable[None]], Callable[
                [commands.Context], None]] = do_true or (
                lambda ctx: None)
            self.do_false: Union[Callable[[commands.Context], None], Callable[
                [commands.Context], Awaitable[None]]] = do_false or (
                lambda ctx: None)

    @staticmethod
    async def cmd_body(ctx: commands.Context,
                       permission_check: Union[
                           Callable[[commands.Context], bool], Callable[[commands.Context], Awaitable[bool]]],
                       do_always: Optional[
                           Union[Callable[[commands.Context], Awaitable[None]], Callable[[commands.Context], None]]] = None,
                       do_if_else: Optional[DoIfElse] = None,
                       always_msg: Optional[str] = None) -> bool:
        """
        The main structure in which commands sent to the bot's channel need to be processed
        :param ctx: context from the original call
        :param permission_check: who is allowed to run the command in question
        :param do_always: this is always ASYNCHRONOUSLY called if permission_check passes; if 'None', does nothing
        :param do_if_else: specifies the if condition on which to enter the if block, what to do in the if and else
            blocks, and the messages to send in either block; if None, all if/else logic is skipped
        :param always_msg: message to always send to chat (after do_before_if and do_if_else); if None, send nothing;
            any occurrence of ComplementsBot.F_USER in the string is replaced with the name of the user in chat who
            called the original command
        :return: True if permission_check passes, False otherwise
        """

        awaitables: Awaitables = Awaitables([])

        user: str = ctx.author.name

        permission_check_task: asyncio.Task = asyncio.create_task(run_with_appropriate_awaiting(permission_check, ctx))

        if do_if_else is not None:
            permission_check_res, if_check_res = await asyncio.gather(permission_check_task,
                                                                      run_with_appropriate_awaiting(do_if_else.if_check, ctx))
            if not permission_check_res:
                return False

            to_send: Optional[str] = None
            if if_check_res:
                awaitables.add_task(run_with_appropriate_awaiting(do_if_else.do_true, ctx))
                if do_if_else.true_msg:
                    to_send = do_if_else.true_msg.replace(ComplementsBot.F_USER, user)
            else:
                awaitables.add_task(run_with_appropriate_awaiting(do_if_else.do_false, ctx))
                if do_if_else.false_msg:
                    to_send = do_if_else.false_msg.replace(ComplementsBot.F_USER, user)
            awaitables.add_task(ComplementsBot.send_and_log(ctx, to_send))
        elif not await permission_check_task:
            return False

        if always_msg is not None:
            to_send = always_msg.replace(ComplementsBot.F_USER, user)
            awaitables.add_task(ComplementsBot.send_and_log(ctx, to_send))

        awaitables.add_task(run_with_appropriate_awaiting(do_always, ctx))
        await awaitables.gather()

        return True

    @commands.command()
    async def joinme(self, ctx: commands.Context) -> None:
        """
        Get the bot to join the user's channel and start complementing people in their channel.
        Also used to reset channel name if streamer changed their username
        """

        raw_userid: Optional[str] = str(await self.name_to_id(ctx.author.name))
        assert raw_userid
        userid: str = str(raw_userid)
        old_username: Optional[str] = await database.get_username(userid=userid)

        async def do_false(ctx: commands.Context) -> None:
            # Have to save to database and update in memory so bot starts working straight away

            awaitables: Awaitables = Awaitables([])
            if not await database.is_channel_joined(userid=userid):
                awaitables.add_task(database.join_channel(userid=userid, username=ctx.author.name))
            elif ctx.author.name != old_username:
                awaitables.add_task(self.part_channels([old_username]))
                awaitables.add_task(database.set_username(ctx.author.name, userid=userid))
            awaitables.add_task(self.join_channels([ctx.author.name]))
            await awaitables.gather()

        async def if_check(ctx: commands.Context) -> bool:
            return (await database.is_channel_joined(userid=userid)
                    and ctx.author.name == old_username)

        await ComplementsBot.cmd_body(
                ctx,
                self.is_in_bot_channel,
                None,
                ComplementsBot.DoIfElse(if_check,
                                        f"@{ComplementsBot.F_USER} I am already in your channel!",
                                        f"@{ComplementsBot.F_USER} I have joined your channel!",
                                        None,
                                        do_false
                                        )
        )

    @commands.command()
    async def leaveme(self, ctx: commands.Context) -> None:
        """
        Bot leaves the user's channel and no longer complements chatters there.
        """

        userid: str = str(await self.name_to_id(ctx.author.name))

        async def do_true(ctx: commands.Context) -> None:
            # Update database and in realtime for "instant" effect
            awaitables: Awaitables = Awaitables([database.leave_channel(userid=userid),
                                                 self.part_channels([ctx.author.name])])
            await awaitables.gather()

        await ComplementsBot.cmd_body(
                ctx,
                self.is_in_bot_channel,
                None,
                ComplementsBot.DoIfElse((lambda ctx: database.is_channel_joined(userid=userid)),
                                        f"@{ComplementsBot.F_USER} I have left your channel; I would appreciate it if "
                                        f"you let me know why you asked me to leave! You can contact me in one of three ways: "
                                        f"DM ComplementsBot right here on Twitch; DM Ereiarrus on Twitch"
                                        f"(https://www.twitch.tv/ereiarrus) or Discord Ereiarrus#2900. Thank you!",
                                        f"@{ComplementsBot.F_USER} I have not joined your channel.",
                                        do_true,
                                        None
                                        )
        )

    @commands.command()
    async def deleteme(self, ctx: commands.Context) -> None:
        """
        Same as the 'leaveme' command, but on top, also delete any records of the user (e.g. custom complements)
        """

        userid: str = str(await self.name_to_id(ctx.author.name))

        async def do_true(ctx: commands.Context) -> None:
            # Remove any user records from database and leave their channel NOW
            awaitables: Awaitables = Awaitables([database.delete_channel(userid=userid),
                                                 self.part_channels([ctx.author.name])])
            await awaitables.gather()

        await ComplementsBot.cmd_body(
                ctx,
                self.is_in_bot_channel,
                None,
                ComplementsBot.DoIfElse((lambda ctx: database.channel_exists(userid=userid)),
                                        f"@{ComplementsBot.F_USER} I have deleted your channel data; I would appreciate it if "
                                        f"you let me know why you asked me to leave! You can contact me in one of three ways: "
                                        f"DM ComplementsBot right here on Twitch; DM Ereiarrus on Twitch"
                                        f"(https://www.twitch.tv/ereiarrus) or Discord Ereiarrus#2900. Thank you!",
                                        f"@{ComplementsBot.F_USER} your channel does not exists in my records.",
                                        do_true,
                                        None
                                        )
        )

    @commands.command()
    async def ignoreme(self, ctx: commands.Context) -> None:
        """
        The user of this command will not get any complements sent their way from ComplementsBot
        """

        userid: str = str(await self.name_to_id(ctx.author.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_in_bot_channel,
                None,
                ComplementsBot.DoIfElse((lambda ctx: database.is_user_ignored(userid=userid)),
                                        f"@{ComplementsBot.F_USER} I am already ignoring you.",
                                        f"@{ComplementsBot.F_USER} I am now ignoring you.",
                                        None,
                                        (lambda ctx: database.ignore(userid=userid)))
        )

    @commands.command()
    async def unignoreme(self, ctx: commands.Context) -> None:
        """
        Undoes the 'ignoreme' command; the user of the command will occasionally receive complements, and a direct
        complement using the 'complement' command will work.
        """

        userid: str = str(await self.name_to_id(ctx.author.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_in_bot_channel,
                None,
                ComplementsBot.DoIfElse((lambda ctx: database.is_user_ignored(userid=userid)),
                                        f"@{ComplementsBot.F_USER} I am no longer ignoring you!",
                                        f"@{ComplementsBot.F_USER} I am not ignoring you!",
                                        (lambda ctx: database.unignore(userid=userid)),
                                        None)
        )

    @commands.command()
    async def count(self, ctx: commands.Context) -> None:
        """
        Shows the number of channels that the bot is active in
        """

        await ComplementsBot.cmd_body(
                ctx,
                self.is_in_bot_channel,
                always_msg=f"! @{ComplementsBot.F_USER} "
                           f"{str(await database.number_of_joined_channels())} channels and counting!"
        )

    @commands.command()
    async def about(self, ctx: commands.Context) -> None:
        """
        Shows some information about the bot
        """

        await ComplementsBot.cmd_body(
                ctx,
                self.is_in_bot_channel,
                always_msg=f"! @{ComplementsBot.F_USER} "
                           "For most up-to-date information on commands, please have a look at "
                           "https://github.com/Ereiarrus/ComplementsBotPy#readme "
                           "and for most up-to-date complements, have a look at "
                           "https://github.com/Ereiarrus/ComplementsBotPy/blob/main/complements_list.txt"
        )

    # --------------------  must be by streamer/mods --------------------

    def is_by_broadcaster_or_mod(self, ctx: commands.Context) -> bool:
        """
        Checks if the user who created the context is the streamer or a mod in the channel
        (the bot itself and creator also has this permission)
        """

        return ctx.author.is_broadcaster or ctx.author.is_mod or ctx.author.name in (
            self.nick, ComplementsBot.OWNER_NICK)

    @commands.command()
    async def setchance(self, ctx: commands.Context) -> None:
        """
        Change how likely it is that person sending message gets complemented by random.
        The number given can be any valid float number, with anything 100 or above guaranteeing a complement, and 0 and
            below guaranteeing no complement.
        """

        if not self.is_by_broadcaster_or_mod(ctx):
            return

        channel: str = ctx.channel.name
        to_send: str
        exception: bool = False
        chance_str: str = self.isolate_args(ctx.message.content)
        chance: float
        try:
            chance = float(chance_str)
        except ValueError:
            # user tried putting a non-float after '!setchance'
            to_send = f"@{channel} '{chance_str}' is an invalid number. Please try again."
            exception = True
        except IndexError:
            # user didn't provide anything after '!setchance'
            to_send = f"@{channel} You did not enter a number. Please try again."
            exception = True
        if exception:
            await ComplementsBot.send_and_log(ctx, to_send)
            return

        to_send = f"@{channel} complement chance set to {chance}!"
        awaitables: Awaitables = Awaitables([database.set_complement_chance(chance, channel, name_to_id=self.name_to_id),
                                             ComplementsBot.send_and_log(ctx, to_send)])
        await awaitables.gather()

    @commands.command(aliases=["disablecommandcomplement", "disablecommandcomp", "disablecmdcomp"])
    async def disablecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Prevent chatter from being able to use the !complement command in user's channel
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.get_cmd_complement_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} your viewers will no longer be able to make use of the "
                        f"!complement command.",
                        f"@{ComplementsBot.F_USER} your viewers already cannot make use of the !complement command.",
                        (lambda ctx: database.set_cmd_complement_enabled(False, userid=userid)),
                        None
                )
        )

    @commands.command(aliases=["enablecommandcomplement", "enablecommandcomp", "enablecmdcomp"])
    async def enablecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Allow chatters in user's chat to use the !complement command
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.get_cmd_complement_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} your viewers can already make use of the !complement command!",

                        f"@{ComplementsBot.F_USER} your viewers will now be able to make use of the !complement command!",
                        None,
                        (lambda ctx: database.set_cmd_complement_enabled(True, userid=userid))
                )
        )

    @commands.command(aliases=["disablerandcomplement", "disablerandcomp", "disablerandomcomp"])
    async def disablerandomcomplement(self, ctx: commands.Context) -> None:
        """
        Prevent the bot from randomly complementing chatters in user's chat
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.get_random_complement_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} your viewers will no longer randomly receive complements.",
                        f"@{ComplementsBot.F_USER} your viewers already do not randomly receive complements.",
                        (lambda ctx: database.set_random_complement_enabled(False, userid=userid)),
                        None
                )
        )

    @commands.command(aliases=["enablerandcomplement", "enablerandcomp", "enablerandomcomp"])
    async def enablerandomcomplement(self, ctx: commands.Context) -> None:
        """
        Allow the bot to randomly complement chatters in user's chat
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.get_random_complement_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} I already randomly send out complements!",
                        f"@{ComplementsBot.F_USER} your viewers will now randomly receive complements!",
                        None,
                        (lambda ctx: database.set_random_complement_enabled(True, userid=userid))
                )
        )

    @commands.command(aliases=["addcomp"])
    async def addcomplement(self, ctx: commands.Context) -> None:
        """
        Add a complement for user's chat only that might be chosen to complement the user's chatters
        """

        if not self.is_by_broadcaster_or_mod(ctx):
            return

        msg: str = ctx.message.content.strip()
        # Anything after the space after '!addcomplement' is counted as being the complement
        complement: str = msg[msg.find(" ") + 1:]
        user: str = ctx.channel.name
        if len(complement) > ComplementsBot.MAX_COMPLEMENT_LENGTH:
            to_send: str = f"@{user} complement is too long. It may not be over " \
                           f"{ComplementsBot.MAX_COMPLEMENT_LENGTH} characters long."
            await ComplementsBot.send_and_log(ctx, to_send)
            return

        awaitables: Awaitables = \
            Awaitables([database.add_complement(complement, user, name_to_id=self.name_to_id),
                        ComplementsBot.send_and_log(ctx, f"@{user} new complements added: '{complement}'")])
        await awaitables.gather()

    @commands.command(aliases=["listcomps"])
    async def listcomplements(self, ctx: commands.Context) -> None:
        """
        Show the user all of their custom complements.
        Due to Twitch having a maximum message length, these might have to be sent over more than one message, so it is
            split to make sure all complements are visible.
        """

        if not self.is_by_broadcaster_or_mod(ctx):
            return

        user: str = ctx.channel.name
        custom_complements: list[str] = await database.get_custom_complements(user, name_to_id=self.name_to_id)
        comps_msg: str = '"' + '", "'.join(custom_complements) + '"'

        msgs: list[str] = textwrap.wrap(f"@{user} complements: {comps_msg}", ComplementsBot.DEFAULT_MAX_MSG_LEN)

        msg: str
        if len(custom_complements) > 0:
            for msg in msgs:
                await ComplementsBot.send_and_log(ctx, msg)
        else:
            msg = f"@{user} No complements found."
            await ComplementsBot.send_and_log(ctx, msg)

    @commands.command(aliases=["removecomp"])
    async def removecomplement(self, ctx: commands.Context) -> None:
        """
        Remove a custom complement, and show the ones that were removed (similarly to !listallcomplements, this might
            require splitting the message into multiple messages due to length limit).
        all non-alphanumeric symbols are removed from anything coming after '!removecomplement ' and compared to all
            the user's custom complements after having all non-alphanumeric symbols removed from them also. All custom
            complements containing as a substring what the user wanted to remove are removed from the user's custom
            complements list.
        """

        if not self.is_by_broadcaster_or_mod(ctx):
            return

        msg: str = ctx.message.content.strip()
        phrase: str = remove_chars(msg[msg.find(" ") + 1:], regex=r"[^a-z0-9]")
        user: str = ctx.channel.name

        userid: str = str(await self.name_to_id(ctx.channel.name))
        to_remove_comps, to_keep_comps = database.complements_to_remove(
                await database.get_custom_complements(userid=userid), phrase)
        await database.remove_complements(userid=userid, to_keep=to_keep_comps)

        removed_comps_msg: str = '"' + '", "'.join(to_remove_comps) + '"'

        # if message goes over length limit, send it over multiple messages
        msgs: list[str] = textwrap.wrap(f"@{user} complement/s removed: {removed_comps_msg}",
                                        ComplementsBot.DEFAULT_MAX_MSG_LEN)

        send_msg: str
        if len(to_remove_comps) > 0:
            for send_msg in msgs:
                await ComplementsBot.send_and_log(ctx, send_msg)
        else:
            send_msg = f"@{user} No complements with that phrase found."
            await ComplementsBot.send_and_log(ctx, send_msg)

    @commands.command(aliases=["removeallcomps"])
    async def removeallcomplements(self, ctx: commands.Context) -> None:
        """
        Remove all custom complements a user has added
        """

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                (lambda ctx: database.remove_all_complements(ctx.channel.name, name_to_id=self.name_to_id)),
                None,
                f"@{ComplementsBot.F_USER} all of your custom complements have been removed.")

    @commands.command()
    async def setmutettsprefix(self, ctx: commands.Context) -> None:
        """
        Set the character/string to put in front of a message to mute TTS
        """

        if not self.is_by_broadcaster_or_mod(ctx):
            return

        msg: str = ctx.message.content
        msg = msg.strip()
        prefix: str = msg[msg.find(" ") + 1:]
        awaitables: Awaitables = \
            Awaitables([database.set_tts_mute_prefix(prefix, ctx.channel.name, name_to_id=self.name_to_id),
                        ComplementsBot.send_and_log(ctx, f"@{ctx.author.name} mute TTS prefix changed to '{prefix}'.")])
        await awaitables.gather()

    @commands.command(aliases=["mutecommandcomplement", "mutecommandcomp", "mutecmdcomp"])
    async def mutecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Mutes TTS for complements sent with !complement command
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.is_cmd_complement_muted(userid=userid)),
                        f"@{ComplementsBot.F_USER} command complements are already muted!",
                        f"@{ComplementsBot.F_USER} command complements are now muted.",
                        None,
                        (lambda ctx: database.set_cmd_complement_is_muted(True, userid=userid))
                )
        )

    @commands.command(aliases=["muterandcomplement", "muterandcomp", "muterandomcomp"])
    async def muterandomcomplement(self, ctx: commands.Context) -> None:
        """
        Mutes TTS for complements given out randomly
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.are_random_complements_muted(userid=userid)),
                        f"@{ComplementsBot.F_USER} random complements are already muted!",
                        f"@{ComplementsBot.F_USER} random complements are now muted.",
                        None,
                        (lambda ctx: database.set_random_complements_are_muted(True, userid=userid))
                )
        )

    @commands.command(aliases=["unmutecommandcomplement", "unmutecommandcomp", "unmutecmdcomp"])
    async def unmutecmdcomplement(self, ctx: commands.Context) -> None:
        """
        Unmutes TTS for complements sent with !complement command
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.is_cmd_complement_muted(userid=userid)),
                        f"@{ComplementsBot.F_USER} command complements are no longer muted!",
                        f"@{ComplementsBot.F_USER} command complements are already unmuted!",
                        (lambda ctx: database.set_cmd_complement_is_muted(False, userid=userid)),
                        None
                )
        )

    @commands.command(aliases=["unmuterandcomplement", "unmuterandcomp", "unmuterandomcomp"])
    async def unmuterandomcomplement(self, ctx: commands.Context) -> None:
        """
        Unmutes TTS for complements given out randomly
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.are_random_complements_muted(userid=userid)),
                        f"@{ComplementsBot.F_USER} random complements are no longer muted!",
                        f"@{ComplementsBot.F_USER} random complements are already unmuted!",
                        (lambda ctx: database.set_random_complements_are_muted(False, userid=userid)),
                        None
                )
        )

    @commands.command(aliases=["enablecustomcomps"])
    async def enablecustomcomplements(self, ctx: commands.Context) -> None:
        """
        All custom complements will be added to the pool that we choose complements for chatters from
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.are_custom_complements_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} custom complements are already enabled!",
                        f"@{ComplementsBot.F_USER} custom complements are now enabled!",
                        None,
                        (lambda ctx: database.set_are_custom_complements_enabled(True, userid=userid))
                )
        )

    @commands.command(aliases=["enabledefaultcomps"])
    async def enabledefaultcomplements(self, ctx: commands.Context) -> None:
        """
        All default complements will be added to the pool that we choose complements for chatters from
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.are_default_complements_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} default complements are already enabled!",
                        f"@{ComplementsBot.F_USER} default complements are now enabled!",
                        None,
                        (lambda ctx: database.set_are_default_complements_enabled(True, userid=userid))
                )
        )

    @commands.command(aliases=["disablecustomcomps"])
    async def disablecustomcomplements(self, ctx: commands.Context) -> None:
        """
        All custom complements will be removed from the pool that we choose complements for chatters from; this does NOT
            delete the custom complements.
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.are_custom_complements_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} custom complements are now disabled.",
                        f"@{ComplementsBot.F_USER} custom complements are already disabled.",
                        (lambda ctx: database.set_are_custom_complements_enabled(False, userid=userid)),
                        None
                )
        )

    @commands.command(aliases=["disabledefaultcomps"])
    async def disabledefaultcomplements(self, ctx: commands.Context) -> None:
        """
        All default complements will be removed from the pool that we choose complements for chatters from
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.are_default_complements_enabled(userid=userid)),
                        f"@{ComplementsBot.F_USER} default complements are now disabled.",
                        f"@{ComplementsBot.F_USER} default complements are already disabled!",
                        (lambda ctx: database.set_are_default_complements_enabled(False, userid=userid)),
                        None
                )
        )

    @commands.command(aliases=["unignorebot"])
    async def unignorebots(self, ctx: commands.Context) -> None:
        """
        Chatters that count as bots might be complemented by ComplementsBot
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.is_ignoring_bots(userid=userid)),
                        f"@{ComplementsBot.F_USER} bots have a chance of being complemented!",
                        f"@{ComplementsBot.F_USER} bots can already get complements!",
                        (lambda ctx: database.set_should_ignore_bots(False, userid=userid)),
                        None
                )
        )

    @commands.command(aliases=["ignorebot"])
    async def ignorebots(self, ctx: commands.Context) -> None:
        """
        Chatters that count as bots will not be complemented by ComplementsBot
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        await ComplementsBot.cmd_body(
                ctx,
                self.is_by_broadcaster_or_mod,
                None,
                ComplementsBot.DoIfElse(
                        (lambda ctx: database.is_ignoring_bots(userid=userid)),
                        f"@{ComplementsBot.F_USER} bots are already not getting complements.",
                        f"@{ComplementsBot.F_USER} bots will no longer get complemented.",
                        None,
                        (lambda ctx: database.set_should_ignore_bots(True, userid=userid))
                )
        )

    @commands.command(aliases=["compleaveme"])
    async def compleave(self, ctx: commands.Context) -> None:
        """
        Allows the user to kick ComplementsBot out of their channel from their own channel chat
        """

        userid: str = str(await self.name_to_id(ctx.channel.name))

        async def do_true(ctx: commands.Context) -> None:
            # Update database and in realtime for "instant" effect
            awaitables: Awaitables = Awaitables([database.leave_channel(userid=userid),
                                                 self.part_channels([ctx.channel.name])])
            await awaitables.gather()

        await ComplementsBot.cmd_body(
                ctx,
                (lambda ctx: ctx.author.name == ctx.channel.name),
                None,
                ComplementsBot.DoIfElse((lambda ctx: database.is_channel_joined(userid=userid)),
                                        f"@{ComplementsBot.F_USER} I have left your channel.",
                                        f"@{ComplementsBot.F_USER} I have not joined your channel.",
                                        do_true,
                                        None
                                        )
        )

    @staticmethod
    def isolate_args(full_cmd_msg: str) -> str:
        """
        :param full_cmd_msg: the command message which includes the command name itself
        :return: removes the '!command' part of the msg along with exactly one single space after it
        """

        full_cmd_msg = full_cmd_msg.strip()
        # ^ Twitch should already do this before getting
        # the message, but just done in case they don't

        first_space_at: int = full_cmd_msg.find(" ")
        space_found: bool = first_space_at >= 0

        if not space_found:
            return ""

        # won't give 'index out of range' as message can't end on a space due to the strip()
        return full_cmd_msg[first_space_at + 1:]
