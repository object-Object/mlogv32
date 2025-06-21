from dataclasses import dataclass
from importlib import resources
from typing import TYPE_CHECKING, Callable

from lark import Lark, Token, Transformer

if TYPE_CHECKING:

    def v_args[T](
        inline: bool = False,
        meta: bool = False,
        tree: bool = False,
    ) -> Callable[[T], T]: ...
else:
    from lark import v_args


@dataclass
class Label:
    name: str


@dataclass
class Statement:
    name: str
    args: list[str]


@dataclass
@v_args(inline=True)
class MlogTransformer(Transformer[Token, list[Label | Statement]]):
    def start(self, *children: Label | Statement):
        return list(children)

    def label(self, name: str):
        return Label(name[:-1])

    def statement(self, name: str, *args: str):
        return Statement(name, list(args))

    def TOKEN(self, token: Token):
        return str(token)


GRAMMAR = (resources.files() / "mlog.lark").read_text("utf-8")

PARSER = Lark(
    GRAMMAR,
    parser="lalr",
    strict=True,
)


def parse_mlog(text: str):
    tree = PARSER.parse(text)
    return MlogTransformer().transform(tree)
