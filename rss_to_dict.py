from datetime import datetime

import dateutil.parser
from nested_lookup import nested_lookup
import requests
import xmltodict
import requests_cache

requests_cache.install_cache("test_cache")


def parse_pubDate(pubDate):
    if pubDate is None:
        return None
    return dateutil.parser.parse(pubDate).isoformat()


def get_categories(channel):
    raw_categories = channel.get("itunes:category", None)
    categories = nested_lookup("@text", raw_categories)
    return categories


def get_enclosure(item):
    raw_enclosure = item.get("enclosure", None)
    if raw_enclosure is None:
        return None
    enclosure = {}
    enclosure["length"] = raw_enclosure.get("@length", None)
    enclosure["type"] = raw_enclosure.get("@type", None)
    enclosure["url"] = raw_enclosure.get("@url", None)
    return enclosure


def get_episode(item):
    episode = {}
    episode["category"] = item.get("category", None)
    episode["description"] = item.get("description", None)
    episode["enclosure"] = get_enclosure(item)
    episode["guid"] = item.get("guid", None).get("#text", None)
    episode["itunes:block"] = item.get("itunes:block", None)
    episode["itunes:duration"] = item.get("itunes:duration", None)
    try:
        episode["itunes:episode"] = int(item.get("itunes:episode", None))
    except TypeError:
        episode["itunes:episode"] = None
    episode["itunes:episodeType"] = item.get("itunes:episodeType", None)
    episode["itunes:explicit"] = item.get("itunes:explicit", None)
    try:
        episode["itunes:image"] = item["itunes:image"]["@href"]
    except KeyError:
        episode["itunes:image"] = None
    try:
        episode["itunes:season"] = int(item.get("itunes:season", None))
    except TypeError:
        episode["itunes:season"] = None
    episode["itunes:title"] = item.get("itunes:title", None)
    episode["link"] = item.get("link", None)
    episode["pubDate"] = item.get("pubDate", None)

    episode["pubDate_iso"] = parse_pubDate(episode["pubDate"])
    episode["pubDate_basic"] = dateutil.parser.parse(episode["pubDate"]).strftime(
        "%Y-%-m-%-m"
    )
    episode["pubDate_pretty"] = dateutil.parser.parse(episode["pubDate"]).strftime(
        "%B %-d, %Y"
    )

    episode["title"] = item.get("title", None)

    return episode


def get_episodes(channel):
    episodes = []
    items = channel.get("item", None)
    for item in items:
        episode = get_episode(item)
        episodes.append(episode)
    return episodes


def parse(url):
    podcast_dict = {}
    podcast_dict["url"] = url
    r = requests.get(url)
    parsed_xml = xmltodict.parse(r.text)
    channel = parsed_xml["rss"]["channel"]

    podcast_dict["copyright"] = channel.get("copyright", None)
    podcast_dict["creativeCommons:license"] = channel.get(
        "creativeCommons:license", None
    )

    podcast_dict["description"] = channel.get("description", None)
    podcast_dict["episodes"] = get_episodes(channel)
    podcast_dict["generator"] = channel.get("generator", None)
    podcast_dict["image"] = channel.get("image", None).get("url", None)
    podcast_dict["itunes:author"] = channel.get("itunes:author", None)
    podcast_dict["itunes:block"] = channel.get("itunes:block", None)
    podcast_dict["itunes:category"] = get_categories(channel)
    podcast_dict["itunes:complete"] = channel.get("itunes:complete", None)
    podcast_dict["itunes:explicit"] = channel.get("itunes:explicit", None)
    podcast_dict["itunes:image"] = channel.get("itunes:image", None).get("@href", None)
    podcast_dict["itunes:keywords"] = channel.get("itunes:keywords", None)
    podcast_dict["itunes:owner"] = channel.get("itunes:owner", None)
    podcast_dict["itunes:new-feed-url"] = channel.get("itunes:new-feed-url", None)
    podcast_dict["itunes:subtitle"] = channel.get("itunes:subtitle", None)
    podcast_dict["itunes:title"] = channel.get("itunes:title", None)
    podcast_dict["itunes:type"] = channel.get("itunes:type", None)
    podcast_dict["language"] = channel.get("language", None)
    podcast_dict["lastBuildDate"] = channel.get("lastBuildDate", None)
    podcast_dict["lastBuildDate_iso"] = parse_pubDate(podcast_dict["lastBuildDate"])
    podcast_dict["link"] = channel.get("link", None)
    podcast_dict["managingEditor"] = channel.get("managingEditor", None)
    podcast_dict["pubDate"] = channel.get("pubDate", None)
    podcast_dict["pubDate_iso"] = parse_pubDate(podcast_dict["pubDate"])
    podcast_dict["webMaster"] = channel.get("webMaster", None)
    podcast_dict["title"] = channel.get("title", None)
    return podcast_dict