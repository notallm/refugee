import requests
from bs4 import BeautifulSoup

import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from hashlib import sha256

ROOT = "https://www.uscis.gov/humanitarian/refugees-and-asylum/refugees"
DEPTH = 2
TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5"
}

session = requests.Session()
session.headers.update(HEADERS)

stopwords = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def clean_text(text: str) -> str:
    tokens = []
    for token in word_tokenize(text):
        token = token.lower()
        token = re.sub(r"[^\w\s]", "", token)
        if token and token not in stopwords:
            tokens.append(lemmatizer.lemmatize(token))
    return " ".join(tokens)

def scrape_url(url: str) -> tuple:
    base = "/".join(url.split("/")[:3])
    texts = []
    urls = []
    response = session.get(url, timeout = TIMEOUT)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        print("retrieved")
        main_content = soup.find("div", class_ = ["container--main", "content", "documentViewer"])
        if main_content:
            for tag in main_content.find_all(["p", "a", "li", "span"]):
                text = clean_text(tag.get_text())
                if tag.name == "a" and "href" in tag.attrs:
                    url = tag["href"]
                    if url[0] == "/":
                        url = base + url
                    else:
                        url = base
                    texts.append(f"{text} (URL: {url})")
                    urls.append(url)
                else:
                    texts.append(text)
        else:
            print("no div found.")
    else:
        print(f"failed to retrieve. status code {response.status_code}")
    return (" ".join(texts), list(set(urls)))

def save(url: str, text: str) -> None:
    filename = "docs/" + sha256(url.encode("utf-8")).hexdigest()
    print(f"saving to {filename}")
    with open(filename, "w+") as handler:
        handler.write(f"URL: {url}\n{text}")

if __name__ == "__main__":
    text, urls = scrape_url(ROOT)
    save(ROOT, text)
    print(text)
    print(len(urls), "urls from root")
    depth = 0
    last_urls = list(set(urls))
    while depth <= DEPTH:
        new_urls = [] # urls found at this depth
        num_last = len(last_urls)
        for i, url in enumerate(last_urls):
            split = url.split(".")[-1]
            if len(split) > 4 or split == "html":
                try:
                    text, urls = scrape_url(url)
                except Exception as e:
                    print("error:", e)
                    continue
                num_urls = len(urls)
                new_urls.extend(urls)
                print(text)
                print("-" * 50)
                if len(text) > 100:
                    save(url, text)
                else:
                    print("not saving document")
                print(f"({i}/{num_last})", "found", num_urls, "from this document and", len(new_urls), "urls total at depth", depth)
                print("-" * 50)
        depth += 1
        last_urls = list(set(new_urls))
