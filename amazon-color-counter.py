#!/usr/bin/env python3

import sys
import requests
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qs
from bs4 import BeautifulSoup
from collections import defaultdict
from prettytable import PrettyTable

COLOR_STR = "Color: "


def get_reviews_page_url(url):
    initial_url = urlsplit(url)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    reviews_page_link = soup.find("a", {"id": "dp-summary-see-all-reviews"})
    if reviews_page_link is None:
        raise ValueError("Invalid Product Page")
    reviews_page_path = reviews_page_link["href"]
    scheme, netloc, url, query, fragment = urlsplit(reviews_page_path)
    url_query = parse_qs(query)
    url_query["reviewerType"] = "all_reviews"
    new_query = urlencode(url_query, doseq=True)
    return urlunsplit((initial_url.scheme, initial_url.netloc, url, new_query, fragment))


def get_page(url, page_number):
    url += "&pageNumber={}".format(page_number)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'}
    r = requests.get(url, headers=headers)
    return BeautifulSoup(r.text, "html.parser")


def get_last_page(url):
    data = get_page(url, 1)
    return data.find("ul", class_="a-pagination").find_all("li")[-2].string


def count_colors(product_page_url):
    reviews_page_url = get_reviews_page_url(product_page_url)

    color_counter = defaultdict(int)
    for i in range(1, int(get_last_page(reviews_page_url))+1):
        print("Processing page #{}".format(i))
        page = get_page(reviews_page_url, i)
        for elem in page.findAll(class_='a-size-mini a-link-normal a-color-secondary'):
            color_string = None
            str_list = elem.strings
            for string in str_list:
                if string.startswith(COLOR_STR):
                    color_string = string[len(COLOR_STR):]
            if color_string is not None:
                color_counter[color_string] += 1
    return color_counter


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Please provide the URL of the product as an argument.")
    else:
        try:
            color_counter = count_colors(sys.argv[1])
        except requests.ConnectionError as e:
            sys.exit("Failed while trying to connect to: {}".format(e.request.url))
        total_counted_colors = sum(color_counter.values())
        table = PrettyTable()
        table.field_names = ["Color", "Count", "%"]
        for color_count in sorted(color_counter.items(), key=lambda x: x[1], reverse=True):
            color_pick_percentage = round(color_count[1] * 100 / total_counted_colors, 2)
            table.add_row(color_count + (color_pick_percentage,))
        print(table)
