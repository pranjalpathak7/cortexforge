"""Prepare a committed sample without modifying the versioned template."""

import shutil
from pathlib import Path

from cortexforge.repository import git


def prepare(destination, sample="payments"):
    if sample not in {"payments", "refund-service"}:
        raise ValueError("Unknown controlled sample")
    target = Path(destination).resolve()
    if target.exists():
        return target
    shutil.copytree(
        Path(__file__).resolve().parents[1] / "sample-repos" / sample,
        target,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    git(target, "init")
    git(target, "add", ".")
    git(
        target,
        "-c",
        "user.name=CortexForge",
        "-c",
        "user.email=local@example.invalid",
        "commit",
        "-m",
        "Sample baseline",
    )
    return target


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", choices=["payments", "refund-service"], default="payments")
    args = parser.parse_args()
    destination = ".cortexforge/sample" if args.sample == "payments" else ".cortexforge/refund-service"
    print(prepare(destination, args.sample))
