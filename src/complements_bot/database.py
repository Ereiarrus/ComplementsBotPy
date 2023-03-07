"""
The API through which items in our database are accessed
"""

import asyncio
from typing import Any, Dict, Tuple, Optional, Callable, Awaitable, Union
from firebase_admin import credentials, db, initialize_app
from src.env_reader import databaseURL
from .utilities import run_with_appropriate_awaiting, remove_chars


_cred: credentials.Certificate
try:
    _cred = credentials.Certificate("src/.firebase_config.json")
except IOError:
    _cred = credentials.Certificate(".firebase_config.json")
initialize_app(_cred, {'databaseURL': databaseURL})

REF: db.Reference = db.reference('/')
IGNORED_DB_REF: db.Reference = REF.child('Ignored')
USERS_DB_REF: db.Reference = REF.child('Users')

_event_loop = asyncio.get_event_loop()

_REF: db.Reference = db.reference('/')
_IGNORED_DB_REF: db.Reference = _REF.child('Ignored')
_USERS_DB_REF: db.Reference = _REF.child('Users')

# Default values for database:
_DEFAULT_COMPLEMENT_CHANCE: float = 10.0 / 3.0
_DEFAULT_SHOULD_IGNORE_BOTS: bool = True
_DEFAULT_TTS_IGNORE_PREFIX: str = "!"
_DEFAULT_COMMAND_COMPLEMENT_ENABLED: bool = True
_DEFAULT_RANDOM_COMPLEMENT_ENABLED: bool = True
_DEFAULT_COMMAND_COMPLEMENT_MUTED: bool = True
_DEFAULT_RANDOM_COMPLEMENT_MUTED: bool = False
_DEFAULT_IS_JOINED: bool = True
_DEFAULT_DEFAULT_COMPLEMENTS_ENABLED: bool = True
_DEFAULT_CUSTOM_COMPLEMENTS_ENABLED: bool = True

# Database keys:
_COMPLEMENT_CHANCE: str = "complement_chance"
_SHOULD_IGNORE_BOTS: str = "should_ignore_bots"
_IS_JOINED: str = "is_joined"
_MUTE_PREFIX: str = "tts_ignore_prefix"
_COMMAND_COMPLEMENT_ENABLED: str = "command_complement_enabled"
_RANDOM_COMPLEMENT_ENABLED: str = "random_complement_enabled"
_CUSTOM_COMPLEMENTS: str = "custom_complements"
_COMMAND_COMPLEMENT_MUTED: str = "command_complement_muted"
_RANDOM_COMPLEMENT_MUTED: str = "random_complement_muted"
_DEFAULT_COMPLEMENTS_ENABLED: str = "default_complements_enabled"
_CUSTOM_COMPLEMENTS_ENABLED: str = "custom_complements_enabled"
_USERNAME: str = "last_known_username"

_DEFAULT_USER: Dict[str, Any] = {_COMPLEMENT_CHANCE: _DEFAULT_COMPLEMENT_CHANCE,
                                 _SHOULD_IGNORE_BOTS: _DEFAULT_SHOULD_IGNORE_BOTS,
                                 _IS_JOINED: _DEFAULT_IS_JOINED,
                                 _COMMAND_COMPLEMENT_ENABLED: _DEFAULT_COMMAND_COMPLEMENT_ENABLED,
                                 _RANDOM_COMPLEMENT_ENABLED: _DEFAULT_RANDOM_COMPLEMENT_ENABLED,
                                 _MUTE_PREFIX: _DEFAULT_TTS_IGNORE_PREFIX,
                                 _COMMAND_COMPLEMENT_MUTED: _DEFAULT_COMMAND_COMPLEMENT_MUTED,
                                 _RANDOM_COMPLEMENT_MUTED: _DEFAULT_RANDOM_COMPLEMENT_MUTED,
                                 _CUSTOM_COMPLEMENTS_ENABLED: _DEFAULT_CUSTOM_COMPLEMENTS_ENABLED,
                                 _DEFAULT_COMPLEMENTS_ENABLED: _DEFAULT_DEFAULT_COMPLEMENTS_ENABLED
                                 }


