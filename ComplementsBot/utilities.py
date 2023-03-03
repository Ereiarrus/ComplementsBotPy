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
