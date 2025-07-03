from configparser import ConfigParser
from pathlib import Path
from typing import Any

import yaml
from typer import Typer

app = Typer()


@app.command()
def main(
    work_dir: Path = Path("riscof_work"),
    config: Path = Path("config.ini"),
):
    with open(config, "r") as f:
        cfg = ConfigParser()
        cfg.read_file(f)
        skip_tests = cfg.get("mlogv32", "skip_tests").split(",")

    with open(work_dir / "test_list.yaml", "rb") as f:
        test_list: dict[str, Any] = yaml.load(f, yaml.Loader)

    filtered_list = dict[str, Any]()
    for testname, value in test_list.items():
        for skip in skip_tests:
            if skip in testname:
                break
        else:
            filtered_list[testname] = value
            continue
        _, _, test_display_name = testname.partition(
            "riscv-arch-test/riscv-test-suite/"
        )
        print(f"Skipping test: {test_display_name}")

    with open(work_dir / "test_list.yaml", "w") as f:
        yaml.dump(filtered_list, f)


if __name__ == "__main__":
    app()
