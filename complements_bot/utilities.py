"""
Useful functions that can be used generally anywhere across the program
"""

import re
from typing import TypeVar, Optional, Awaitable, Callable, Union, ParamSpec

_T = TypeVar("_T")
_U = ParamSpec("_U")


async def run_with_appropriate_awaiting(func: Optional[Union[Callable[_U, Awaitable[_T]], Callable[_U, _T]]], *args,
                                        **kwargs) -> Optional[_T]:
    """
    :param func: the function we want to get the result of
    :return: whatever func returned after being awaited if async, the result of func itself
    Runs 'func'; if it is a future, then it awaits for its result and returns that; otherwise, returns the result of
    the run.
    """
    if func is None:
        return None
    to_do: Union[_T, Awaitable[_T]] = func(*args, **kwargs)
    if isinstance(to_do, Awaitable):
        return await to_do
    return to_do


def remove_chars(some_str: str, regex: str = r"[^a-z0-9]") -> str:
    """
    :param some_str: The string we want to remove all appearances of a pattern from
    :param regex: the pattern we are wanting to remove
    :return: 'some_str' with 'regex' pattern removed from it
    """
    return re.sub(regex, "", some_str.lower())
