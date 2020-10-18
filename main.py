#!/usr/bin/env python3

import asyncio
from requests import Response, get
import xml.etree.cElementTree as ET

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36"
    )
}

reps = "https://clerk.house.gov/xml/lists/MemberData.xml"
senators = "https://www.senate.gov/general/contact_information/senators_cfm.xml"


async def main():
    asyncio.gather(fetch_senate(), fetch_house())


async def fetch_house():
    response: Response = get(reps, headers=headers, stream=True)
    parser = ET.iterparse(response.raw, events=("start", "end"))

    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "member":
            info = elem.find("member-info")

            fname = info.find("firstname").text
            lname = info.find("lastname").text
            party = info.find("party").text
            state = info.find("state").attrib["postal-code"]
            district = elem.find("statedistrict").text
            bioguide = info.find("bioguideID").text

            print(
                "{%s, %s, %s, %s, {%s, %s}}"
                % (bioguide, fname, lname, party, state, district)
            )

            elem.clear()


async def fetch_senate():
    response: Response = get(senators, headers=headers, stream=True)
    parser = ET.iterparse(response.raw, events=("start", "end"))

    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "member":
            fname = elem.find("first_name").text
            lname = elem.find("last_name").text
            party = elem.find("party").text
            state = elem.find("state").text
            bioguide = elem.find("bioguide_id").text
            _class = elem.find("class").text

            print(
                "{%s, %s, %s, %s, {%s, %s}}"
                % (bioguide, fname, lname, party, state, _class)
            )

            elem.clear()


if __name__ == "__main__":
    asyncio.run(main())
