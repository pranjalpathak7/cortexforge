import argparse
import json

from cortexforge.contracts import CreateRun
from cortexforge.workflow import Engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["create", "run", "step", "show", "resume"])
    parser.add_argument("--data", default=".cortexforge")
    parser.add_argument("--id")
    parser.add_argument("--repository")
    parser.add_argument("--fault", default="none")
    args = parser.parse_args()
    engine = Engine(args.data)
    if args.command == "create":
        result = engine.create(
            CreateRun(
                repository=args.repository,
                mode="demo",
                fault=args.fault,
                requirement="Add apply_discount with integer rounding and validated 0..100 percent",
            )
        )
    elif args.command == "show":
        result = engine.store.get(args.id)
    else:
        result = getattr(engine, "advance" if args.command == "step" else args.command)(args.id)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
