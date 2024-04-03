#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from glob import glob
from pathlib import Path

import yaml


python_directory = "ra_utils"
markdown_directory = "docs/modules"


python_files = set(glob("*.py", root_dir=python_directory, recursive=True)) - {
    "__init__.py",
}
markdown_files = set(glob("*.md", root_dir=markdown_directory, recursive=True))


# We want a markdown file for each python file
wanted_markdown_files = {file.replace(".py", ".md") for file in python_files}
mismatch = wanted_markdown_files ^ markdown_files
if mismatch:
    print("File mismatch between python code and module docs", mismatch)
    exit(1)

# Extract the filenames of modules in the nav in mkdocs
mkdocs_text = Path("mkdocs.yml").read_text()
mkdocs = yaml.safe_load(mkdocs_text)
nav = mkdocs["nav"]
modules = next(e["Modules"] for e in nav if isinstance(e, dict) and "Modules" in e)
modules_in_toc = {next(iter(m.values())).removeprefix("modules/") for m in modules}

mismatch = modules_in_toc ^ markdown_files
if mismatch:
    print("Mismatch between module docs and index", mismatch)
    exit(1)
