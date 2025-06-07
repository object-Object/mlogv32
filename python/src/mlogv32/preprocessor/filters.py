import functools
from typing import Any, Callable

from jinja2.runtime import Context

from mlogv32.scripts.ram_proc import VariableFormat


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
def ram_variable(index: int):
    return VariableFormat.minimized.get_variable(index)


@make_jinja_exceptions_suck_a_bit_less
def csr(name: str | int):
    match name:
        case str():
            if name not in CSRS:
                raise KeyError(f"Invalid CSR: {name}")
            return ram_variable(CSRS[name])
        case int():
            return ram_variable(name)


@make_jinja_exceptions_suck_a_bit_less
def quote(value: Any):
    return f'"{value}"'


CSRS: dict[str, int] = {
    # unprivileged
    "cycle": 0xC00,
    "time": 0xC01,
    "instret": 0xC02,
    **{f"hpmcounter{i}": 0xC00 + i for i in range(3, 32)},
    "cycleh": 0xC80,
    "timeh": 0xC81,
    "instreth": 0xC82,
    **{f"hpmcounter{i}h": 0xC80 + i for i in range(3, 32)},
    # supervisor
    "sstatus": 0x100,
    "sie": 0x104,
    "stvec": 0x105,
    "scounteren": 0x106,
    "senvcfg": 0x10A,
    "scountinhibit": 0x120,
    "sscratch": 0x140,
    "sepc": 0x141,
    "scause": 0x142,
    "stval": 0x143,
    "sip": 0x144,
    "scountovf": 0xDA0,
    "satp": 0x180,
    "scontext": 0x5A8,
    "sstateen0": 0x10C,
    "sstateen1": 0x10D,
    "sstateen2": 0x10E,
    "sstateen3": 0x10F,
    # machine
    "mvendorid": 0xF11,
    "marchid": 0xF12,
    "mimpid": 0xF13,
    "mhartid": 0xF14,
    "mconfigptr": 0xF15,
    "mstatus": 0x300,
    "misa": 0x301,
    "medeleg": 0x302,
    "mideleg": 0x303,
    "mie": 0x304,
    "mtvec": 0x305,
    "mcounteren": 0x306,
    "mstatush": 0x310,
    "medelegh": 0x312,
    "mscratch": 0x340,
    "mepc": 0x341,
    "mcause": 0x342,
    "mtval": 0x343,
    "mip": 0x344,
    "mtinst": 0x34A,
    "mtval2": 0x34B,
    "menvcfg": 0x30A,
    "menvcfgh": 0x31A,
    "mseccfg": 0x747,
    "mseccfgh": 0x757,
    **{f"pmpcfg{i}": 0x3A0 + i for i in range(0, 16)},
    **{f"pmpaddr{i}": 0x3B0 + i for i in range(0, 64)},
    "mstateen0": 0x30C,
    "mstateen1": 0x30D,
    "mstateen2": 0x30E,
    "mstateen3": 0x30F,
    "mstateen0h": 0x31C,
    "mstateen1h": 0x31D,
    "mstateen2h": 0x31E,
    "mstateen3h": 0x31F,
}
