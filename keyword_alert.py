##
# @author Xin Li <helloimlixin@gmail.com>
# @file Python scripts to crawl the Sina Weibo hotlist and export the results into excel files.
# @desc Created on 2020-04-27 5:11:32 am
# @copyright Xin Li
#
import os
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
import time
from datetime import datetime
from config import keys, urls
from multiprocessing.pool import ThreadPool
from ScrapingUtils import create_webdriver, create_mobile_webdriver
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from PIL import Image
import io

HEADLESS = True
THRESHOLD = 4

'''
手机端热搜榜：https://m.weibo.cn/p/106003type=25&t=3&disable_hot=1&filter_type=realtimehot?jumpfrom=weibocom
手机端话题总榜：https://m.weibo.cn/p/106003type=25&t=3&disable_hot=1&filter_type=topicscene?jumpfrom=weibocom
pc话题榜：https://d.weibo.com/p/aj/proxy?api=http://contentrecommend.mobile.sina.cn/dot/dot.lua&__rnd=1591831924050
pc热门话题：https://weibo.com/u/1805682534/home?topnav=1&wvr=6
'''

MY_ADDRESS = "helloimlixin@outlook.com"
PASSWORD = "AndrewLee_94"


def monitor(url_type, url, keywords):
    """
    Parallel Process to Monitor Four Weibo Lists:
    mobile hotlist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot&title=%E7%83%AD%E6%90%9C%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscen'
    mobile topiclist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscene&title=%E8%AF%9D%E9%A2%98%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
    pc topiclist url: 'https://d.weibo.com/231650'
    pc hottopic url: 'https://d.weibo.com/'
    """
    final_dict = {}

    if url_type == 'mobile_hotlist':
        driver = create_webdriver(headless=HEADLESS)
        driver.get(url)
        time.sleep(5)
        result_soup = BeautifulSoup(driver.page_source, 'lxml')
        mobile_hotlist_elements = result_soup.select('div.card-list div.card div.card-wrap span.main-text')
        mobile_hotlist = []
        if mobile_hotlist_elements:
            for i in range(50):
                mobile_hotlist.append(mobile_hotlist_elements[i].text.strip())
            for i in range(len(mobile_hotlist)):
                mobile_hotlist_item = mobile_hotlist[i]
                for keyword in keywords:
                    if longest_common_substring(mobile_hotlist_item, keyword) >= THRESHOLD:
                        final_dict['关键词：' + keyword + ' 上榜话题：' + mobile_hotlist_item + ' 榜单：移动端热搜榜'] = i

            print('Mobile Hotlist Successfully Checked:)')
        driver.close()

    # elif url_type == 'mobile_topiclist':
    #     driver = create_webdriver(headless=HEADLESS)
    #     driver.get(url)
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     for i in range(3):
    #         driver.execute_script('window.scrollBy(0, 1000)')
    #         wait_between(0.5, 1.0)
    #     WebDriverWait(driver, 100).until(EC.presence_of_element_located(
    #         (By.CSS_SELECTOR, '#app > div:nth-child(1) > div:nth-child(1) > div:nth-child(51)')
    #     ))
    #     result_soup = BeautifulSoup(driver.page_source, 'lxml')
    #     mobile_topiclist_elements = result_soup.select('div.card div div.card-list h3')
    #     mobile_topiclist = []
    #     for element in mobile_topiclist_elements:
    #         mobile_topiclist.append(element.text.strip()[1:-1])
    #     for i in range(len(mobile_topiclist)):
    #         item = mobile_topiclist[i]
    #         for keyword in keywords:
    #             if longest_common_substring(item, keyword) > 3:
    #                 result.append([item, keyword, str(i + 1), '移动端话题榜'])

    # elif url_type == 'pc_topiclist':
    #     driver = create_webdriver(headless=HEADLESS)
    #     # For the first page.
    #     driver.get(url)
    #     WebDriverWait(driver, 100).until(EC.presence_of_element_located(
    #         (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
    #                           'a.page.next.S_txt1.S_line1 > span')
    #     ))
    #     result_soup = BeautifulSoup(driver.page_source, 'lxml')
    #     pc_topiclist_elements = result_soup.select('div.m_wrap.clearfix ul.pt_ul li.pt_li div.title a.S_txt1')
    #     pc_topiclist = []
    #     for element in pc_topiclist_elements:
    #         pc_topiclist.append(element.text.strip()[1:-1])
    #     # For the following pages.
    #     page_num = 2
    #     WebDriverWait(driver, 100).until(EC.presence_of_element_located(
    #             (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
    #                               'a.page.next.S_txt1.S_line1 > span')
    #         ))
    #     next_page_elements = driver.find_elements_by_css_selector('#Pl_Discover_Pt6Rank__3 > div > div > '
    #                                                               'div.WB_cardpage.S_line1 > div > '
    #                                                               'a.page.next.S_txt1.S_line1 > span')
    #     while next_page_elements and len(pc_topiclist) < 50:
    #         next_page_elements[0].click()
    #         wait_between(0.5, 1.0)
    #         WebDriverWait(driver, 100).until(EC.presence_of_element_located(
    #             (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
    #                               'a.page.next.S_txt1.S_line1 > span')
    #         ))
    #         result_soup = BeautifulSoup(driver.page_source, 'lxml')
    #         pc_topiclist_elements = result_soup.select('div.m_wrap.clearfix ul.pt_ul li.pt_li div.title a.S_txt1')
    #         for element in pc_topiclist_elements:
    #             pc_topiclist.append(element.text.strip()[1:-1])
    #         WebDriverWait(driver, 100).until(EC.presence_of_element_located(
    #             (By.CSS_SELECTOR, '#Pl_Discover_Pt6Rank__3 > div > div > div.WB_cardpage.S_line1 > div > '
    #                               'a.page.next.S_txt1.S_line1 > span')
    #         ))
    #         next_page_elements = driver.find_elements_by_css_selector('#Pl_Discover_Pt6Rank__3 > div > div > '
    #                                                                   'div.WB_cardpage.S_line1 > div > '
    #                                                                   'a.page.next.S_txt1.S_line1 > span')
    #         page_num += 1
    #         wait_between(0.5, 1.0)
    #
    #     for i in range(len(pc_topiclist)):
    #         item = pc_topiclist[i]
    #         for keyword in keywords:
    #             if longest_common_substring(item, keyword) > 3:
    #                 result.append([item, keyword, str(i + 1), 'pc端话题榜'])
    #
    # elif url_type == 'pc_hottopic':
    #     driver = create_webdriver(headless=HEADLESS)
    #     driver.get(url)
    #     WebDriverWait(driver, 1000).until(EC.presence_of_element_located(
    #         (By.CSS_SELECTOR, '#pl_unlogin_home_hots > div:nth-child(1)')
    #     ))
    #     result_soup = BeautifulSoup(driver.page_source, 'lxml')
    #     pc_hottopic_elements = result_soup.select('div.WB_main_r div.UG_contents div.UG_list_c h3.list_title_s a.S_txt1')
    #     pc_hottopic = []
    #     for element in pc_hottopic_elements:
    #         pc_hottopic.append(element.text.strip()[1:-1])

    # for i in range(len(pc_hottopic)):
    #     item = pc_hottopic[i]
    #     for keyword in keywords:
    #         if longest_common_substring(item, keyword) > 3:
    #             result.append([item, keyword, str(i + 1), 'pc端热门话题'])

    return final_dict


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


