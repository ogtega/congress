#!/usr/bin/env python3

import json

from congress import fetch_house, fetch_senate


def main():
    senate = fetch_senate()
    house = fetch_house()

    with open("house.json", "w") as f:
        json.dump(
            {"members": house.members, "committees": house.committees},
            f,
            indent=4,
            sort_keys=True,
        )
    with open("senate.json", "w") as f:
        json.dump(
            {"members": senate.members, "committees": senate.committees},
            f,
            indent=4,
            sort_keys=True,
        )


if __name__ == "__main__":
    main()
