#!/usr/bin/env python3

import codecs
import csv
import json
import math
import re
import tempfile
import urllib
import xml.etree.cElementTree as ET
import zipfile
from datetime import datetime
from ftplib import FTP
from functools import reduce
from http.client import HTTPResponse
from typing import IO, Any, Deque, Dict, Generator, List, Tuple
from urllib.request import Request

import fiona
from fiona.collection import Collection

headers: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36"
    )
}

senate_vote_pattern = re.compile(
    "congress=([0-9]+)&session=([0-9])&vote=([0-9]+)$"
)  # Used to match senate vroll call vote urls


def main():
    _, congress = next(gen_congress())
    fetch_states()
    fetch_cds()
    fetch_senate_members()
    fetch_house_members()
    fetch_bills(congress)
    # TODO: Get committee assignments


def fetch_bills(congress):
    bills = list()
    links = Deque(
        ["https://www.govinfo.gov/bulkdata/json/BILLSTATUS/{}".format(congress)]
    )
    types = {"hr", "s", "hjres", "sjres"}

    while len(links):
        link = links.pop()

        file = download(
            link,
            {
                "Accept": "application/json",
                "User-Agent": headers["User-Agent"],
            },
        )

        if link.endswith(".zip"):
            bulkdata = zipfile.ZipFile(file, "r")
            files = bulkdata.filelist

            for file in files:
                bills.append(parse_bill(bulkdata.open(file)))
            continue

        with open(file.name) as f:
            data = json.load(f)
            for item in data["files"]:
                if item["name"] in types:
                    links.append(item["link"])
                    continue
                if not item["folder"] and item["mimeType"] == "application/zip":
                    links.appendleft(item["link"])
    return bills


