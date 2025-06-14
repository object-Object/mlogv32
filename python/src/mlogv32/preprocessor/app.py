from pathlib import Path
from typing import Annotated, Any, TypedDict

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from typer import Option, Typer

from mlogv32.preprocessor.extensions import CommentStatement

from .filters import FILTERS

app = Typer(
    pretty_exceptions_show_locals=False,
)


@app.command(name="file")
def command_file(
    path: Path,
    output: Annotated[Path | None, Option("-o", "--output")] = None,
):
    path = path.resolve()

    env = create_jinja_env(path.parent)
    template = env.get_template(path.name)
    result = template.render()

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, "utf-8")
    else:
        print(result)


@app.command()
def configs(yaml_path: Path):
    with yaml_path.open("rb") as f:
        data: ConfigsYaml = yaml.load(f, yaml.Loader)

    output_dir = yaml_path.parent
    env = create_jinja_env(output_dir)
    template = env.get_template(data["template"])

    for name, args in data["configs"].items():
        result = template.render(**(data["defaults"] | args))
        (output_dir / name).with_suffix(".mlog").write_text(result, "utf-8")


def create_jinja_env(template_dir: Path):
    env = Environment(
        loader=FileSystemLoader(template_dir),
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
    env.filters |= FILTERS
    return env


class ConfigsYaml(TypedDict):
    template: str
    defaults: dict[str, Any]
    configs: dict[str, dict[str, Any]]


if __name__ == "__main__":
    app()
