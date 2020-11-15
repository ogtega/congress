#!/usr/bin/env python3

import json
from congress import fetch_districts


def main():
    with open("districts.json", "w") as f:
        json.dump(fetch_districts(), f)


if __name__ == "__main__":
    main()
