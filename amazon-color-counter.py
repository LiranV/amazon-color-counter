#!/usr/bin/env python3

import sys
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qs
from bs4 import BeautifulSoup
from collections import defaultdict
from prettytable import PrettyTable
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import tqdm


class AmazonReviewsColorCounter():
    COLOR_STR = "Color: "

    def __init__(self):
        self._driver = self._init_webdriver()

    def _init_webdriver(self, headless=True):
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        return driver

    def _get_page_source(self, url):
        self._driver.get(url)
        return BeautifulSoup(self._driver.page_source, "html.parser")

    def _get_reviews_page_url(self, url):
        url_path = urlsplit(url).path
        product_id = url_path.split('/')[3]
        return f"https://www.amazon.com/product-reviews/{product_id}"

    def _get_reviews_page(self, reviews_page_url, page_number):
        reviews_page_url += f"/ref=cm_cr_getr_d_paging_btm_next_{page_number}?pageNumber={page_number}"
        return self._get_page_source(reviews_page_url)

    def _get_last_reviews_page_number(self, url):
        data = self._get_page_source(url)
        review_count_info_text = data.find(
            "span", attrs={"data-hook": "cr-filter-info-review-count"}).string
        review_count = int(review_count_info_text.split(" ")[3].replace(",", ""))
        last_page, extra_page_needed = divmod(review_count, 10)
        return last_page + 1 if extra_page_needed else last_page

    def count_colors(self, product_page_url, page_limit=None):
        reviews_page_url = self._get_reviews_page_url(product_page_url)
        color_counter = defaultdict(int)
        last_page_number = self._get_last_reviews_page_number(reviews_page_url)
        page_limit = last_page_number if page_limit is None else min(page_limit, last_page_number)
        for i in tqdm.trange(1, page_limit+1, unit='page'):
            page = self._get_reviews_page(reviews_page_url, i)
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
        self._driver.close()


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
