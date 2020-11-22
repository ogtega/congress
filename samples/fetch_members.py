#!/usr/bin/env python3

import json

from congress import fetch_house, fetch_senate


def main():
    with open("house.json", "w") as f:
        json.dump(fetch_house(), f, indent=4, sort_keys=True)
    with open("senate.json", "w") as f:
        json.dump(fetch_senate(), f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
