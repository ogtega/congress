import math
import tempfile
import urllib
from datetime import datetime
from http.client import HTTPResponse
from typing import IO, Dict
from urllib.request import Request

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


def get_congress(year=datetime.today().year) -> int:
    return math.floor((year + 1) / 2 - 894)
