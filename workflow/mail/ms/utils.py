from bs4 import BeautifulSoup
from typing import Tuple, List
import re


def parse_body(html_content: str) -> Tuple[str, List[str]]:
    """
    Parse body to get text and urls
    """
    """
    Parse body to get text and urls
    remove table (signature element should be removed)
    ignore urls from spingence.com, linkedin.com, spingence-ai, facebook.com, smasoft-tech.com
    return text and urls

    :param html_content: raw html content
    :return: text, urls

    """
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.body
    # drop all tables
    for table in body.find_all("table"):
        table.decompose()
    text_list = []
    urls = []
    ignore_domains = [
        "spingence.com",
        "linkedin.com",
        "spingence-ai",
        "facebook.com",
        "smasoft-tech.com",
        "aka.ms",
    ]
    for element in body.children:
        try:
            if element.attrs.get('id') == 'ms-outlook-mobile-signature':
                continue
            # get all the urls in the element
            for child in element.children:
                if child.name in ["br",'hr','table']:
                    continue
                
                if child.name != "a":
                    text_list.append(child.get_text().strip())
        except AttributeError:
            pass
    urls = [a['href'] for a in body.find_all('a') if a.has_attr('href')]
    urls = [url for url in urls if not any(domain in url for domain in ignore_domains)]
    urls = list(set(urls))
    return "\n".join(text_list), urls

def parse_html(html_content):
    """
    Parse HTML content and extract text using BeautifulSoup.

    :param html_content: The raw HTML content as a string.
    :return: Extracted text from the HTML.
    """
    # Create a BeautifulSoup object
    soup = BeautifulSoup(html_content, "html.parser")
    # remove all tables
    for table in soup.find_all("table"):
        table.decompose()
    # Extract text from the parsed HTML
    extracted_text = soup.get_text().strip()

    return extracted_text


def parse_subject(subject: str) -> Tuple[str, str]:
    """
    parse email subject to get category and assistant
    [category-assistant]=>category,assistant
    """
    # re extract content between [] and parse - to get category and assistant
    parsed_title = re.findall(r"\[(.*?)\]", subject)
    if len(parsed_title) > 0:
        parsed_result = parsed_title[0].split("-")
        if len(parsed_result) > 0:
            category = parsed_result[0]
            assistant = parsed_result[1]
            return category, assistant
    raise ValueError(f"Failed to parse subject: {subject}")
