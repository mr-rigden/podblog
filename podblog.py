import json
import os
import shutil
import sys
from urllib.parse import urlparse


import markdown

import requests
import requests_cache


from slugify import slugify
from jinja2 import Environment, FileSystemLoader

import rss_to_dict


DEBUG = True
if DEBUG:
    requests_cache.install_cache("audio_cache")


BASE_PATH = os.path.dirname(os.path.realpath(__file__))
OUT_PUT_PATH = os.path.join(BASE_PATH, "output")
TEMPLATES = os.path.join(BASE_PATH, "templates")


file_loader = FileSystemLoader(TEMPLATES)
env = Environment(loader=file_loader)


def update_podblog(podblog_path):
    podblog_path = os.path.abspath(podblog_path)
    config_path = os.path.join(podblog_path, "config.json")
    config = {}
    with open(config_path) as f:
        config = json.load(f)
    config["podblog_path"] = podblog_path
    config["www"] = os.path.join(podblog_path, "www")
    config[
        "madewith"
    ] = "Made with <a href='https://github.com/mr-rigden/podblog'>PodBlog</a>"

    os.makedirs(config["www"], exist_ok=True)
    podcast = rss_to_dict.parse(config["rss_url"])
    podcast["config"] = config
    for each in podcast["episodes"]:
        each["title_slug"] = slugify(each["title"])
    if config["archive"]:
        podcast = archive(podcast)
    save_podcast_json(podcast)
    copy_static_files(podcast)
    make_sitemap(podcast)
    make_frontpage(podcast)
    for episode in podcast["episodes"]:
        make_episode(episode, podcast)


def archive(podcast):
    audio_path = os.path.join(podcast["config"]["www"], "audio")
    os.makedirs(audio_path, exist_ok=True)
    print(audio_path)
    for each in podcast["episodes"]:
        print(each["enclosure"]["url"])
        file_name = download_audio_file(each["enclosure"]["url"], audio_path)
        each["enclosure"]["url"] = "../audio/" + file_name

    file_name = download_coverart(podcast)
    podcast["itunes:image"] = file_name
    download_rss(podcast)

    return podcast


def download_audio_file(url, audio_dir):
    header = requests.head(url, allow_redirects=True)
    file_name = os.path.basename(urlparse(header.url).path)
    file_path = os.path.join(audio_dir, file_name)
    if os.path.exists(file_path):
        print("exists")
        return file_name
    r = requests.get(url, allow_redirects=True)
    open(file_path, "wb").write(r.content)
    return file_name


def download_rss(podcast):
    file_path = os.path.join(podcast["config"]["www"], "rss.xml")
    r = requests.get(podcast["url"], allow_redirects=True)
    with open(file_path, "w") as f:
        f.write(r.text)


def download_coverart(podcast):
    # podcast_dir = os.path.join(output_dir, slugify(podcast_dict["title"]))
    header = requests.head(podcast["itunes:image"], allow_redirects=True)
    file_name = os.path.basename(urlparse(header.url).path)
    # file_path = os.path.join(podcast_dir, "img", file_name)
    file_path = os.path.join(podcast["config"]["www"], file_name)
    if os.path.exists(file_path):
        return file_name
    r = requests.get(podcast["itunes:image"], allow_redirects=True)
    open(file_path, "wb").write(r.content)
    return file_name


def make_episode(episode, podcast):
    episode["description"] = markdown.markdown(
        episode["description"], extensions=["pymdownx.magiclink"]
    )
    episode_path = os.path.join(
        podcast["config"]["www"], episode["title_slug"], "index.html"
    )
    if not DEBUG:
        if os.path.exists(episode_path):
            return
    os.makedirs(os.path.dirname(episode_path), exist_ok=True)
    template = env.get_template("episode.html")
    output = template.render(episode=episode, podcast=podcast)
    with open(episode_path, "w") as f:
        f.write(output)


def make_frontpage(podcast):
    file_path = os.path.join(podcast["config"]["www"], "index.html")
    template = env.get_template("frontpage.html")
    output = template.render(podcast=podcast)
    with open(file_path, "w") as f:
        f.write(output)


def make_sitemap(podcast):
    file_path = os.path.join(podcast["config"]["www"], "sitemap.xml")
    template = env.get_template("sitemap.xml")
    output = template.render(podcast=podcast)
    with open(file_path, "w") as f:
        f.write(output)


def save_podcast_json(podcast):
    podcast_json_path = os.path.join(podcast["config"]["www"], "podcast.json")
    with open(podcast_json_path, "w") as f:
        f.write(json.dumps(podcast, sort_keys=True, indent=4))


def copy_static_files(podcast):
    g_static_path = os.path.join(TEMPLATES, "static")
    static_path = os.path.join(podcast["config"]["www"], "static")
    if os.path.isdir(static_path):
        return
    shutil.copytree(g_static_path, static_path)


def initialize_new_podblog(url):
    podcast = rss_to_dict.parse(url)
    podcast["title_slug"] = slugify(podcast["title"])
    podcast_path = os.path.join(OUT_PUT_PATH, podcast["title_slug"])
    podcast_www_path = os.path.join(podcast_path, "www")
    if not DEBUG:
        if os.path.isdir(podcast_path):
            print("Podblog already exists")
            exit()
    os.makedirs(podcast_path, exist_ok=True)
    os.makedirs(podcast_www_path, exist_ok=True)
    sample_list = [
        {"Name": "Name", "URL": "URL"},
        {"Name": "Name", "URL": "URL"},
    ]
    config = {}
    config["archive"] = False
    config["base_url"] = ""
    config["menu"] = sample_list
    config["rss_url"] = url
    config["social"] = sample_list
    config["subscribe"] = sample_list
    config["title"] = podcast["title"]
    config_path = os.path.join(podcast_path, "config.json")
    with open(config_path, "w") as f:
        f.write(json.dumps(config, sort_keys=True, indent=4))


if __name__ == "__main__":
    mode = ""

    try:
        mode = sys.argv[1]
    except IndexError:
        print("Missing Mode")
        exit()

    if mode == "-i":
        print("Initializing...")
        try:
            url = sys.argv[2]
            print(url)
        except IndexError:
            print("Missing URL")
            exit()
        initialize_new_podblog(url)
        exit()

    if mode == "-u":
        print("Updating...")
        try:
            podblog_path = sys.argv[2]
            print(podblog_path)
            update_podblog(podblog_path)
        except IndexError:
            print("Missing Podblog")
            exit()
        exit()

    print("Unknown Mode :(")
    exit()
