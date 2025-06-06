#!/usr/bin/env bash
set -euox pipefail

sudo chown -R vscode /workspaces

uv sync
