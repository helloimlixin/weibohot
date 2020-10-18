import time
import random
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
import pandas as pd
from bs4 import BeautifulSoup
import requests
import os


def timeme(function):
    """Helper annotation function for performance measure.

    Contains a wrapper function that computes method runtime by seconds.

    Args:
        function: function to annotate for time measure.

    Returns:
        wrapper: a wrapper function for time measure.
    """

    def wrapper(*args, **kwargs):
        """Wrapper function to compute function runtime.

        Uses time library.

        Args:
            *args: non-keyworded variable length argument list passed to the
            wrapper function.
            **kwargs: keyworded variable length argument list passed to the
            wrapper function.

        Returns:
            result: execution time in seconds.
        """
        start_time = int(round(time.time() * 1000))
        result = function(*args, **kwargs)
        end_time = int(round(time.time() * 1000))
        print("Execution time: {}".format((end_time - start_time) / 1000))
        return result

    return wrapper


def wait_between(low, high):
    """Helper function to wait for random time interval to simulate a human waiting.

    Waits for a random time interval under a uniform distribution.

    Args:
        low: interval lower bound.
        high: interval upper bound.
    """
    random_seconds = random.uniform(low, high)
    time.sleep(random_seconds)


def create_webdriver(headless=False):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}
    capabilities['pageLoadStrategy'] = "none"
    driver = webdriver.Chrome(options=options,
                              executable_path='/Users/xinli/Desktop/weibohot/chromedriver',
                              desired_capabilities=capabilities)
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


def export_excel(topic_info, topic_df, excel_path, columns, post_screenshot):
    topic_df.columns = columns
    writer = pd.ExcelWriter(excel_path)
    topic_df.to_excel(writer, sheet_name='bonjour', index=False)
    workbook = writer.book
    worksheet = writer.sheets['bonjour']
    if post_screenshot:
        for i, row in enumerate(topic_info):
            worksheet.write_url('G' + str(i + 2), r'external:' + row[6])
    workbook.close()
    writer.save()


def get_fan_data(nickname):
    """Get fan count for Weibo User.

    Args:
        nickname (str): Weibo User nickname
    """
    search_url = f'http://s.weibo.com/user?q={nickname}&Refer=SUer_box'
    response = requests.get(search_url)
    page_str = BeautifulSoup(response.text, 'lxml').get_text()
    fans_count_field_idx = page_str.find('粉丝')

    while not page_str[fans_count_field_idx + 2].isdigit():
        # print(page_str[0:5])
        page_str = page_str[fans_count_field_idx + 2:]
        fans_count_field_idx = page_str.find('粉丝')

    fans_count_len = page_str[fans_count_field_idx:].find('\n')
    fans_count = page_str[fans_count_field_idx + 2: fans_count_field_idx + fans_count_len]
    if fans_count.find('万') != -1:
        fans_count = fans_count[:fans_count.find('万')] + '00000'

    return fans_count
