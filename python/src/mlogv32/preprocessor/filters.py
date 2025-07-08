import functools
from typing import Any, Callable

from jinja2.runtime import Context
from jinja2.utils import Namespace

from mlogv32.scripts.ram_proc import VariableFormat

from .constants import CSRS, MEMORY_K, MEMORY_M

FILTERS = dict[str, Callable[..., Any]]()


def register_filter[T: Callable[..., Any]](name: str | None = None) -> Callable[[T], T]:
    def decorator(f: T) -> T:
        FILTERS[name or f.__name__] = f
        return f

    return decorator


# from hexdoc.jinja.filters
def make_jinja_exceptions_suck_a_bit_less[**P, R](f: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            args_ = list(args)
            if args_ and isinstance(args_[0], Context):
                args_ = args_[1:]

            e.add_note(f"args:   {args_}")
            e.add_note(f"kwargs: {kwargs}")
            raise

    return wrapper


@make_jinja_exceptions_suck_a_bit_less
@register_filter()
def ram_var(index: int):
    return VariableFormat.mlogv32.get_variable(index)


@make_jinja_exceptions_suck_a_bit_less
@register_filter()
def csr(name: str | int):
    match name:
        case str():
            if name not in CSRS:
                raise KeyError(f"Invalid CSR: {name}")
            return ram_var(CSRS[name])
        case int():
            return ram_var(name)


@make_jinja_exceptions_suck_a_bit_less
@register_filter()
def quote(value: Any):
    return f'"{value}"'


@make_jinja_exceptions_suck_a_bit_less
@register_filter()
def memory_size(size: int):
    if size == 0:
        return "0"
    if size % MEMORY_M == 0:
        return f"{size // MEMORY_M}M"
    if size % MEMORY_K == 0:
        return f"{size // MEMORY_K}K"
    return hex(size)


@make_jinja_exceptions_suck_a_bit_less
@register_filter("hex")
def hex_filter(n: int):
    return hex(n)


@make_jinja_exceptions_suck_a_bit_less
@register_filter()
def namespace_dict(namespace: Namespace):
    # cursed
    attrs: dict[str, Any] = namespace._Namespace__attrs
    return attrs
