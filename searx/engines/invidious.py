# SPDX-License-Identifier: AGPL-3.0-or-later
"""Invidious (Videos)

If you want to use invidious with SearXNG you should setup one locally.
No public instance offer a public API now

- https://github.com/ChathurangaCPM/search-engine/issues/2722#issuecomment-2884993248

"""
from __future__ import annotations

import time
import random
from urllib.parse import quote_plus, urlparse
from dateutil import parser

from searx.utils import humanize_number

# about
about = {
    "website": 'https://api.invidious.io/',
    "wikidata_id": 'Q79343316',
    "official_api_documentation": 'https://docs.invidious.io/api/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ["videos", "music"]
paging = True
time_range_support = True

# base_url can be overwritten by a list of URLs in the settings.yml
base_url: list | str = []


def init(_):
    if not base_url:
        raise ValueError("missing invidious base_url")


def request(query, params):
    time_range_dict = {
        "day": "today",
        "week": "week",
        "month": "month",
        "year": "year",
    }

    if isinstance(base_url, list):
        params["base_url"] = random.choice(base_url)
    else:
        params["base_url"] = base_url

    search_url = params["base_url"] + "/api/v1/search?q={query}"
    params["url"] = search_url.format(query=quote_plus(query)) + "&page={pageno}".format(pageno=params["pageno"])

    if params["time_range"] in time_range_dict:
        params["url"] += "&date={timerange}".format(timerange=time_range_dict[params["time_range"]])

    if params["language"] != "all":
        lang = params["language"].split("-")
        if len(lang) == 2:
            params["url"] += "&range={lrange}".format(lrange=lang[1])

    return params


def response(resp):
    results = []

    search_results = resp.json()
    base_invidious_url = resp.search_params['base_url'] + "/watch?v="

    for result in search_results:
        rtype = result.get("type", None)
        if rtype == "video":
            videoid = result.get("videoId", None)
            if not videoid:
                continue

            url = base_invidious_url + videoid
            thumbs = result.get("videoThumbnails", [])
            thumb = next((th for th in thumbs if th["quality"] == "sddefault"), None)
            if thumb:
                thumbnail = thumb.get("url", "")
            else:
                thumbnail = ""

            # some instances return a partial thumbnail url
            # we check if the url is partial, and prepend the base_url if it is
            if thumbnail and not urlparse(thumbnail).netloc:
                thumbnail = resp.search_params['base_url'] + thumbnail

            publishedDate = parser.parse(time.ctime(result.get("published", 0)))
            length = time.gmtime(result.get("lengthSeconds"))
            if length.tm_hour:
                length = time.strftime("%H:%M:%S", length)
            else:
                length = time.strftime("%M:%S", length)

            results.append(
                {
                    "url": url,
                    "title": result.get("title", ""),
                    "content": result.get("description", ""),
                    "length": length,
                    "views": humanize_number(result['viewCount']),
                    "template": "videos.html",
                    "author": result.get("author"),
                    "publishedDate": publishedDate,
                    "iframe_src": resp.search_params['base_url'] + '/embed/' + videoid,
                    "thumbnail": thumbnail,
                }
            )

    return results
