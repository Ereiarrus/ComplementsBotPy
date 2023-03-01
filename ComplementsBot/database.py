"""
The API through which items in our database are accessed
"""

import re
from firebase_admin import credentials, db
from env_reader import databaseURL
from typing import Any, Dict, Tuple, Optional, Callable
import firebase_admin

cred: credentials.Certificate = credentials.Certificate("./.firebase_config.json")
firebase_admin.initialize_app(cred, {'databaseURL': databaseURL})

REF: db.Reference = db.reference('/')
IGNORED_DB_REF: db.Reference = REF.child('Ignored')
USERS_DB_REF: db.Reference = REF.child('Users')

# Default values for database:
DEFAULT_COMPLEMENT_CHANCE: float = 10.0 / 3.0
DEFAULT_SHOULD_IGNORE_BOTS: bool = True
DEFAULT_TTS_IGNORE_PREFIX: str = "!"
DEFAULT_COMMAND_COMPLEMENT_ENABLED: bool = True
DEFAULT_RANDOM_COMPLEMENT_ENABLED: bool = True
DEFAULT_COMMAND_COMPLEMENT_MUTED: bool = True
DEFAULT_RANDOM_COMPLEMENT_MUTED: bool = False
DEFAULT_IS_JOINED: bool = True
DEFAULT_DEFAULT_COMPLEMENTS_ENABLED: bool = True
DEFAULT_CUSTOM_COMPLEMENTS_ENABLED: bool = True

# Database keys:
COMPLEMENT_CHANCE: str = "complement_chance"
SHOULD_IGNORE_BOTS: str = "should_ignore_bots"
IS_JOINED: str = "is_joined"
MUTE_PREFIX: str = "tts_ignore_prefix"
COMMAND_COMPLEMENT_ENABLED: str = "command_complement_enabled"
RANDOM_COMPLEMENT_ENABLED: str = "random_complement_enabled"
CUSTOM_COMPLEMENTS: str = "custom_complements"
COMMAND_COMPLEMENT_MUTED: str = "command_complement_muted"
RANDOM_COMPLEMENT_MUTED: str = "random_complement_muted"
DEFAULT_COMPLEMENTS_ENABLED: str = "default_complements_enabled"
CUSTOM_COMPLEMENTS_ENABLED: str = "custom_complements_enabled"

DEFAULT_USER: Dict[str, Any] = {COMPLEMENT_CHANCE: DEFAULT_COMPLEMENT_CHANCE,
                                SHOULD_IGNORE_BOTS: DEFAULT_SHOULD_IGNORE_BOTS,
                                IS_JOINED: DEFAULT_IS_JOINED,
                                COMMAND_COMPLEMENT_ENABLED: DEFAULT_COMMAND_COMPLEMENT_ENABLED,
                                RANDOM_COMPLEMENT_ENABLED: DEFAULT_RANDOM_COMPLEMENT_ENABLED,
                                MUTE_PREFIX: DEFAULT_TTS_IGNORE_PREFIX,
                                COMMAND_COMPLEMENT_MUTED: DEFAULT_COMMAND_COMPLEMENT_MUTED,
                                RANDOM_COMPLEMENT_MUTED: DEFAULT_RANDOM_COMPLEMENT_MUTED,
                                CUSTOM_COMPLEMENTS_ENABLED: DEFAULT_CUSTOM_COMPLEMENTS_ENABLED,
                                DEFAULT_COMPLEMENTS_ENABLED: DEFAULT_DEFAULT_COMPLEMENTS_ENABLED
                                }


