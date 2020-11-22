#!/usr/bin/env python3

import json
from congress import fetch_districts


def main():
    with open("districts.json", "w") as f:
        json.dump(fetch_districts(), f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
