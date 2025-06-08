from jinja2.ext import Extension


class CommentStatement(Extension):
    """Allows writing inline expressions without causing an mlogls error.

    For example:
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
