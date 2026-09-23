"""Reserved pilot command: closed until a reviewed protocol is explicitly authorized."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True)
    parser.parse_args()
    # Deliberately before loading a protocol, data, checkpoints or optimizer.
    # A caller-supplied authorized=true is not authorization recorded by this project.
    print(
        json.dumps(
            dict(
                status="blocked",
                reason="No explicitly authorized pilot protocol registered",
                market_data_loaded=False,
                parameter_updates=0,
            )
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
