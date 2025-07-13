from __future__ import annotations

import re
from typing import Iterable, Protocol, cast, override

from jinja2 import Environment
from jinja2.ext import Extension
from jinja2.lexer import Token, TokenStream, count_newlines

from mlogv32.preprocessor.filters import make_jinja_exceptions_suck_a_bit_less


class CommentStatement(Extension):
    """Allows writing inline expressions without causing an mlogls error.

    Example:
    ```
    op add foo bar {{# 1 }}
    ```
    """

    @override
    def preprocess(
        self,
        source: str,
        name: str | None,
        filename: str | None = None,
    ) -> str:
        # hacky
        return source.replace("{{#", "{{")


class LineExpressionEnv(Protocol):
    line_expression_prefix: str
    line_expression_re: re.Pattern[str]

    @staticmethod
    def of(environment: Environment) -> LineExpressionEnv:
        return cast(LineExpressionEnv, environment)

    @staticmethod
    def extend(
        environment: Environment,
        *,
        line_expression_prefix: str,
    ):
        environment.extend(
            line_expression_prefix=line_expression_prefix,
            line_expression_re=re.compile(
                r"^([ \t\v]*)"
                + re.escape(line_expression_prefix)
                + r"(-?) ([^\r\n]+)$",
                flags=re.M,
            ),
        )


class LineExpression(Extension):
    """Adds line expressions, similar to the built-in line statements/comments.

    Configuration:
    ```
    LineExpressionEnv.extend(env, line_expression_prefix="#{")
    ```
    Example:
    ```
    #{ 1 + 1
    ```
    Output:
    ```
    2
    ```
    """

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)

    @property
    def _env(self):
        return LineExpressionEnv.of(self.environment)

    @override
    def filter_stream(self, stream: TokenStream) -> TokenStream | Iterable[Token]:
        for token in stream:
            if token.type != "data":
                yield token
                continue

            pos = 0
            lineno = token.lineno

            while True:
                match = self._env.line_expression_re.search(token.value, pos)
                if match is None:
                    break

                new_pos = match.start()
                if new_pos > pos:
                    preval = token.value[pos:new_pos]
                    if match.group(2):
                        preval = preval.rstrip()
                    yield Token(lineno, "data", preval)
                    lineno += count_newlines(preval)

                if not match.group(2):
                    yield Token(lineno, "data", match.group(1))

                for subtoken in self.environment.lexer.tokenize(
                    "{{ " + match.group(3) + " }}",
                    name=stream.name,
                    filename=stream.filename,
                ):
                    yield Token(lineno, subtoken.type, subtoken.value)

                pos = match.end()

            if pos < len(token.value):
                yield Token(lineno, "data", token.value[pos:])


# https://jinja.palletsprojects.com/en/stable/extensions/#inline-gettext


_local_re = re.compile(r"(?:(?<=[\n #\t;])|^)\$([^\n #\t;]+)")


class LocalVariablesEnv(Protocol):
    local_variable_index: int
    largest_local_variable: int
    local_variable_cache: dict[str, str]

    @staticmethod
    def of(environment: Environment) -> LocalVariablesEnv:
        return cast(LocalVariablesEnv, environment)

    @staticmethod
    def extend(
        environment: Environment,
        *,
        local_variable_index: int = 1,
        largest_local_variable: int = 0,
        local_variable_cache: dict[str, str] | None = None,
    ):
        if local_variable_cache is None:
            local_variable_cache = {}
        environment.extend(
            local_variable_index=local_variable_index,
            largest_local_variable=largest_local_variable,
            local_variable_cache=local_variable_cache,
        )


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
        LocalVariablesEnv.extend(environment)
        environment.globals |= {  # type: ignore
            "reset_locals": self.reset_locals,
            "declare_locals": self.declare_locals,
            "local_variable": self.local_variable,
        }

    @property
    def _env(self):
        return LocalVariablesEnv.of(self.environment)

    @make_jinja_exceptions_suck_a_bit_less
    def reset_locals(self, i: int = 1):
        if i < 1:
            raise ValueError(f"Invalid local variable index: {i}")
        self._env.local_variable_index = i
        self._env.local_variable_cache.clear()

    @make_jinja_exceptions_suck_a_bit_less
    def declare_locals(self, *names: str | list[str], i: int = 1):
        self.reset_locals(i)
        for name in names:
            if isinstance(name, list):
                self.declare_locals(*name)
            else:
                if not name.startswith("$$"):
                    raise ValueError(f"Invalid local variable declaration: {name}")
                self.local_variable(name.removeprefix("$"), declare=True)

    @make_jinja_exceptions_suck_a_bit_less
    def local_variable(self, name: str | int | None = None, declare: bool = False):
        cache = self._env.local_variable_cache

        if name not in cache:
            if isinstance(name, int):
                i = name
                if i < 1:
                    raise ValueError(f"Invalid local variable index: {i}")
            else:
                i = self._env.local_variable_index

            value = f"local{i}"

            self._env.local_variable_index = i + 1

            if not isinstance(name, str):
                return value

            # names starting with $$ should be declared ahead of time via declare_locals
            if not declare and name.startswith("$"):
                raise ValueError(f"Undeclared local variable: ${name}")

            cache[name] = value

            self._env.largest_local_variable = max(i, self._env.largest_local_variable)

        return cache[name]

    @override
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
