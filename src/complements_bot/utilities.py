"""
Useful functions that can be used generally anywhere across the program
"""

import asyncio
import re
from typing import Awaitable, Callable, Optional, ParamSpec, TypeVar, Union, Coroutine

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


class Awaitables:
    """
    Class that makes making a collection of tasks and then gathering easier
    """

    def __init__(self, tasks: Optional[list[Union[asyncio.Future, Coroutine]]] = None):
        self._tasks = []
        if tasks is not None:
            for task in tasks:
                if isinstance(task, asyncio.Future):
                    self._tasks.append(task)
                else:
                    self._tasks.append(asyncio.create_task(task))
        self._used = False

    def add_task(self, task: Union[asyncio.Future, Coroutine]) -> None:
        """
        :param task: the awaitable we want to add
        Creates a task out of the awaitable using 'asyncio.create_task' and adding it to a list
        """
        if not self._used:
            if isinstance(task, asyncio.Future):
                self._tasks.append(task)
            else:
                self._tasks.append(asyncio.create_task(task))
        else:
            raise asyncio.InvalidStateError("All tasks have already been gathered - cannot add new ones.")

    def gather(self) -> asyncio.Future:
        """
        asyncio.gather on all tasks added to this object; needs to be awaited for actual result
        """
        if not self._used:
            self._used = True
            return asyncio.gather(*self._tasks)

        raise asyncio.InvalidStateError("All tasks have already been gathered.")
