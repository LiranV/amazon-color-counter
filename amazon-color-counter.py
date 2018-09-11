#!/usr/bin/env python3

import sys
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qs
from bs4 import BeautifulSoup
from collections import defaultdict
from prettytable import PrettyTable
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class AmazonReviewsColorCounter():
    COLOR_STR = "Color: "

    def __init__(self):
        self._driver = self._init_webdriver()

    def _init_webdriver(self, headless=True):
        options = Options()
        options.set_headless(headless=headless)
        driver = webdriver.Firefox(firefox_options=options)
        return driver

    def _get_page_source(self, url):
        self._driver.get(url)
        return self._driver.page_source

    def _get_reviews_page_url(self, url):
        initial_url = urlsplit(url)
        page_src = self._get_page_source(url)
        soup = BeautifulSoup(page_src, "html.parser")
        reviews_page_link = soup.find("a", {"id": "dp-summary-see-all-reviews"})
        if reviews_page_link is None:
            raise ValueError("Invalid Product Page")
        reviews_page_path = reviews_page_link["href"]
        scheme, netloc, url, query, fragment = urlsplit(reviews_page_path)
        url_query = parse_qs(query)
        url_query["reviewerType"] = "all_reviews"
        new_query = urlencode(url_query, doseq=True)
        return urlunsplit((initial_url.scheme, initial_url.netloc, url, new_query, fragment))

    def _get_page(self, url, page_number):
        url += "&pageNumber={}".format(page_number)
        page_src = self._get_page_source(url)
        return BeautifulSoup(page_src, "html.parser")

    def _get_last_page(self, url):
        data = self._get_page(url, 1)
        return data.find("ul", class_="a-pagination").find_all("li")[-2].string

    def count_colors(self, product_page_url, page_limit=None):
        reviews_page_url = self._get_reviews_page_url(product_page_url)
        color_counter = defaultdict(int)
        max_page_number = int(self._get_last_page(reviews_page_url))
        page_limit = max_page_number if page_limit is None else min(page_limit, max_page_number)
        for i in range(1, page_limit+1):
            print("Processing reviews page #{}".format(i))
            page = self._get_page(reviews_page_url, i)
            for elem in page.findAll(class_='a-size-mini a-link-normal a-color-secondary'):
                color_string = None
                str_list = elem.strings
                for string in str_list:
                    string = string.strip()
                    if string.startswith(AmazonReviewsColorCounter.COLOR_STR):
                        color_string = string[len(AmazonReviewsColorCounter.COLOR_STR):]
                if color_string is not None:
                    color_counter[color_string] += 1
        return color_counter

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Please provide the URL of the product as an argument.")
    else:
        arcc = AmazonReviewsColorCounter()
        color_counter = arcc.count_colors(sys.argv[1])
        arcc.close()
        total_counted_colors = sum(color_counter.values())
        table = PrettyTable()
        table.field_names = ["Color", "Count", "%"]
        for color_count in sorted(color_counter.items(), key=lambda x: x[1], reverse=True):
            color_pick_percentage = round(color_count[1] * 100 / total_counted_colors, 2)
            table.add_row(color_count + (color_pick_percentage,))
        print(table)
