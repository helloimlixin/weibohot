import requests
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
import time

headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1"
        }

url = "https://i.snssdk.com/feoffline/hot_list/template/hot_list/?client_extra_params=%7B%22custom_log_pb%22%3A%22%7B%5C%22cluster_type%5C%22%3A%5C%220%5C%22%2C%5C%22entrance_hotspot%5C%22%3A%5C%22search%5C%22%2C%5C%22hide_hot_board_card%5C%22%3A%5C%221%5C%22%2C%5C%22hot_board_cluster_id%5C%22%3A%5C%226857776172588237326%5C%22%2C%5C%22location%5C%22%3A%5C%22hot_board%5C%22%2C%5C%22rank%5C%22%3A%5C%2250%5C%22%2C%5C%22source%5C%22%3A%5C%22trending_tab%5C%22%2C%5C%22style_id%5C%22%3A%5C%2240128%5C%22%7D%22%7D&count=50&extra=%7B%22CardStyle%22%3A0%2C%22JumpToWebList%22%3Atrue%7D&fe_api_version=2&log_pb=%7B%22cluster_type%22%3A%220%22%2C%22entrance_hotspot%22%3A%22search%22%2C%22hide_hot_board_card%22%3A%221%22%2C%22hot_board_cluster_id%22%3A%226857776172588237326%22%2C%22location%22%3A%22hot_board%22%2C%22rank%22%3A%2250%22%2C%22source%22%3A%22trending_tab%22%2C%22style_id%22%3A%2240128%22%7D&stream_api_version=88&style_type=18&tab_name=stream"

def create_webdriver(headless=False):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    if headless == True:
        options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}
    capabilities['pageLoadStrategy'] = "none"
    driver = webdriver.Chrome(options=options, executable_path="./chromedriver", desired_capabilities=capabilities)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': """Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
                """
    })
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd(
        'Network.setExtraHTTPHeaders', {'headers': {'User-Agent': 'browser1'}})

    return driver

driver = create_webdriver(headless=True)
driver.get(url)
time.sleep(5)

soup = BeautifulSoup(driver.page_source, 'html.parser')
card_titles = soup.select('div.hot-list div.card-title')
for card_title in card_titles:
    print(card_title.text)
driver.close()
