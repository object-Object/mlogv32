from dataclasses import dataclass
from importlib import resources
from typing import TYPE_CHECKING, Callable, Iterable, Iterator

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
class Directive:
    name: str
    args: list[str]


type ASTNode = Label | Statement | Directive


@dataclass
@v_args(inline=True)
class MlogTransformer(Transformer[Token, list[ASTNode]]):
    def start(self, *children: ASTNode):
        return list(children)

    def label(self, name: str):
        return Label(name[:-1])

    def statement(self, name: str, *args: str):
        return Statement(name, list(args))

    def directive(self, name: str, *args: str):
        return Directive(name, list(args))

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


def iter_labels(ast: Iterable[ASTNode]) -> Iterator[tuple[str, int]]:
    line_num = 0
    for node in ast:
        match node:
            case Label(name=name):
                yield (name, line_num)
            case Statement():
                line_num += 1
            case Directive(name="assert_line", args=[n]):
                assert line_num == int(n), (
                    f"Expected next line to be {n}, but got {line_num}"
                )
            case Directive():
                pass


def check_unsaved_variables(ast: Iterable[ASTNode]):
    saved_variables = {"@counter"}
    warned_variables = set[str]()
    state = "init"

    for node in ast:
        match node:
            case Statement(name="read", args=[var, target, name]):
                if state == "fetch" and target == "prev_proc":
                    if var != name[1:-1]:
                        print(
                            f"[WARNING] Invalid variable restoration: {var} != {name[1:-1]}"
                        )
                    elif var in saved_variables:
                        print(f"[WARNING] Duplicate variable restoration: {var}")
                    saved_variables.add(var)
                    continue
            case Statement(name="getblock", args=[_, var, *_]):
                pass
            case Statement(name="getflag", args=[var, *_]):
                pass
            case Statement(name="getlink", args=[var, *_]):
                pass
            case Statement(name="lookup", args=[_, var, *_]):
                pass
            case Statement(name="op", args=[_, var, *_]):
                pass
            case Statement(name="sensor", args=[var, *_]):
                pass
            case Statement(name="set", args=[var, *_]):
                pass
            case Directive(name="begin_fetch"):
                state = "fetch"
                continue
            case Directive(name="end_fetch"):
                state = "check"
                continue
            case Directive(name="push_saved", args=[var]):
                saved_variables.add(var)
                continue
            case Directive(name="pop_saved", args=[var]):
                saved_variables.remove(var)
                continue
            case _:
                continue

        if state == "check" and var not in saved_variables | warned_variables:
            print(f"[WARNING] Unsaved variable: {var}")
            warned_variables.add(var)

    print(f"Saved variable count: {len(saved_variables - {'@counter'})}")
