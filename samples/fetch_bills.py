#!/usr/bin/env python3

import json
import os

from congress import fetch_bills


def main():
    bills = fetch_bills()

    for bill in bills:
        fname = f"bills/{bill.id}.json"
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, "w") as f:
            json.dump(
                {
                    "id": bill.id,
                    "title": bill.title,
                    "congress": bill.congress,
                    "summary": bill.summary,
                    "subjects": bill.subjects,
                    "sponsors": bill.sponsors,
                    "cosponsors": bill.cosponsors,
                },
                f,
                indent=4,
                sort_keys=True,
            )


if __name__ == "__main__":
    main()
