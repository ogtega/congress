#!/usr/bin/env python3

from congress import districts
import json
from congress import fetch_districts
import os


def main():
    districts = fetch_districts()

    for district in districts:
        fname = f"cds/{district['state']}-{district['district']}.json"
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, "w") as f:
            json.dump(district, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
