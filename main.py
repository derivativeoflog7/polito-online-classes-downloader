import os
import shutil
import requests
import logging
from bs4 import BeautifulSoup

# "settings"
OUTPUT_DIR = "./out/"
DEBUGGING = False

# Constants
URL_PLACEHOLDER = "?#?"
BASE_URL = "https://didattica.polito.it/portal/pls/portal/"
VC_BASE_URL = f"{BASE_URL}sviluppo.videolezioni.vis?cor={URL_PLACEHOLDER}"


def die(msg: str, code: int) -> None:
    print(msg)
    print("Press enter to exit")
    input()
    exit(code)


def get_page_urls(html: str) -> list[str]:
    urls = []
    soup = BeautifulSoup(html, features="html.parser")
    elems = soup.find("div", {"id": "navbar_left_menu"})  # Get navbar...
    elems = elems.find_all("li", {"class": "h5"})  # ... get all h5 tags ...
    logging.info(f"Found {len(elems)} links")
    for i in elems:
        partial_url = i.find("a")["href"]  # ... finally get the hrefs from the <a> children
        url = f"{BASE_URL}{partial_url}"  # Transform to full URL
        urls.append(url)
        logging.info(f"Added {url} to list")
    return urls


def get_video_urls(page_urls: list[str], s: requests.Session) -> list[str]:
    urls = []
    for i in page_urls:
        logging.info(f"Visiting {i} to retrieve video URL")
        r = s.get(i)  # Visit page...
        soup = BeautifulSoup(r.text, features="html.parser")
        video_url = soup.find("video").find("source")["src"]
        urls.append(video_url)  # ...and get <source> inside <video>
        logging.info(f"Added {video_url} to list")
    return urls


def download_videos(video_urls: list[str], s: requests.Session, course: str) -> None:
    tot_count = len(video_urls)
    if not os.path.exists(OUTPUT_DIR):  # Check if main output subdirectory exists and create it if not
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(f"{OUTPUT_DIR}{course}"):  # Check if subdirectory for course exists and create it if not
        os.makedirs(f"{OUTPUT_DIR}{course}")
    for count, value in enumerate(video_urls):
        print(f"Downloading video {count + 1}/{tot_count}")
        filename = value.split("/")[-1]  # Get filename from url
        logging.info(f"Downloading {value}")
        with s.get(value, stream=True) as r:
            with open(f"{OUTPUT_DIR}{course}/{filename}", "wb") as f:
                shutil.copyfileobj(r.raw, f)


def main():
    if DEBUGGING:
        logging.basicConfig(level=logging.DEBUG)

    owa_session = input("Enter the owa_session cookie value: ")
    course = input("Enter the course ID: ")
    cookies = {"owa_session": owa_session}
    s = requests.Session()
    r = s.get(VC_BASE_URL.replace(URL_PLACEHOLDER, course), cookies=cookies)
    # If anyone has a better way to check for incorrect values, let me know!
    if "Access denied!" in r.text:
        die("Access denied! Make sure the cookie value is correct!", 1)
    elif "no data found" in r.text:
        die("No data found! Make sure the course ID is correct!", 2)
    page_urls = get_page_urls(r.text)
    video_urls = get_video_urls(page_urls, s)
    download_videos(video_urls, s, course)
    die("Done!", 0)

main()
