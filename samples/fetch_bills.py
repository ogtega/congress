#!/usr/bin/env python3

import json

from congress import fetch_bills, get_congress


def main():
    congress = get_congress()
    with open("bills.json", "w") as f:
        json.dump(fetch_bills(congress), f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
