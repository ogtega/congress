import math
import tempfile
import urllib
from datetime import datetime
from http.client import HTTPResponse
from typing import IO, Dict, Generator
from urllib.request import Request


class Congress:
    number: int
    year: int

    def __init__(self, num: int, year: int):
        self.number = num
        self.year = year


headers: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/39.0.2171.95 Safari/537.36"
    )
}


def download(url: str, headers: Dict[str, str] = dict(), suffix: str = "") -> IO[bytes]:
    request = Request(url)
    request.headers.update(headers)
    response: HTTPResponse = urllib.request.urlopen(request)

    tmp: IO[bytes] = tempfile.NamedTemporaryFile(suffix=suffix)
    tmp.write(response.read())
    tmp.seek(0)

    return tmp


def get_congress() -> int:
    return next(gen_congress()).number


def gen_congress(year=datetime.today().year) -> Generator[Congress, None, None]:
    for i in range(year, 1788, -1):
        yield Congress(math.floor((i + 1) / 2 - 894), i)