class Database:
    """
    The way to interact with the database
    """

    def __init__(self,
                 name_to_id: Union[Callable[[str], str], Callable[[str], Awaitable[str]]],
                 id_to_name: Union[Callable[[str], str], Callable[[str], Awaitable[str]]]) -> None:
        self.name_to_id_init: Union[Callable[[str], str], Callable[[str], Awaitable[str]]] = name_to_id
        self.id_to_name_init: Union[Callable[[str], str], Callable[[str], Awaitable[str]]] = id_to_name

    async def name_to_id(self, name: str) -> Optional[str]:
        """
        :param name: the username of the user whose user id we want
        :return: the user id of the specified user, if the user exists; otherwise 'None'
        """
        return await run_with_appropriate_awaiting(self.name_to_id_init, name)

    async def id_to_name(self, uid: str) -> Optional[str]:
        """
        :param uid: the user id of the user whose username we want
        :return: the username of the specified user, if the user exists; otherwise 'None'
        """
        return await run_with_appropriate_awaiting(self.id_to_name_init, uid)


async def is_user_ignored(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
    Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) \
        -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether the specified user is ignored from getting complements or not
    """

    assert username or userid
    assert userid or name_to_id

    users: list[str] = await _event_loop.run_in_executor(None, _IGNORED_DB_REF.get)
    if users is None:
        # No ignored users exist
        return False

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)

    return userid in users


async def ignore(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Adds the user to the ignored users list (so that they can't be complemented)
    """
    assert username or userid
    assert userid or name_to_id

    def ignore_transaction(data: list[str]) -> list[str]:
        if data is None:
            data = []
        if userid is not None:
            data.append(userid)
        return data

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)

    await _event_loop.run_in_executor(None, _IGNORED_DB_REF.transaction, ignore_transaction)


async def unignore(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Removes the user from the ignored users list (so that they can be complemented)
    """
    assert username or userid
    assert userid or name_to_id

    def unignore_transaction(data: list[str]) -> list[str]:
        if userid:
            data.remove(userid)
        return data

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)

    await _event_loop.run_in_executor(None, _IGNORED_DB_REF.transaction, unignore_transaction)


async def channel_exists(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether the channel has an entry in the database of ever being joined by the bot
    """
    assert username or userid
    assert userid or name_to_id

    users = await _event_loop.run_in_executor(None, _USERS_DB_REF.get, False, True)
    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    return (users is not None) and userid in users


async def is_channel_joined(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether the bot is active in the channel
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    if not await channel_exists(userid=userid):
        return False

    return bool(await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_IS_JOINED).get))


async def join_channel(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    The user is added to the database (if not already there) and marked as having the bot active in their chat
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    if not await channel_exists(userid=userid):
        await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).set, _DEFAULT_USER)
        await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_USERNAME).set, username)
    else:
        await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_IS_JOINED).set, True)


async def leave_channel(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    The bot is marked as inactive in the user's channel
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_IS_JOINED).set, False)


async def delete_channel(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Deletes any mention of the channel from the database; does not affect ignored users
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).delete)


async def get_joined_channels() -> list[str]:
    """
    :return: a list of all joined channels (in the form of a list of user IDs) where the bot is currently active
    """

    all_users = await _event_loop.run_in_executor(None, _USERS_DB_REF.get, False, True)
    joined_users: list[str] = []
    if all_users is None:
        return joined_users
    for user in all_users:
        if await _event_loop.run_in_executor(None, _USERS_DB_REF.child(user).child(_IS_JOINED).get):
            joined_users.append(user)
    return joined_users


async def number_of_joined_channels() -> int:
    """
    :return: The number of joined channels where the bot is currently active
    """
    return len(await get_joined_channels())


async def set_tts_mute_prefix(prefix: str, username: Optional[str] = None, userid: Optional[str] = None,
                              name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                  [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param prefix: the new prefix for messages so that they are muted on tts
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Changes the character that is prepended to messages so that tts does not pick them up
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_MUTE_PREFIX).set, prefix)


async def get_tts_mute_prefix(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> str:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: the currently set prefix that mutes tts
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    prefix = await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_MUTE_PREFIX).get)
    if prefix is None:
        await set_tts_mute_prefix(_DEFAULT_TTS_IGNORE_PREFIX, userid=userid)
        prefix = _DEFAULT_TTS_IGNORE_PREFIX
    return prefix


async def set_complement_chance(chance: float, username: Optional[str] = None, userid: Optional[str] = None,
                                name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                    [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param chance: what the new chance (in percentage) of being complemented at random should be
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Updates the chance of being randomly complemented by the bot
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_COMPLEMENT_CHANCE).set, chance)


