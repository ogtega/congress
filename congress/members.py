import xml.etree.cElementTree as ET
from typing import Any, Dict, List, Optional, Set

from .utils import download, headers


class Committee:
    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name


class Member:
    def __init__(
        self,
        id: str,
        fname: str,
        lname: str,
        party: str,
        state: str,
        srank: Optional[str] = None,
        district: Optional[str] = None,
        lisid: Optional[str] = None,
        committees: List[str] = list(),
    ) -> None:
        self.id = id
        self.fname = fname
        self.lname = lname
        self.party = party
        self.state = state
        self.srank = srank
        self.district = district
        self.lisid = lisid
        self.committees = committees


class ChamberData:
    def __init__(
        self, members: List[Member] = list(), committees: List[Committee] = list()
    ):
        self.members = members
        self.committees = committees


def fetch_senate() -> ChamberData:
    res = ChamberData()
    committee_set: Set[str] = set()

    file = download(
        "https://www.senate.gov/legislative/LIS_MEMBER/cvc_member_data.xml", headers
    )

    parser = ET.iterparse(file.name, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event == "end" and elem.tag == "senator":
            name = elem.find("name")
            assignments = elem.find("committees")
            comcodes = list()

            for assignment in assignments:
                code = assignment.attrib.get("code")
                if code in committee_set or not len(code):
                    continue

                res.committees.append(Committee(code.lower(), assignment.text))
                committee_set.add(code)
                comcodes.append(code)

            res.members.append(
                Member(
                    elem.find("bioguideId").text,
                    name.find("first").text,
                    name.find("last").text,
                    elem.find("party").text,
                    elem.find("state").text,
                    elem.find("stateRank").text,
                    committees=comcodes,
                )
            )

    file.close()
    return res


def fetch_house() -> ChamberData:
    res = ChamberData()

    file = download("https://clerk.house.gov/xml/lists/MemberData.xml", headers)

    parser = ET.iterparse(file.name, events=("start", "end"))

    event: str
    elem: ET.Element
    for event, elem in parser:
        if event != "end":
            continue
        if elem.tag == "member":
            info = elem.find("member-info")
            assignments = elem.find("committee-assignments")

            res.members.append(
                Member(
                    info.find("bioguideID").text,
                    info.find("firstname").text,
                    info.find("lastname").text,
                    info.find("party").text,
                    info.find("state").attrib.get("postal-code"),
                    district=elem.find("statedistrict").text,
                    committees=list(
                        filter(
                            lambda x: len(x) > 1,
                            map(lambda x: f"h{get_house_comcode(x)}", assignments),
                        )
                    ),
                )
            )
        if elem.tag == "committees":
            for committee in elem:
                res.committees.append(
                    Committee(
                        ("j" if committee.attrib.get("type") == "joint" else "h")
                        + get_house_comcode(committee),
                        committee.find(f"{committee.tag}-fullname").text,
                    )
                )

    file.close()
    return res


def get_house_comcode(elem: ET.Element) -> str:
    return str.lower(
        elem.attrib.get(f"{elem.tag[:-6]}code", "")
    )  # Gets either com or subcom from r"(com|subcom)mitte" the tag name
