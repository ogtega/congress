import calendar
import json
import re
import time
import xml.etree.cElementTree as ET
import zipfile
from datetime import datetime
from functools import reduce
from typing import Deque, List

from .utils import download, get_congress, headers

senate_vote_pattern = re.compile(
    "congress=([0-9]+)&session=([0-9])&vote=([0-9]+)$"
)  # Used to match senate roll call vote urls


class Vote:
    def __init__(self, chamber: str, action: str, date: int) -> None:
        self.chamber = chamber
        self.action = action
        self.date = date
        self.yeas = list()
        self.nays = list()
        self.nv = list()


class Bill:
    def __init__(
        self,
        id: str = "",
        title: str = "",
        congress: int = "",
        summary: str = "",
        subjects: List[str] = list(),
        sponsors: List[str] = list(),
        cosponsors: List[str] = list(),
        votes: List[Vote] = list(),
    ) -> None:
        self.id = id
        self.title = title
        self.congress = congress
        self.subjects = subjects
        self.summary = summary
        self.sponsors = sponsors
        self.cosponsors = cosponsors
        self.votes = votes


def fetch_bills(congress: int = get_congress()) -> List[Bill]:
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


# https://github.com/usgpo/bill-status/blob/master/BILLSTATUS-XML_User_User-Guide.md
def parse_bill(file) -> Bill:
    bill: Bill = Bill()
    parser = ET.iterparse(file, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event != "end":
            continue

        if elem.tag == "bill":
            num = elem.find("billNumber").text
            bill_type = elem.find("billType").text.lower()

            bill.id = f"{bill_type}{num}"
            bill.title = elem.find("title").text
            bill.congress = int(elem.find("congress").text)
        if elem.tag == "billSubjects":
            items = elem.findall(".//name")
            bill.subjects = list(map(lambda n: n.text.lower(), items))
        if elem.tag == "billSummaries" and len(elem):
            bill.summary = get_summary(elem)
        if elem.tag == "sponsors" or elem.tag == "cosponsors":
            items = elem.findall("./item/bioguideId")
            if elem.tag == "sponsors":
                bill.sponsors = list(map(lambda x: x.text.lower(), items))
            else:
                bill.cosponsors = list(map(lambda x: x.text.lower(), items))
        if elem.tag == "recordedVote":
            bill.votes.append(get_vote(elem))
    return bill


def get_summary(elem: ET.Element):
    datefmt = "%Y-%m-%d"

    summary: ET.Element = reduce(
        lambda x, y, fmt=datefmt: x
        if datetime.strptime(x.find("actionDate").text, fmt)
        > datetime.strptime(y.find("actionDate").text, fmt)
        else y,
        elem,
    )

    return summary.find("text").text


def get_vote(elem: ET.Element) -> Vote:
    url = elem.find("url").text
    m = senate_vote_pattern.search(url)

    action = elem.find("fullActionName").text
    date = calendar.timegm(time.strptime(elem.find("date").text, "%Y-%m-%dT%H:%M:%SZ"))

    if m:  # Senate roll call votes
        congress = m.group(1)
        session = m.group(2)
        num = m.group(3)

        url = "https://www.senate.gov/legislative/LIS/roll_call_votes/vote{}{}/vote_{}_{}_{}.xml".format(
            congress, session, congress, session, num
        )

        file = download(url, headers)
        return parse_votes_senate(action, date, file)
    else:  # House roll call votes
        file = download(
            url.replace("Votes", "evs"), headers
        )  # Need to do this swap to avoid 404s
        return parse_votes_house(action, date, file)


def parse_votes_house(action: str, date: int, file) -> Vote:
    parser = ET.iterparse(file, events=("start", "end"))
    vote: Vote = Vote("h", action, date)

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "recorded-vote":
            legistlator = elem.find("legislator")
            bioguide = legistlator.attrib.get("name-id").lower()
            if elem.find("vote").text.lower() in ["aye", "yea"]:
                vote.yeas.append(bioguide)
                continue
            if elem.find("vote").text.lower() in ["nay", "no"]:
                vote.nays.append(bioguide)
                continue
            vote.nv.append(bioguide)

    return vote


def parse_votes_senate(action: str, date: int, file) -> Vote:
    parser = ET.iterparse(file, events=("start", "end"))
    vote: Vote = Vote("s", action, date)

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "member":
            bioguide = elem.find("lis_member_id").text.lower()
            if elem.find("vote_cast").text.lower() == "yea":
                vote.yeas.append(bioguide)
                continue
            if elem.find("vote_cast").text.lower() == "nay":
                vote.nays.append(bioguide)
                continue
            vote.nv.append(bioguide)

    return vote