def is_user_ignored(username: Optional[str] = None, userid: Optional[int] = None,
                    name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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

    users: list[int] = IGNORED_DB_REF.get()
    if users is None:
        # No ignored users exist
        return False

    if not userid:
        userid = name_to_id(username)

    return userid in users


def ignore(username: str = None, userid: int = None,
           name_to_id: Optional[Callable[[str], int]] = None) -> None:
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

    def ignore_transaction(data: list[str]):
        if data is None:
            data = []
        data.append(userid)
        return data

    if not userid:
        userid = name_to_id(username)

    IGNORED_DB_REF.transaction(ignore_transaction)


def unignore(username: str = None, userid: int = None,
             name_to_id: Optional[Callable[[str], int]] = None) -> None:
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

    def unignore_transaction(data: list[int]) -> list[int]:
        data.remove(userid)
        return data

    if not userid:
        userid = name_to_id(username)

    IGNORED_DB_REF.transaction(unignore_transaction)


def channel_exists(username: str = None, userid: int = None,
                   name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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

    users = USERS_DB_REF.get(False, True)
    if not userid:
        userid = name_to_id(username)
    return (users is not None) and userid in users


def is_channel_joined(username: str = None, userid: int = None,
                      name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    if not channel_exists(userid=userid):
        return False

    return bool(USERS_DB_REF.child(userid).child(IS_JOINED).get())


def join_channel(username: str = None, userid: int = None,
                 name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    if not channel_exists(userid=userid):
        USERS_DB_REF.child(userid).set(DEFAULT_USER)
    else:
        USERS_DB_REF.child(userid).child(IS_JOINED).set(True)


def leave_channel(username: str = None, userid: int = None,
                  name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(IS_JOINED).set(False)


def delete_channel(username: str = None, userid: int = None,
                   name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).delete()


def get_joined_channels() -> list[int]:
    """
    :return: a list of all joined channels (in the form of a list of user IDs) where the bot is currently active
    """

    all_users = USERS_DB_REF.get(False, True)
    joined_users: list[int] = []
    if all_users is None:
        return joined_users
    for user in all_users:
        if USERS_DB_REF.child(user).child(IS_JOINED).get():
            joined_users.append(user)
    return joined_users


def number_of_joined_channels() -> int:
    """
    :return: The number of joined channels where the bot is currently active
    """
    return len(get_joined_channels())


def set_tts_mute_prefix(prefix: str, username: str = None, userid: int = None,
                        name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(MUTE_PREFIX).set(prefix)


def get_tts_mute_prefix(username: str = None, userid: int = None,
                        name_to_id: Optional[Callable[[str], int]] = None) -> str:
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
        userid = name_to_id(username)
    prefix = USERS_DB_REF.child(userid).child(MUTE_PREFIX).get()
    if prefix is None:
        set_tts_mute_prefix(DEFAULT_TTS_IGNORE_PREFIX, userid=userid)
        prefix = DEFAULT_TTS_IGNORE_PREFIX
    return prefix


def set_complement_chance(chance: float, username: str = None, userid: int = None,
                          name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(COMPLEMENT_CHANCE).set(chance)


def get_complement_chance(username: str = None, userid: int = None,
                          name_to_id: Optional[Callable[[str], int]] = None) -> float:
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
        userid = name_to_id(username)
    chance = USERS_DB_REF.child(userid).child(COMPLEMENT_CHANCE).get()
    if chance is None:
        set_complement_chance(DEFAULT_COMPLEMENT_CHANCE, userid=userid)
        chance = DEFAULT_COMPLEMENT_CHANCE
    return chance


def set_cmd_complement_enabled(is_enabled: bool, username: str = None, userid: int = None,
                               name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_ENABLED).set(is_enabled)


def get_cmd_complement_enabled(username: str = None, userid: int = None,
                               name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_ENABLED).get()
    if is_enabled is None:
        set_cmd_complement_enabled(DEFAULT_COMMAND_COMPLEMENT_ENABLED, userid=userid)
        is_enabled = DEFAULT_COMMAND_COMPLEMENT_ENABLED
    return is_enabled


def set_random_complement_enabled(is_enabled: bool, username: str = None, userid: int = None,
                                  name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_ENABLED).set(is_enabled)


def get_random_complement_enabled(username: str = None, userid: int = None,
                                  name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_ENABLED).get()
    if is_enabled is None:
        set_random_complement_enabled(DEFAULT_RANDOM_COMPLEMENT_ENABLED, userid=userid)
        is_enabled = DEFAULT_RANDOM_COMPLEMENT_ENABLED
    return is_enabled


def add_complement(complement: str, username: str = None, userid: int = None,
                   name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)

    def add_transaction(data):
        if data is None:
            data = []
        data.append(complement)
        return data

    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).transaction(add_transaction)


def remove_chars(some_str: str, regex: str = r"[^a-z0-9]") -> str:
    """
    :param some_str: The string we want to remove all appearances of a pattern from
    :param regex: the pattern we are wanting to remove
    :return: 'some_str' with 'regex' pattern removed from it
    """
    return re.sub(regex, "", some_str.lower())


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
        comp_edit = remove_chars(comp)
        if phrase in comp_edit:
            removed_comps.append(comp)
        else:
            leftover_comps.append(comp)

    return removed_comps, leftover_comps


def remove_complements(username: str = None, userid: int = None, to_keep: Optional[list[str]] = None,
                       to_remove: Optional[list[str]] = None,
                       name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)

    def remove_transaction(data):
        if to_remove:
            for comp in to_remove:
                data.remove(comp)
            return data
        return to_keep or []

    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).transaction(remove_transaction)


def remove_all_complements(username: str = None, userid: int = None,
                           name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).delete()


def get_custom_complements(username: str = None, userid: int = None,
                           name_to_id: Optional[Callable[[str], int]] = None) -> list[str]:
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
        userid = name_to_id(username)
    complements = USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).get()
    return complements or []


def is_cmd_complement_muted(username: str = None, userid: int = None,
                            name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    is_muted = USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_MUTED).get()
    if is_muted is None:
        return DEFAULT_COMMAND_COMPLEMENT_MUTED
    return bool(is_muted)


def set_cmd_complement_is_muted(is_muted: bool, username: str = None, userid: int = None,
                                name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_MUTED).set(is_muted)


def are_random_complements_muted(username: str = None, userid: int = None,
                                 name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    is_muted = USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_MUTED).get()
    if is_muted is None:
        return DEFAULT_RANDOM_COMPLEMENT_MUTED
    return bool(is_muted)


def set_random_complements_are_muted(are_muted: bool, username: str = None, userid: int = None,
                                     name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_MUTED).set(are_muted)


def are_default_complements_enabled(username: str = None, userid: int = None,
                                    name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(DEFAULT_COMPLEMENTS_ENABLED).get()
    if is_enabled is None:
        return DEFAULT_DEFAULT_COMPLEMENTS_ENABLED
    return bool(is_enabled)


def set_are_default_complements_enabled(are_enabled: bool, username: str = None, userid: int = None,
                                        name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(DEFAULT_COMPLEMENTS_ENABLED).set(are_enabled)


def set_are_custom_complements_enabled(are_enabled: bool, username: str = None, userid: int = None,
                                       name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS_ENABLED).set(are_enabled)


def are_custom_complements_enabled(username: str = None, userid: int = None,
                                   name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS_ENABLED).get()
    if is_enabled is None:
        return DEFAULT_CUSTOM_COMPLEMENTS_ENABLED
    return bool(is_enabled)


def is_ignoring_bots(username: str = None, userid: int = None,
                     name_to_id: Optional[Callable[[str], int]] = None) -> bool:
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
        userid = name_to_id(username)
    is_ignoring = USERS_DB_REF.child(userid).child(SHOULD_IGNORE_BOTS).get()
    if is_ignoring is None:
        return DEFAULT_SHOULD_IGNORE_BOTS
    return bool(is_ignoring)


def set_should_ignore_bots(should_ignore_bots: bool, username: str = None, userid: int = None,
                           name_to_id: Optional[Callable[[str], int]] = None) -> None:
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
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(SHOULD_IGNORE_BOTS).set(should_ignore_bots)
