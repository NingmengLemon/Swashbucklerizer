from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
import requests

import hashlib
import json
import typing
from datetime import datetime, timezone
import time
import os
import re

from swbkarchive import Media, MediaType, Diary, SwbkArchive


def new_brower():
    option = Options()
    option.binary_location = "./chrome-win/chrome.exe"
    service = Service(executable_path="./chrome-win/chromedriver.exe")
    browser = webdriver.Chrome(options=option, service=service)
    return browser


def save_cookies(brw: webdriver.Chrome, save_as: str):
    brw.get("https://icity.ly/")
    cookies = brw.get_cookies()
    with open(save_as, "w+", encoding="utf-8") as file:
        json.dump(cookies, file, ensure_ascii=False, indent=4)
    return cookies


def load_cookies(brw: webdriver.Chrome, cookiefile: str):
    if not os.path.exists(cookiefile):
        return
    brw.get("https://icity.ly/")
    with open(cookiefile, "r", encoding="utf-8") as file:
        cookies = json.load(file)
    for c in cookies:
        brw.add_cookie(c)


def is_logined(brw: webdriver.Chrome):
    brw.get("https://icity.ly/")
    return "welcome" not in brw.current_url


def get_page(brw: webdriver.Chrome, page: int = 1) -> list[WebElement]:
    brw.get("https://icity.ly/?page=%d" % page)
    time.sleep(1)
    try:
        brw.find_element(by=By.XPATH, value="/html/body/div[2]/div[2]/div/div/div")
    except NoSuchElementException:
        pass
    else:
        return []
    container = brw.find_elements(
        by=By.XPATH, value="/html/body/div[2]/div[2]/div/ul[1]/li"
    )
    return container


def element_to_diary(element: WebElement) -> Diary:
    text = element.find_element(by=By.CLASS_NAME, value="comment").text
    try:
        photo_bar = element.find_element(by=By.CLASS_NAME, value="photos")
    except NoSuchElementException:
        photo_urls = []
    else:
        photo_urls = [
            re.sub(r"/\d+x\d+$", "", e.get_attribute("src"), 1)
            for e in photo_bar.find_elements(by=By.TAG_NAME, value="img")
        ]
    pubtime_str = element.find_element(by=By.TAG_NAME, value="time").get_attribute(
        "datetime"
    )
    pubtime = (
        time.mktime(time.strptime(pubtime_str, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    )
    photos = [
        (
            requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43",
                    "Referer": "https://icity.ly/",
                },
            ).content,
            url,
        )
        for url in photo_urls
    ]
    diary = Diary(time_=pubtime)
    counter = 1
    text = text.replace("\n", "  \n")
    for p, u in photos:
        filename = hashlib.md5(p).hexdigest() + "." + u.split(".")[-1]
        text += "\n\n![Image %d](appdata/Image/%s)" % (counter, filename)
        counter += 1
        diary.add_media(Media(p, MediaType.IMAGE, u.split(".")[-1]))

    diary.content = text
    return diary
    # return text, photos, pubtime


def export(diarylist: list[Diary], save_as: str):
    archive = SwbkArchive(time_=time.time())
    for diary in diarylist:
        archive.add_diary(diary)
    archive.export_as_zipfile(save_as)


def main():
    browser = new_brower()
    load_cookies(browser, "./cookies.json")
    time.sleep(1)
    while not is_logined(browser):
        print("在浏览器中登录。完成后按下 Enter")
        input()
        time.sleep(1)
    save_cookies(browser, "./cookies.json")
    browser.get("https://icity.ly/?page=1")
    diarylist: list[Diary] = []
    page_container = ["Not Empty"]
    page = 1
    while page_container:
        print("Handling page", page)
        page_container = get_page(browser, page=page)
        diarylist += [element_to_diary(e) for e in page_container]
        page += 1
    export(diarylist, "./export_%d.zip" % (round(time.time())))
    browser.quit()
    input("All Done! Press enter to exit.")
    return 0


if __name__ == "__main__":
    exit(main())
