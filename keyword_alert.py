##
# @author Xin Li <helloimlixin@gmail.com>
# @file Python scripts to crawl the Sina Weibo hotlist and export the results into excel files.
# @desc Created on 2020-04-27 5:11:32 am
# @copyright Xin Li
#
import os
import time
import requests
from bs4 import BeautifulSoup
from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
import random
from config import keys, urls
from multiprocessing.pool import ThreadPool
import http.client
from urllib import parse
import json
from email_sender import send_mail

HEADLESS = False

'''
手机端热搜榜：https://m.weibo.cn/p/106003type=25&t=3&disable_hot=1&filter_type=realtimehot?jumpfrom=weibocom
手机端话题总榜：https://m.weibo.cn/p/106003type=25&t=3&disable_hot=1&filter_type=topicscene?jumpfrom=weibocom
pc话题榜：https://d.weibo.com/p/aj/proxy?api=http://contentrecommend.mobile.sina.cn/dot/dot.lua&__rnd=1591831924050
pc热门话题：https://weibo.com/u/1805682534/home?topnav=1&wvr=6
'''

MY_ADDRESS = "helloimlixin@outlook.com"
PASSWORD = "AndrewLee_94"


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
    if headless == True:
        options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}
    capabilities['pageLoadStrategy'] = "none"
    driver = webdriver.Chrome(options=options, executable_path='./chromedriver', desired_capabilities=capabilities)
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


def save_html_as(result_soup, filename):
    with open('intermediate_pages/' + filename, 'w') as file:
        file.write(result_soup.prettify())


'''
mobile hotlist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot&title=%E7%83%AD%E6%90%9C%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscen'
mobile topiclist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscene&title=%E8%AF%9D%E9%A2%98%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
pc topiclist url: 'https://d.weibo.com/231650'
pc hottopic url: 'https://d.weibo.com/'
'''


def spider(driver, url_type, url, keywords):
    result = []

    if url_type == 'mobile_hotlist':
        driver.get(url)
        time.sleep(5)
        result_soup = BeautifulSoup(driver.page_source, 'lxml')
        save_html_as(result_soup, url_type + '.html')
        mobile_hotlist_elements = result_soup.select('div.card-list div.card div.card-wrap span.main-text')
        mobile_hotlist = []
        for i in range(50):
            mobile_hotlist.append(mobile_hotlist_elements[i].text.strip())
        for i in range(len(mobile_hotlist)):
            item = mobile_hotlist[i]
            for keyword in keywords:
                if longest_common_substring(item, keyword) > 3:
                    if i == 0:
                        result.append([item, keyword, '置顶', '移动端热搜榜'])
                    else:
                        result.append([item, keyword, str(i), '移动端热搜榜'])

    if url_type == 'mobile_topiclist':
        driver = create_webdriver(headless=HEADLESS)
        driver.get(url)
        time.sleep(500000)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        for i in range(3):
            driver.execute_script('window.scrollBy(0, 1000)')
            wait_between(0.5, 1.0)
        WebDriverWait(driver, 100).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#app > div:nth-child(1) > div:nth-child(1) > div:nth-child(51)')
        ))
        result_soup = BeautifulSoup(driver.page_source, 'lxml')
        save_html_as(result_soup, url_type + '.html')
        mobile_topiclist_elements = result_soup.select('div.card div div.card-list h3')
        mobile_topiclist = []
        for element in mobile_topiclist_elements:
            mobile_topiclist.append(element.text.strip()[1:-1])
        for i in range(len(mobile_topiclist)):
            item = mobile_topiclist[i]
            for keyword in keywords:
                if longest_common_substring(item, keyword) > 3:
                    result.append([item, keyword, str(i + 1), '移动端话题榜'])

    elif url_type == 'pc_topiclist':
        driver = create_webdriver(headless=HEADLESS)
        # For the first page.
        driver.get(url)
        WebDriverWait(driver, 100).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
                              'a.page.next.S_txt1.S_line1 > span')
        ))
        result_soup = BeautifulSoup(driver.page_source, 'lxml')
        save_html_as(result_soup, url_type + '-1.html')
        pc_topiclist_elements = result_soup.select('div.m_wrap.clearfix ul.pt_ul li.pt_li div.title a.S_txt1')
        pc_topiclist = []
        for element in pc_topiclist_elements:
            pc_topiclist.append(element.text.strip()[1:-1])
        # For the following pages.
        page_num = 2
        WebDriverWait(driver, 100).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
                                  'a.page.next.S_txt1.S_line1 > span')
            ))
        next_page_elements = driver.find_elements_by_css_selector('#Pl_Discover_Pt6Rank__3 > div > div > '
                                                                  'div.WB_cardpage.S_line1 > div > '
                                                                  'a.page.next.S_txt1.S_line1 > span')
        while next_page_elements and len(pc_topiclist) < 50:
            next_page_elements[0].click()
            wait_between(0.5, 1.0)
            WebDriverWait(driver, 100).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
                                  'a.page.next.S_txt1.S_line1 > span')
            ))
            result_soup = BeautifulSoup(driver.page_source, 'lxml')
            save_html_as(result_soup, url_type + '-' + str(page_num) + '.html')
            pc_topiclist_elements = result_soup.select('div.m_wrap.clearfix ul.pt_ul li.pt_li div.title a.S_txt1')
            for element in pc_topiclist_elements:
                pc_topiclist.append(element.text.strip()[1:-1])
            WebDriverWait(driver, 100).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
                                  'a.page.next.S_txt1.S_line1 > span')
            ))
            next_page_elements = driver.find_elements_by_css_selector('#Pl_Discover_Pt6Rank__3 > div > div > '
                                                                      'div.WB_cardpage.S_line1 > div > '
                                                                      'a.page.next.S_txt1.S_line1 > span')
            page_num += 1
            wait_between(0.5, 1.0)

        for i in range(len(pc_topiclist)):
            item = pc_topiclist[i]
            for keyword in keywords:
                if longest_common_substring(item, keyword) > 3:
                    result.append([item, keyword, str(i + 1), 'pc端话题榜'])

    elif url_type == 'pc_hottopic':
        driver = create_webdriver(headless=HEADLESS)
        driver.get(url)
        WebDriverWait(driver, 1000).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#pl_unlogin_home_hots > div:nth-child(1)')
        ))
        result_soup = BeautifulSoup(driver.page_source, 'lxml')
        save_html_as(result_soup, url_type + '.html')
        pc_hottopic_elements = result_soup.select('div.WB_main_r div.UG_contents div.UG_list_c h3.list_title_s a.S_txt1')
        pc_hottopic = []
        for element in pc_hottopic_elements:
            pc_hottopic.append(element.text.strip()[1:-1])

    for i in range(len(pc_hottopic)):
        item = pc_hottopic[i]
        for keyword in keywords:
            if longest_common_substring(item, keyword) > 3:
                result.append([item, keyword, str(i + 1), 'pc端热门话题'])

    return result


