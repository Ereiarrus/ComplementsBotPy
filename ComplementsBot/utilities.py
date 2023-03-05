from typing import TypeVar, ParamSpec, Optional, Awaitable, Callable, Union

T = TypeVar("T")
U = ParamSpec("U")


async def run_with_appropriate_awaiting(func: Optional[Union[Callable[U, Awaitable[T]], Callable[U, T]]], *args,
                                        **kwargs) -> T:
    if func is None:
        return
    to_do: Union[None, Awaitable[None]] = func(*args, **kwargs)
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
