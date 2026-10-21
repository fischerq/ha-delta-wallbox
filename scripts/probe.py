#!/usr/bin/env python3
"""Read-only probe of a Delta AC MAX wallbox over Modbus TCP.

    python3 scripts/probe.py 192.168.25.199 [--port 502] [--device-id 1]

Prints the decoded state the integration would see. Compare with the
wallbox app / display (charging power, session energy). Never writes.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

from delta_wallbox.client import DeltaWallboxClient  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("host")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--device-id", type=int, default=1)
    args = parser.parse_args()
    client = DeltaWallboxClient(args.host, args.port, args.device_id)
    try:
        print("serial:", client.read_serial())
        print(json.dumps(client.read_state(), indent=2))
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
