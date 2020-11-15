import xml.etree.cElementTree as ET
from typing import Dict, List

from .utils import download, headers


def fetch_senate():
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


def fetch_house():
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
