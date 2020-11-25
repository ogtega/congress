import xml.etree.cElementTree as ET
from typing import Any, Dict, List, Set

from .utils import download, headers


class MemberData:
    members: List[Dict[str, Any]] = list()
    committees: List[Dict[str, str]] = list()


def fetch_senate() -> MemberData:
    res = MemberData()
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

            for assignment in assignments:
                code = assignment.attrib.get("code")
                if code in committee_set:
                    continue

                res.committees.append({"id": code.lower(), "name": assignment.text})
                committee_set.add(code)

            res.members.append(
                {
                    "id": elem.find("bioguideId").text,
                    "lis_id": elem.attrib.get("lis_member_id", None),
                    "fname": name.find("first").text,
                    "lname": name.find("last").text,
                    "party": elem.find("party").text,
                    "state": elem.find("state").text,
                    "class": elem.find("stateRank").text,
                    "committees": list(
                        filter(
                            lambda x: len(x),
                            map(lambda x: x.attrib.get("code").lower(), assignments),
                        )
                    ),
                }
            )

    file.close()
    return res


def fetch_house() -> MemberData:
    res = MemberData()

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
                {
                    "id": info.find("bioguideID").text,
                    "fname": info.find("firstname").text,
                    "lname": info.find("lastname").text,
                    "party": info.find("party").text,
                    "state": info.find("state").attrib.get("postal-code"),
                    "district": elem.find("statedistrict").text,
                    "committees": list(
                        filter(
                            lambda x: len(x) > 1,
                            map(lambda x: f"h{get_house_comcode(x)}", assignments),
                        )
                    ),
                }
            )
        if elem.tag == "committees":
            for committee in elem:
                res.committees.append(
                    {
                        "id": "h" + get_house_comcode(committee),
                        "name": committee.find(f"{committee.tag}-fullname").text,
                    }
                )

    file.close()
    return res


def get_house_comcode(elem: ET.Element):
    return str.lower(
        elem.attrib.get(f"{elem.tag[:-6]}code", "")
    )  # Gets either com or subcom from r"(com|subcom)mitte" the tag name
