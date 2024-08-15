# https://stackoverflow.com/a/60748729

from typing import TypeVar

T = TypeVar("T")
def static_init(cls: T) -> T:
    if f := getattr(cls, "__static__", None): f()
    else: raise NotImplementedError("class marked static with no __static__ method")
    return cls
