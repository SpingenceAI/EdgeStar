from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from markdownify import markdownify as md
from bs4 import BeautifulSoup


# Set up the remote WebDriver
def create_webdriver():
    """Create a webdriver instance"""
    selenium_url = "http://localhost:4444/wd/hub"  # Docker container URL)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Remote(command_executor=selenium_url, options=chrome_options)
    return driver


def scrape(url: str) -> str:
    """Scrape the url and return the html content from webpage"""
    driver = create_webdriver()
    try:
        driver.get(url)  # Replace with your target URL
        html = driver.page_source
        return html
    finally:
        driver.quit()


def parse_html(html: str) -> str:
    """Parse the html content and return the body text or markdown"""
    content = BeautifulSoup(html, "html.parser")
    body = content.find("body").prettify()
    return md(body)


def scrape_body(url: str) -> str:
    """Get the body markdown from the url"""
    html = scrape(url)
    return parse_html(html)

def scrape_url(url: str) -> tuple[str, str, str]:
    """Get the html and body markdown from the url"""
    html = scrape(url)
    content = BeautifulSoup(html, "html.parser")
    body = content.find("body").prettify()
    body_markdown = md(body)
    body_text = content.get_text()
    return html, body_markdown, body_text
