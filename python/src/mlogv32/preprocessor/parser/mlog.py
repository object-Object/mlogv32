from dataclasses import dataclass
from importlib import resources
from typing import TYPE_CHECKING, Callable, Iterator

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
    name: Token


@dataclass
class Statement:
    name: Token
    args: list[Token]


@dataclass
class Directive:
    name: Token
    args: list[Token]


type ASTNode = Label | Statement | Directive

type AST = list[ASTNode]


@dataclass
@v_args(inline=True)
class MlogTransformer(Transformer[Token, list[ASTNode]]):
    def start(self, *children: ASTNode):
        return list(children)

    def label(self, name: Token):
        return Label(name.update(value=name[:-1]))

    def statement(self, name: Token, *args: Token):
        return Statement(name, list(args))

    def directive(self, name: Token, *args: Token):
        return Directive(name, list(args))


GRAMMAR = (resources.files() / "mlog.lark").read_text("utf-8")

PARSER = Lark(
    GRAMMAR,
    parser="lalr",
    strict=True,
)


def parse_mlog(text: str):
    tree = PARSER.parse(text)
    return MlogTransformer().transform(tree)


class MlogError(AssertionError):
    def __init__(self, message: str, token: Token, *args: object) -> None:
        super().__init__(message, *args)
        self.token = token


class DirectiveError(MlogError):
    pass


def expect_int(
    n: Token,
    predicate: Callable[[int], bool] | None = None,
    description: str = "value",
):
    try:
        result = int(n)
    except ValueError as e:
        raise DirectiveError(str(e), n) from e
    if predicate is None or predicate(result):
        return result
    raise DirectiveError(f"Invalid {description}: {result}", n)


def iter_labels(ast: AST) -> Iterator[tuple[str, int]]:
    counter = 0
    length_assertion = None
    for node in ast:
        match node:
            case Label(name=name):
                yield (name, counter)

            case Statement():
                counter += 1

            case Directive(name="start_assert_length", args=[n]):
                if length_assertion is not None:
                    raise DirectiveError(
                        "Nested length assertions are not supported", node.name
                    )
                # length, start counter, token for errors
                length_assertion = (
                    expect_int(n, lambda v: v >= 0, "length assertion"),
                    counter,
                    n,
                )

            case Directive(name="end_assert_length"):
                if length_assertion is None:
                    raise DirectiveError(
                        "Found end_assert_length without matching start_assert_length",
                        node.name,
                    )
                want_length, start_counter, _ = length_assertion
                length_assertion = None
                got_length = counter - start_counter
                if want_length != got_length:
                    raise DirectiveError(
                        f"Expected @counter to be {start_counter + want_length} (length {want_length}), but got {counter} (length {got_length})",
                        node.name,
                    )

            case Directive(name="assert_counter", args=[n]):
                if counter != expect_int(n):
                    raise DirectiveError(
                        f"Expected @counter to be {n}, but got {counter}", node.name
                    )

            case Directive():
                pass

    if length_assertion is not None:
        _, _, token = length_assertion
        raise DirectiveError(
            "Found start_assert_length without matching end_assert_length", token
        )


def check_unsaved_variables(ast: AST):
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
            case Statement(name="select", args=[var, *_]):
                pass
            case Directive(name="start_fetch"):
                state = "fetch"
                continue
            case Directive(name="end_fetch"):
                state = "check"
                continue
            case Directive(name="push_saved", args=args):
                for var in args:
                    saved_variables.add(var)
                continue
            case Directive(name="pop_saved", args=args):
                for var in args:
                    saved_variables.remove(var)
                continue
            case _:
                continue

        if state == "check" and var not in saved_variables | warned_variables:
            print(f"[WARNING] Unsaved variable: {var}")
            warned_variables.add(var)

    print(f"Saved variable count: {len(saved_variables - {'@counter'})}")


def count_statements(ast: AST):
    n = 0
    for node in ast:
        if isinstance(node, Statement):
            n += 1
    return n


def replace_symbolic_labels(
    text: str,
    ast: AST,
    labels: dict[str, int],
    *,
    check: bool = True,
) -> str:
    parts = list[str]()

    start_pos = 0

    for token in _iter_label_refs(ast):
        label = token[1:-1]
        if label not in labels:
            raise MlogError(f"Unknown symbolic label: {label}", token)

        if token.start_pos is None or token.end_pos is None:
            raise MlogError(f"Internal error: invalid token: {token}", token)

        parts += [
            text[start_pos : token.start_pos],
            str(labels[label]),
        ]

        start_pos = token.end_pos

    parts += text[start_pos:]

    new_text = "".join(parts)

    # sanity checks
    if check:
        new_ast = parse_mlog(new_text)
        if count_statements(ast) != count_statements(new_ast):
            raise AssertionError(
                "Source transformation failed: mismatched statement count"
            )
        if labels != dict(iter_labels(new_ast)):
            raise AssertionError("Source transformation failed: mismatched labels")

    return new_text


def _iter_label_refs(ast: AST) -> Iterator[Token]:
    for node in ast:
        if not isinstance(node, Statement):
            continue
        for token in node.args:
            if token.type != "LABEL_REF":
                continue
            yield token