def path_generator(path):
    now_time = time.strftime("%m-%d %H-%M", time.localtime(time.time()))
    now_time_day = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    now_time_hour = time.strftime("%H", time.localtime(time.time()))
    now_time_time = time.strftime("%H%M", time.localtime(time.time()))

    path = r'{}/{}/{}:00'.format(path, now_time_day, now_time_hour)
    exists = os.path.exists(path)
    if not exists:
        os.makedirs(path)
    path = '{}/weibo_hot_{}.xlsx'.format(path, now_time_time)
    return path, now_time


'''
mobile hotlist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot&title=%E7%83%AD%E6%90%9C%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscen'
mobile topiclist url: 'https://m.weibo.cn/p/index?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicscene&title=%E8%AF%9D%E9%A2%98%E6%A6%9C&extparam=lon%3D%26lat%3D&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
pc topiclist url: 'https://d.weibo.com/231650'
pc hottopic url: 'https://d.weibo.com/'
'''


def keyword_alert_utils(url_type):
    url = urls[url_type]['url']
    keywords = urls[url_type]['keywords']
    try:
        return monitor(url_type, url, keywords)
    except TimeoutException:
        print('Timeout Exception occurred at time:', datetime.now().strftime('%H:%M:%S'))
        return monitor(url_type, url, keywords, keys['user1'])


def flatten_dict(nested_dicts):
    flattened = {}
    for nested_dict in nested_dicts:
        for nested_dict_key, nested_dict_value in nested_dict.items():
            flattened[nested_dict_key] = nested_dict_value
    return flattened


def parallel_crawler(keywords, urls):
    for url in urls:
        urls[url]['keywords'] = keywords
    pool = ThreadPool(8)
    final_result_dict = pool.map(keyword_alert_utils, urls)
    pool.close()
    pool.join()
    return flatten_dict(final_result_dict)


def send_mail(receiver_email, mail_content, mail_imgs, from_address, sender):
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = receiver_email
    msg['Subject'] = "关键词上榜提醒"
    msg.attach(MIMEText(mail_content, 'plain'))
    for mail_img in mail_imgs:
        msg.attach(mail_img)
    sender.send_message(msg)
    del msg

    return sender


def email_login(from_address, password):
    sender = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    sender.starttls()
    sender.login(from_address, password)

    return sender
