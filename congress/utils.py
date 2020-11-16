import math
import tempfile
import urllib
from datetime import datetime
from http.client import HTTPResponse
from typing import IO, Dict, Generator, Tuple
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


def get_congress() -> int:
    return next(gen_congress())[1]


def gen_congress(year=datetime.today().year) -> Generator[Tuple[int, int], None, None]:
    for i in range(year, 1788, -1):
        yield (i, math.floor((i + 1) / 2 - 894))
