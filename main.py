import os
import shutil
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = "./out/"

URL_PLACEHOLDER="?#?"
BASE_URL = "https://didattica.polito.it/portal/pls/portal/"
VC_BASE_URL = f"{BASE_URL}sviluppo.videolezioni.vis?cor={URL_PLACEHOLDER}"


def get_page_urls(html: str) -> list[str]:
    urls = []
    soup = BeautifulSoup(html, features="html.parser")
    elems = soup.find("div", {"id": "navbar_left_menu"}) # Get navbar...
    elems = elems.find_all("li", {"class": "h5"}) # ... get all h5 tags ...
    for i in elems:
        partial_url = i.find("a")["href"] # ... finally get the hrefs from the <a> children
        url = f"{BASE_URL}{partial_url}" # Transform to full URL
        urls.append(url)
    return urls


def get_video_urls(page_urls: list[str], s: requests.Session) -> list[str]:
    urls = []
    for i in page_urls:
        r = s.get(i) # Visit page...
        soup = BeautifulSoup(r.text, features="html.parser")
        urls.append(soup.find("video").find("source")["src"]) # ...and get <source> inside <video>
    return urls


def download_videos(video_urls: list[str], s: requests.Session, id: int) -> None:
    tot_count = len(video_urls)
    if not os.path.exists(OUTPUT_DIR): # Check if main output subdirectory exists and create it if not
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(f"{OUTPUT_DIR}{id}"): # Check if course subdirectory exists and create it if not
        os.makedirs(f"{OUTPUT_DIR}{id}")
    for count, value in enumerate(video_urls):
        print(f"Downloading video {count + 1}/{tot_count}")
        filename = value.split("/")[-1] # Get filename from url
        with s.get(value, stream=True) as r:
            with open(f"{OUTPUT_DIR}{id}/{filename}", "wb") as f:
                shutil.copyfileobj(r.raw, f)


def main():
    owa_session = input("Enter the owa_session cookie value: ")
    course = input("Enter the course ID: ")
    cookies = {"owa_session": owa_session}
    s = requests.Session()
    r = s.get(VC_BASE_URL.replace(URL_PLACEHOLDER, course), cookies=cookies)
    #If anyone has a better way to check for incorrect values, let me know!
    if "Access denied!" in r.text:
        print("Access denied! Make sure the cookie value is correct!")
        exit(1)
    elif "no data found" in r.text:
        print("No data found! Make sure the course ID is correct!")
        exit(2)
    page_urls = get_page_urls(r.text)
    video_urls = get_video_urls(page_urls, s)
    download_videos(video_urls, s, course)

main()

