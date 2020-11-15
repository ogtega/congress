#!/usr/bin/env python3

from congress import (
    fetch_bills,
    fetch_districts,
    fetch_house,
    fetch_senate,
    get_congress,
)


def main():
    congress = get_congress()
    fetch_house()
    fetch_senate()
    fetch_districts()
    fetch_bills(congress)


if __name__ == "__main__":
    main()
