#!/usr/bin/env python3

import json
import math
import tempfile
import urllib
import xml.etree.cElementTree as ET
from datetime import datetime
from ftplib import FTP
from http.client import HTTPResponse
from typing import Dict, Generator, IO, List, Tuple
from urllib.request import Request

import fiona

headers: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36"
    )
}


def main():
    fetch_senate()
    fetch_house()
    fetch_cds()


def fetch_cds():
    ftp = FTP("ftp.census.gov")
    ftp.login()
    for year, _ in gen_congress():
        files: List[str] = ftp.nlst("geo/tiger/TIGER{}/CD/".format(year))
        if files:
            response: HTTPResponse = urllib.request.urlopen(
                "https://www2.census.gov/{}".format(files[0])
            )

            tmp = tempfile.NamedTemporaryFile(suffix=".zip")
            tmp.write(response.read())
            shapefile_to_json("zip://{}".format(tmp.name))
            tmp.close()
            break


def fetch_house():
    file = download("https://clerk.house.gov/xml/lists/MemberData.xml", headers)

    parser = ET.iterparse(file.name, events=("start", "end"))

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
    file.close()


def fetch_senate():
    file = download(
        "https://www.senate.gov/general/contact_information/senators_cfm.xml", headers
    )

    parser = ET.iterparse(file.name, events=("start", "end"))

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
    file.close()


def download(url: str, headers: Dict[str, str] = dict()) -> IO[bytes]:
    request = Request(url)
    request.headers.update(headers)
    response: HTTPResponse = urllib.request.urlopen(request)

    tmp: IO[bytes] = tempfile.NamedTemporaryFile()
    tmp.write(response.read())

    return tmp


def gen_congress(year=datetime.today().year) -> Generator[Tuple[int, int], None, None]:
    for i in range(year, 1788, -1):
        yield (i, math.floor((i + 1) / 2 - 894))


def shapefile_to_json(file):
    geojson = {"type": "FeatureCollection", "features": []}
    with fiona.open(file) as source:
        for f in source:
            geojson["features"].append(f)
    with open(r"shape.json", "w") as file:
        json.dump(geojson, file, indent=4)


if __name__ == "__main__":
    main()
