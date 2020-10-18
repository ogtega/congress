#!/usr/bin/env python3
from requests import Response, get
import xml.etree.cElementTree as ET

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36"
    )
}

senators = "https://www.senate.gov/general/contact_information/senators_cfm.xml"


def main():
    response: Response = get(senators, headers=headers, stream=True)
    for event, elem in ET.iterparse(response.raw, events=("start", "end")):
        print(elem)


if __name__ == "__main__":
    main()