async def get_complement_chance(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> float:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: the currently set chance (in percents) of being randomly complemented
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    chance = await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_COMPLEMENT_CHANCE).get)
    if chance is None:
        await set_complement_chance(_DEFAULT_COMPLEMENT_CHANCE, userid=userid)
        chance = _DEFAULT_COMPLEMENT_CHANCE
    return chance


async def set_cmd_complement_enabled(is_enabled: bool, username: Optional[str] = None, userid: Optional[str] = None,
                                     name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                         [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param is_enabled: the new state of whether !complement command can be used
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    updates the status of whether chatters are allowed to complement other using the !complement command
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_COMMAND_COMPLEMENT_ENABLED).set,
                                      is_enabled)


async def get_cmd_complement_enabled(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether chatters may use the !complement command
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    is_enabled = await _event_loop.run_in_executor(
        None, _USERS_DB_REF.child(userid).child(_COMMAND_COMPLEMENT_ENABLED).get)
    if is_enabled is None:
        await set_cmd_complement_enabled(_DEFAULT_COMMAND_COMPLEMENT_ENABLED, userid=userid)
        is_enabled = _DEFAULT_COMMAND_COMPLEMENT_ENABLED
    return is_enabled


async def set_random_complement_enabled(is_enabled: bool, username: Optional[str] = None, userid: Optional[str] = None,
                                        name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                            [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param is_enabled: is the bot allowed to complement chatters at random
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Marks in the DB whether the bot may complement chatters at random
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_RANDOM_COMPLEMENT_ENABLED).set,
                                      is_enabled)


async def get_random_complement_enabled(username: Optional[str] = None, userid: Optional[str] = None,
                                        name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                            [str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: Whether the bot is allowed to randomly complement chatters
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    is_enabled = await _event_loop.run_in_executor(None,
                                                   _USERS_DB_REF.child(userid).child(_RANDOM_COMPLEMENT_ENABLED).get)
    if is_enabled is None:
        await set_random_complement_enabled(_DEFAULT_RANDOM_COMPLEMENT_ENABLED, userid=userid)
        is_enabled = _DEFAULT_RANDOM_COMPLEMENT_ENABLED
    return is_enabled


async def add_complement(complement: str, username: Optional[str] = None, userid: Optional[str] = None,
                         name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                             [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param complement: the new custom complement to be added
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Adds a custom complement to the DB
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)

    def add_transaction(data):
        if data is None:
            data = []
        data.append(complement)
        return data

    await _event_loop.run_in_executor(
        None, _USERS_DB_REF.child(userid).child(_CUSTOM_COMPLEMENTS).transaction, add_transaction)


def complements_to_remove(data: list[str], phrase: str) -> Tuple[list[str], list[str]]:
    """
    :param data: The list of items we are selecting items to keep/remove from
    :param phrase: the phrase that tells us which items in 'data' we want to get rid of
    :return: Tuple of (complements that we removed, complements that we kept)
    """
    if data is None:
        data = []

    leftover_comps = []
    removed_comps = []
    for comp in data:
        comp_edit = remove_chars(comp, regex=r"[^a-z0-9]")
        if phrase in comp_edit:
            removed_comps.append(comp)
        else:
            leftover_comps.append(comp)

    return removed_comps, leftover_comps


async def remove_complements(username: Optional[str] = None, userid: Optional[str] = None,
                             to_keep: Optional[list[str]] = None, to_remove: Optional[list[str]] = None,
                             name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                 [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change.
    Either provide to_remove or to_keep; if both given, to_remove takes precedence
    :param to_remove: blacklist of custom complements to be removed
    :param to_keep: whitelist of custom complements to be kept
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Removes all complements in 'to_remove', or those not in 'to_keep', with blacklist ('to_remove') taking precedence
    if both specified
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)

    def remove_transaction(data):
        if to_remove:
            for comp in to_remove:
                data.remove(comp)
            return data
        return to_keep or []

    await _event_loop.run_in_executor(
        None, _USERS_DB_REF.child(userid).child(_CUSTOM_COMPLEMENTS).transaction, remove_transaction)


async def remove_all_complements(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Deletes all of a user's custom complements
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_CUSTOM_COMPLEMENTS).delete)


async def get_custom_complements(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> list[str]:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: all of a user's custom complements
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    complements = await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_CUSTOM_COMPLEMENTS).get)
    return complements or []


async def is_cmd_complement_muted(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether chatters are allowed to use the !complement command
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    is_muted = await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_COMMAND_COMPLEMENT_MUTED).get)
    if is_muted is None:
        return _DEFAULT_COMMAND_COMPLEMENT_MUTED
    return bool(is_muted)


async def set_cmd_complement_is_muted(is_muted: bool, username: Optional[str] = None, userid: Optional[str] = None,
                                      name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                          [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param is_muted: if command complements (!complement <user>) should be muted by tts
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    allows the changing of the tts muted status of command complements (!complement <user>)
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_COMMAND_COMPLEMENT_MUTED).set, is_muted)


async def are_random_complements_muted(username: Optional[str] = None, userid: Optional[str] = None,
                                       name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                           [str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether random complements are muted for tts
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    is_muted = await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_RANDOM_COMPLEMENT_MUTED).get)
    if is_muted is None:
        return _DEFAULT_RANDOM_COMPLEMENT_MUTED
    return bool(is_muted)


async def set_random_complements_are_muted(are_muted: bool, username: Optional[str] = None,
                                           userid: Optional[str] = None, name_to_id: Optional[
            Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param are_muted: new state for if random complements should be muted for the sake of tts
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    allows the changing of the tts muted status of randomly given out complements
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_RANDOM_COMPLEMENT_MUTED).set, are_muted)


async def are_default_complements_enabled(username: Optional[str] = None, userid: Optional[str] = None,
                                          name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                              [str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether the bot should be using any of the default complements
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    is_enabled = await _event_loop.run_in_executor(
        None, _USERS_DB_REF.child(userid).child(_DEFAULT_COMPLEMENTS_ENABLED).get)
    if is_enabled is None:
        return _DEFAULT_DEFAULT_COMPLEMENTS_ENABLED
    return bool(is_enabled)


async def set_are_default_complements_enabled(are_enabled: bool, username: Optional[str] = None,
                                              userid: Optional[str] = None, name_to_id: Optional[
            Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param are_enabled: new status for if the bot is allowed make use of the default complements
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Allows changing of whether the bot is allowed to make use of the default complements
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(
        None, _USERS_DB_REF.child(userid).child(_DEFAULT_COMPLEMENTS_ENABLED).set, are_enabled)


async def set_are_custom_complements_enabled(are_enabled: bool, username: Optional[str] = None,
                                             userid: Optional[str] = None, name_to_id: Optional[
            Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param are_enabled: the new status for whether the bot is allowed to make use of the custom complements
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Allows the changing of if the bot is allowed to make use of the custom complements
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(
        None, _USERS_DB_REF.child(userid).child(_CUSTOM_COMPLEMENTS_ENABLED).set, are_enabled)


async def are_custom_complements_enabled(username: Optional[str] = None, userid: Optional[str] = None,
                                         name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                             [str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether the bot is allowed to use custom complements
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    is_enabled = await _event_loop.run_in_executor(
        None, _USERS_DB_REF.child(userid).child(_CUSTOM_COMPLEMENTS_ENABLED).get)
    if is_enabled is None:
        return _DEFAULT_CUSTOM_COMPLEMENTS_ENABLED
    return bool(is_enabled)


async def is_ignoring_bots(username: Optional[str] = None, userid: Optional[str] = None, name_to_id: Optional[
        Union[Callable[[str], Optional[str]], Callable[[str], Awaitable[Optional[str]]]]] = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether the bot is allowed to complements other bots
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    is_ignoring = await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_SHOULD_IGNORE_BOTS).get)
    if is_ignoring is None:
        return _DEFAULT_SHOULD_IGNORE_BOTS
    return bool(is_ignoring)


async def set_should_ignore_bots(should_ignore_bots: bool, username: Optional[str] = None, userid: Optional[str] = None,
                                 name_to_id: Optional[Union[Callable[[str], Optional[str]], Callable[
                                     [str], Awaitable[Optional[str]]]]] = None) -> None:
    """
    At least one of 'username' or 'userid' must be specified, and if userid is not specified, name_to_id must be
    specified; userid is preferred whenever possible due to being guaranteed to never change
    :param should_ignore_bots: the new status for if the bot may complement other bots
    :param name_to_id: function that allows us to convert a username to a user id
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    Allows for toggling of whether the bot is allowed to complement other bots
    """
    assert username or userid
    assert userid or name_to_id

    if not userid:
        userid = await run_with_appropriate_awaiting(name_to_id, username)
    await _event_loop.run_in_executor(None, _USERS_DB_REF.child(userid).child(_SHOULD_IGNORE_BOTS).set,
                                      should_ignore_bots)
