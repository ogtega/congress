import codecs
import csv
from ftplib import FTP
from functools import lru_cache
from typing import Any, Dict, List

import fiona
from fiona.collection import Collection

from .utils import download, gen_congress, headers


def fetch_districts():
    cds = list()
    ftp = FTP("ftp.census.gov")
    fp_to_state = fetch_states()
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
                            "state": fp_to_state[f["properties"]["STATEFP"]],
                            "district": f["properties"]["GEOID"][-2:],
                            "geometry": f["geometry"],
                        }
                    )
            file.close()
            break
    return cds


@lru_cache()
def fetch_states() -> Dict[str, str]:
    states: Dict[str, str] = dict()

    file = download("https://www2.census.gov/geo/docs/reference/state.txt", headers)
    reader = csv.DictReader(codecs.iterdecode(file, "utf-8"), delimiter="|")

    for row in reader:
        states[row["STATE"]] = row["STUSAB"].lower()

    file.close()
    return states
