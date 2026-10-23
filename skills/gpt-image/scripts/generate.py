#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openai>=2.32.0",
#     "python-dotenv>=1.0",
#     "json5>=0.9",
# ]
# ///
"""Run the image CLI from this checkout only."""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_src = Path(__file__).resolve().parents[3] / "src"
    if not (repo_src / "gpt_image_cli" / "cli.py").is_file():
        print(
            "error: local src/gpt_image_cli/cli.py not found; keep the complete skill repository together.",
            file=sys.stderr,
        )
        return 2

    sys.path.insert(0, str(repo_src))
    from gpt_image_cli.cli import main as cli_main

    return int(cli_main() or 0)


if __name__ == "__main__":
    sys.exit(main())
