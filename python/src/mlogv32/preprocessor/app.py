from pathlib import Path
from typing import Annotated

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from typer import Option, Typer

from mlogv32.preprocessor.extensions import CommentStatement

from . import filters

app = Typer(
    pretty_exceptions_show_locals=False,
)


@app.command()
def main(
    path: Path,
    output: Annotated[Path | None, Option("-o", "--output")] = None,
):
    path = path.resolve()

    env = Environment(
        loader=FileSystemLoader(path.parent),
        line_statement_prefix="#%",
        line_comment_prefix="#%#",
        autoescape=False,
        lstrip_blocks=True,
        trim_blocks=True,
        undefined=StrictUndefined,
        extensions=[
            CommentStatement,
        ],
    )
    env.filters |= {  # pyright: ignore[reportAttributeAccessIssue]
        "ram_variable": filters.ram_variable,
        "quote": filters.quote,
        "csr": filters.csr,
    }

    template = env.get_template(path.name)
    result = template.render()

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, "utf-8")
    else:
        print(result)


if __name__ == "__main__":
    app()
