import re
from typing import Iterable

from jinja2 import Environment
from jinja2.ext import Extension
from jinja2.lexer import Token, TokenStream, count_newlines


class CommentStatement(Extension):
    """Allows writing inline expressions without causing an mlogls error.

    Example:
    ```
    op add foo bar {{# 1 }}
    ```
    """

    def preprocess(
        self,
        source: str,
        name: str | None,
        filename: str | None = None,
    ) -> str:
        # hacky
        return source.replace("{{#", "{{")


# https://jinja.palletsprojects.com/en/stable/extensions/#inline-gettext

_local_re = re.compile(r"(?:(?<=[\n #\t;])|^)\$([^\n #\t;]+)")


class LocalVariables(Extension):
    """Allows giving names to anonymous local variables.

    Example:
    ```
    #% do reset_locals()
    set $foo "bar"
    set $bar 1
    op add $foo $bar 1

    #% do reset_locals(5)
    set $foo "qux"
    set $baz "quux"
    ```
    Output:
    ```
    set local1 "bar"
    set local2 1
    op add local1 local2 1

    set local5 "qux"
    set local6 "qux"
    ```
    """

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        environment.extend(
            local_variable_index=1,
            largest_local_variable=0,
            local_variable_cache={},
        )
        environment.globals |= {  # type: ignore
            "reset_locals": self.reset_locals,
            "declare_locals": self.declare_locals,
            "local_variable": self.local_variable,
        }

    def reset_locals(self, i: int = 1):
        if i < 1:
            raise ValueError(f"Invalid local variable index: {i}")
        setattr(self.environment, "local_variable_index", i)
        getattr(self.environment, "local_variable_cache").clear()

    def declare_locals(self, *names: str | list[str]):
        for name in names:
            if isinstance(name, list):
                self.declare_locals(*name)
            else:
                self.local_variable(name.removeprefix("$"))

    def local_variable(self, name: str | int | None = None):
        cache: dict[str, str] = getattr(self.environment, "local_variable_cache")

        if name not in cache:
            if isinstance(name, int):
                i = name
                if i < 1:
                    raise ValueError(f"Invalid local variable index: {i}")
            else:
                i: int = getattr(self.environment, "local_variable_index")

            value = f"local{i}"

            setattr(self.environment, "local_variable_index", i + 1)

            if not isinstance(name, str):
                return value

            cache[name] = value

            setattr(
                self.environment,
                "largest_local_variable",
                max(i, getattr(self.environment, "largest_local_variable")),
            )

        return cache[name]

    def filter_stream(self, stream: TokenStream) -> TokenStream | Iterable[Token]:
        for token in stream:
            if token.type != "data":
                yield token
                continue

            pos = 0
            lineno = token.lineno

            while True:
                match = _local_re.search(token.value, pos)
                if match is None:
                    break

                new_pos = match.start()
                if new_pos > pos:
                    preval = token.value[pos:new_pos]
                    yield Token(lineno, "data", preval)
                    lineno += count_newlines(preval)

                name = match.group(1)

                yield Token(lineno, "variable_begin", "")
                yield Token(lineno, "name", "local_variable")
                yield Token(lineno, "lparen", "")
                yield Token(lineno, "string", name)
                yield Token(lineno, "rparen", "")
                yield Token(lineno, "variable_end", "")

                pos = match.end()

            if pos < len(token.value):
                yield Token(lineno, "data", token.value[pos:])