def parse_bill(file):
    bill: Dict[str, Any] = {"votes": list()}
    parser = ET.iterparse(file, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end":
            if elem.tag == "bill":
                num = elem.find("billNumber").text
                billType = elem.find("billType").text.lower()

                bill["id"] = "{}{}".format(billType, num)
                bill["title"] = elem.find("title").text
                bill["congress"] = elem.find("congress").text
            if elem.tag == "billSubjects":
                items = elem.findall(".//name")
                bill["subjects"] = list(map(lambda n: n.text, items))
            if elem.tag == "billSummaries" and len(elem):
                datefmt = "%Y-%m-%d"

                summary = reduce(
                    lambda x, y: x
                    if datetime.strptime(x.find("actionDate").text, datefmt)
                    > datetime.strptime(y.find("actionDate").text, datefmt)
                    else y,
                    elem,
                )

                bill["summary"] = summary.find("text").text
            if elem.tag == "sponsors":
                items = elem.findall("./item/bioguideId")
                bill["sponsors"] = list(map(lambda x: x.text, items))
            if elem.tag == "cosponsors" and len(elem):
                items = elem.findall("./item/bioguideId")
                bill["cosponsors"] = list(map(lambda x: x.text, items))
            if elem.tag == "recordedVote":
                url = elem.find("url").text
                m = senate_vote_pattern.search(url)

                if m:  # Senate roll call votes
                    congress = m.group(1)
                    session = m.group(2)
                    vote = m.group(3)

                    url = "https://www.senate.gov/legislative/LIS/roll_call_votes/vote{}{}/vote_{}_{}_{}.xml".format(
                        congress, session, congress, session, vote
                    )

                    file = download(url, headers)
                    bill["votes"].append(parse_votes_senate(file))
                else:  # House roll call votes
                    file = download(
                        url.replace("Votes", "evs"), headers
                    )  # Need to do this swap to avoid 404s
                    bill["votes"].append(parse_votes_house(file))
    return bill


def parse_votes_house(file):
    roll_call: Dict[str, Any] = {
        "chamber": "h",
        "yea": list(),
        "nay": list(),
        "nv": list(),
    }

    parser = ET.iterparse(file, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "recorded-vote":
            legistlator = elem.find("legislator")
            bioguide = legistlator.attrib["name-id"]
            if elem.find("vote").text.lower() == "yea":
                roll_call["yea"].append(bioguide)
                continue
            if elem.find("vote").text.lower() == "nay":
                roll_call["nay"].append(bioguide)
                continue
            roll_call["nv"].append(bioguide)

    return roll_call


def parse_votes_senate(file):
    roll_call: Dict[str, Any] = {
        "chamber": "s",
        "yea": list(),
        "nay": list(),
        "nv": list(),
    }

    parser = ET.iterparse(file, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "member":
            bioguide = elem.find("lis_member_id").text
            if elem.find("vote_cast").text.lower() == "yea":
                roll_call["yea"].append(bioguide)
                continue
            if elem.find("vote_cast").text.lower() == "nay":
                roll_call["nay"].append(bioguide)
                continue
            roll_call["nv"].append(bioguide)

    return roll_call


def fetch_states() -> List[Dict[str, str]]:
    states: List[Dict[str, str]] = list()

    file = download("https://www2.census.gov/geo/docs/reference/state.txt", headers)
    reader = csv.DictReader(codecs.iterdecode(file, "utf-8"), delimiter="|")

    for row in reader:
        states.append(
            {
                "id": row["STUSAB"].lower(),
                "fips": row["STATE"],
                "name": row["STATE_NAME"],
            }
        )

    file.close()
    return states


def fetch_cds():
    cds = list()
    ftp = FTP("ftp.census.gov")
    ftp.login()

    for year, _ in gen_congress():
        files: List[str] = ftp.nlst("geo/tiger/TIGER{}/CD/".format(year))

        if files:
            file = download(
                "https://www2.census.gov/{}".format(files[0]), headers, ".zip"
            )

            source: Collection
            with fiona.open("zip://{}".format(file.name)) as source:
                f: Dict[str, Any]
                for f in source:
                    cds.append(
                        {
                            "id": f["properties"]["GEOID"],
                            "statefp": f["properties"]["STATEFP"],
                            "district": f["properties"]["GEOID"][-2:],
                            "geometry": f["geometry"],
                        }
                    )
            file.close()
            break
    return cds


def fetch_house_members():
    members: List[Dict[str, str]] = list()
    file = download("https://clerk.house.gov/xml/lists/MemberData.xml", headers)

    parser = ET.iterparse(file.name, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "member":
            info = elem.find("member-info")

            members.append(
                {
                    "id": info.find("bioguideID").text,
                    "fname": info.find("firstname").text,
                    "lname": info.find("lastname").text,
                    "party": info.find("party").text,
                    "state": info.find("state").attrib["postal-code"],
                    "district": elem.find("statedistrict").text,
                }
            )

    file.close()
    return members


def fetch_senate_members():
    members: List[Dict[str, str]] = list()
    file = download(
        "https://www.senate.gov/legislative/LIS_MEMBER/cvc_member_data.xml", headers
    )

    parser = ET.iterparse(file.name, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "senator":
            name = elem.find("name")
            members.append(
                {
                    "id": elem.find("bioguideId").text,
                    "lis_id": elem.attrib["lis_member_id"],
                    "fname": name.find("first").text,
                    "lname": name.find("last").text,
                    "party": elem.find("party").text,
                    "state": elem.find("state").text,
                    "class": elem.find("stateRank").text,
                }
            )

    file.close()
    return members


def download(url: str, headers: Dict[str, str] = dict(), suffix: str = "") -> IO[bytes]:
    request = Request(url)
    request.headers.update(headers)
    response: HTTPResponse = urllib.request.urlopen(request)

    tmp: IO[bytes] = tempfile.NamedTemporaryFile(suffix=suffix)
    tmp.write(response.read())
    tmp.seek(0)

    return tmp


def gen_congress(year=datetime.today().year) -> Generator[Tuple[int, int], None, None]:
    for i in range(year, 1788, -1):
        yield (i, math.floor((i + 1) / 2 - 894))


if __name__ == "__main__":
    main()
