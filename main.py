#!/usr/bin/env python3

import fiona
import asyncio, math
import tempfile
import json
from ftplib import FTP
from datetime import datetime
from typing import List
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
cds_path = "geo/tiger/TIGER{}/CD/"


async def main():
    await asyncio.gather(fetch_senate(), fetch_house(), fetch_cds())


def fetch_cds():
    ftp = FTP("ftp.census.gov")
    ftp.login()
    for year, cd in gen_congress():
        files: List[str] = ftp.nlst(cds_path.format(year))
        if files:
            print(files)
            response: Response = get("https://www2.census.gov/{}".format(files[0]))

            tmp = tempfile.NamedTemporaryFile(suffix=".zip")
            tmp.write(response.content)
            shapefile_to_json(
                "zip://{}".format(tmp.name), "/tl_{}_us_cd{}.shp".format(year, cd)
            )
            tmp.close()
            break


async def shapefile_to_json(file, shape):
    geojson = {"type": "FeatureCollection", "features": []}
    with fiona.open(shape, vfs=file) as source:
        for f in source:
            geojson["features"].append(f)
    with open(r"shape.json", "w") as file:
        json.dump(geojson, file)


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
                "{{{}, {}, {}, {}, {{{}, {}}}".format(
                    bioguide, fname, lname, party, state, district
                )
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
                "{{{}, {}, {}, {}, {{{}, {}}}}}".format(
                    bioguide, fname, lname, party, state, _class
                )
            )

            elem.clear()


def gen_congress(year=datetime.today().year):
    for i in range(year, 1788, -1):
        yield (i, math.floor((i + 1) / 2 - 894))


if __name__ == "__main__":
    asyncio.run(main())