def longest_common_substring(str1, str2):
    m = len(str1)
    n = len(str2)
    # Initialize a DP table with zeroes.
    dp = [[0 for j in range(n + 1)] for i in range(m + 1)]
    # Create a variable to store the longest length of the substring.
    result = 0

    # Fill out the DP table.
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 or j == 0:
                dp[i][j] = 0
            elif str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                result = max(result, dp[i][j])
            else:
                dp[i][j] = 0

    return result


def export_to_excel(list, path):
    dataFrame = DataFrame(list)
    current_path, current_time = path_generator(path)
    DataFrame.to_excel(dataFrame, current_path, sheet_name=current_time, index=False)
    print('Hotlist at time {} is successfully exported to excel.'.format(current_time))


def path_generator(path):
    nowTime = time.strftime("%m-%d %H-%M", time.localtime(time.time()))
    nowTime_day = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    nowTime_hour = time.strftime("%H", time.localtime(time.time()))
    nowTime_time = time.strftime("%H%M", time.localtime(time.time()))

    path = r'{}/{}/{}:00'.format(path, nowTime_day, nowTime_hour)
    isexists = os.path.exists(path)
    if not isexists:
        os.makedirs(path)
    path = '{}/weibo_hot_{}.xlsx'.format(path, nowTime_time)
    return path, nowTime


'''
mobile hotlist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot&title=%E7%83%AD%E6%90%9C%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscen'
mobile topiclist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscene&title=%E8%AF%9D%E9%A2%98%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
pc topiclist url: 'https://d.weibo.com/231650'
pc hottopic url: 'https://d.weibo.com/'
'''


def keyword_alert_utils(url_type):
    url = urls[url_type]['url']
    keywords = urls[url_type]['keywords']
    driver = urls[url_type]['driver']
    try:
        return spider(driver, url_type, url, keywords)
    except TimeoutException:
        print('Timeout Exception occurred at time:', datetime.now().strftime('%H:%M:%S'))
        return spider(url_type, url, keywords, keys['user1'])


def flatten_list(nested_list):
    flattened = []
    for list in nested_list:
        for item in list:
            flattened.append(item)
    return flattened


def parallel_crawler():
    # weibo_hotlist = keyword_alert_utils(keys, urls)
    keywords = ['美国暴乱', '钟南山院士', '哥伦布雕像', '最丑夏日穿搭', '理科生才懂', '垃圾分类', '布隆迪总统']
    for key in urls:
        urls[key]['keywords'] = keywords
    pool = ThreadPool(8)
    result = pool.map(keyword_alert_utils, urls)
    pool.close()
    pool.join()
    return flatten_list(result)


if __name__ == '__main__':
    while True:
        result_list = parallel_crawler()
        for item in result_list:
            print(item)
        time.sleep(60 * 5)
