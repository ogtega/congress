#!/usr/bin/env python3

import fiona
import asyncio, math
import tempfile
from ftplib import FTP
from datetime import datetime
from typing import List
from numpy.lib.utils import source
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
    # await asyncio.gather(fetch_senate(), fetch_house())
    fetch_cds()


def fetch_cds():
    ftps = FTP("ftp.census.gov")
    ftps.login()
    for year, _ in gen_congress():
        files: List[str] = ftps.nlst(cds_path.format(year))
        if files:
            response: Response = get(
                "https://www2.census.gov/{}".format(files[0]), stream=True
            )

            tmp = tempfile.TemporaryFile(suffix=".zip")
            for chunk in response.iter_content():
                tmp.write(chunk)
            shapefile_to_json(tmp)


def shapefile_to_json(file):
    with fiona.open(file) as source:
        with fiona.open(
            "out.json",
            "w",
            driver="GeoJSON",
            crs=fiona.crs.from_epsg(4326),
            schema=source.schema,
        ) as sink:
            for rec in source:
                sink.write(rec)


def gen_congress(year=datetime.today().year):
    for i in range(year, 1788, -1):
        yield (i, math.floor((i + 1) / 2 - 894))


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


if __name__ == "__main__":
    asyncio.run(main())
