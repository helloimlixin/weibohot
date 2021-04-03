##
# @author Xin Li <helloimlixin@gmail.com>
# @file Description: scrapping utility for weibo topics
# @desc Created on 2020-05-19 8:23:30 am
# @copyright Xin Li
#
import http

from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.remote.command import Command
from urllib3 import exceptions
from ScrapingUtils import timeme, wait_between, create_webdriver, export_excel, get_fan_data
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from PIL import Image
from io import BytesIO
import os
import glob
from datetime import datetime, timedelta
import socket

TOPIC = "#学历歧视背后的经济学原理#"
VIP_CATEGORIES = ["蓝V", "黄V", "金V", "会员", "达人", "正常"]
SELECTED_VIP_CATEGORIES = ["蓝V", "黄V", '金V']
icon_dict = {"icon-vip-b": "蓝V", "icon-vip-y": "黄V", "icon-vip-g": "金V", "icon-member": "会员", "icon-daren": "达人",
             "": "普通"}
TIME_INTERVAL = ["09月18日", "09月22日"]


def scrape_data(i, driver, card_element, card_headers, nick_name, post_time, vip_type, line_list, shares, comments,
                likes, post_screenshot, link, time_of_posts, screenshot_count, output_dir):
    line_list.append(nick_name)
    line_list.append(post_time)
    line_list.append(vip_type)
    if len(shares) > 3:
        line_list.append(shares[3:])
    else:
        line_list.append('0')
    if len(comments) > 3:
        line_list.append(comments[3:])
    else:
        line_list.append('0')
    if len(likes) > 0:
        line_list.append(likes)
    else:
        line_list.append('0')

    '''
    Add Screenshot.
    '''
    if post_screenshot:
        # Save post screenshot.
        location = card_element.location_once_scrolled_into_view
        size = card_element.size
        driver.execute_script("window.scrollBy(0, arguments[0]);", -70)
        page_screenshot = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(page_screenshot))
        screensize = (driver.execute_script("return document.body.clientWidth"),
                      # Get size of the part of the screen visible in the screenshot
                      driver.execute_script("return window.innerHeight"))
        img = img.resize(screensize)  # resize so coordinates in png correspond to coordinates on webpage

        left = location['x']
        top = location['y'] + 70
        if i == len(card_headers) - 1:
            top += 50
        right = left + int(size['width'])
        bottom = top + int(size['height'])
        img = img.crop((left, top, right, bottom))  # defines crop points
        img_identifier = 'images/' + nick_name.strip() + ' ' + vip_type.strip() + ' ' + post_time.strip()
        img_list = glob.glob(output_dir + 'images/*.png')
        if not exists_img(img_identifier, img_list):
            img_filename = img_identifier + '.png'
            img_path = output_dir + img_filename
            img.save(img_path)  # saves new cropped image
            line_list.append(img_filename)
            screenshot_count += 1
        else:
            img_filename = img_identifier + '.png'
            line_list.append(img_filename)

    line_list.append('=HYPERLINK("' + link + '", "打开用户链接")')
    post_link = 'http:' + time_of_posts[i].select('a')[0]['href'].strip()
    print('DEBUG:', post_link)
    line_list.append('=HYPERLINK("' + post_link + '", "打开讨论链接")')

    num_followers = get_fan_data(nick_name)
    for _ in range(10):
        if len(num_followers) > 10:
            num_followers = get_fan_data(nick_name)
        else:
            break
    line_list.append(num_followers)

    return line_list, driver, screenshot_count


def topic_info_fetcher(driver, page_source, output_dir, selected_vip_categories, time_interval, screenshot, initial_cnt):
    WebDriverWait(driver, 100).until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, '#pl_feedlist_index > div:nth-child(1)')
    ))
    # Parse the HTML with BeautifulSoup and create a soup object.
    soup = BeautifulSoup(page_source, 'html.parser')

    card_list = soup.select('#pl_feedlist_index > div:nth-child(1)')[0]
    card_headers = card_list.select('div.card-wrap div.card div.card-feed')
    card_elements = driver.find_elements_by_css_selector('div.card-wrap')
    card_actions = card_list.select('div.card-act ul li a')

    time_of_posts = card_list.select('div.card-feed div.content p.from')
    topic_info_list = []
    screenshot_count = initial_cnt

    for i in range(len(card_headers)):
        line_list = []
        card_header = card_headers[i]
        card_element = card_elements[i]
        # card = card_list.select('div.card div.content div.info ul')[i]
        tag = ''
        vip_category = ''
        if card_header.select('div.content div.info div a i.icon-vip'):
            vip_category += card_header.select('div.content div.info div a i.icon-vip')[0]['class'][1]
        if vip_category != '':
            tag += vip_category.strip()

        if icon_dict[tag] in selected_vip_categories:
            '''
            Get the required information.
            '''
            post_time = date_extractor(time_of_posts[i].text.strip()[:12])
            nick_name = card_header.select('p.txt')[0]['nick-name']
            vip_type = icon_dict[tag]
            link = 'http:' + card_header.select('div.info div a.name')[0]['href'].strip()
            shares = card_actions[i * 4 + 1].text.strip()
            comments = card_actions[i * 4 + 2].text.strip()
            likes = card_actions[i * 4 + 3].text.strip()

            if len(time_interval) == 1:
                line_list, driver, screenshot_count = scrape_data(
                    i, driver, card_element, card_headers, nick_name, post_time,
                    vip_type, line_list, shares, comments, likes, screenshot, link,
                    time_of_posts, screenshot_count, output_dir)
            elif time_interval[0] <= post_time <= time_interval[1]:
                line_list, driver, screenshot_count = scrape_data(
                    i, driver, card_element, card_headers, nick_name, post_time,
                    vip_type, line_list, shares, comments, likes, screenshot, link,
                    time_of_posts, screenshot_count, output_dir)

        if len(line_list) > 0:
            topic_info_list.append(line_list)

        if get_status(driver) == 'Dead':
            print('Driver is dead, saving topic info...')
            return topic_info_list, screenshot_count

    return topic_info_list, screenshot_count


def exists_img(img_identifier, img_list):
    for img_name in img_list:
        if img_identifier in img_name:
            return True
    return False


def date_extractor(post_time):
    raw_date = str(datetime.date(datetime.now()))
    current_date = raw_date[-5:-3] + '月' + raw_date[-2:] + '日'
    colon_idx = post_time.find(':')
    if '今天' in post_time:
        post_time = post_time.replace('今天', current_date)[:6] + ' ' + post_time[colon_idx - 2:colon_idx] + '时' \
                    + post_time[colon_idx + 1: colon_idx + 3] + '分'
    elif '今天' not in post_time and '月' not in post_time and ':' in post_time:
        post_time = current_date + ' ' + post_time[colon_idx - 2:colon_idx] + '时' \
                    + post_time[colon_idx + 1: colon_idx + 3] + '分'
    elif ':' in post_time:
        post_time = post_time[:6] + ' ' + post_time[colon_idx - 2:colon_idx] + '时' \
                    + post_time[colon_idx + 1: colon_idx + 3] + '分'
    else:
        current_datetime = datetime.now()
        if '分钟' in post_time:
            minute_delay = int(post_time[:post_time.find('分钟')])
            post_time = current_date + ' ' + (current_datetime - timedelta(minutes=minute_delay)).time().strftime(
                '%H时%M分%S')[:-3]
        elif '秒' in post_time:
            second_delay = int(post_time[:post_time.find('秒')])
            post_time = current_date + ' ' + (current_datetime - timedelta(seconds=second_delay)).time().strftime(
                '%H时%M分%S')[:-3]

    return post_time


def locate_img(img_identifier, img_list):
    for i in range(len(img_list)):
        if img_identifier in img_list[i]:
            return i
    return -1


def weibo_login(headless):
    login_url = 'https://weibo.com/cn'
    driver = create_webdriver(headless=headless)
    driver.get(login_url)
    secure_login_btn_selector = '#pl_login_form > div > div.info_header > div > a:nth-child(2)'
    WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, secure_login_btn_selector)
    ))
    wait_between(1.0, 2.0)
    driver.find_element_by_css_selector(secure_login_btn_selector).click()
    qr_code_selector = '#pl_login_form > div > div.login_content > img'
    WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, qr_code_selector)
    ))
    qr_code_src = 'blank'
    while qr_code_src.find('blank') != -1:
        qr_code_element = driver.find_element_by_css_selector(qr_code_selector)
        qr_code_src = qr_code_element.get_attribute('src')

    print('QR Code fetched, please scan to login.')

    return driver, qr_code_src


@timeme
def topic_scraper_utils(driver, qr_code_src, topic, selected_vip_categories, time_interval, post_screenshot):
    message = 'Web page successfully rendered.'
    while qr_code_src is None:
        print('Login failed: restarting Weibo login procedure.')
        driver, qr_code_src = weibo_login(False)

    print(message)

    qr_result_selector = '#pl_login_form > div > div.login_content > div.result.res_error > div > a'
    input_field_selector = '#plc_top > div > div > div.gn_search_v2 > input'

    while not driver.find_elements_by_css_selector(input_field_selector):
        if driver.find_elements_by_css_selector(qr_result_selector) and \
                driver.find_element_by_css_selector(qr_result_selector).text.strip() == '刷新页面':
            print('DEBUG: 扫码失败，刷新页面')
            wait_between(2.0, 3.0)
            driver.refresh()
            break
        wait_between(5.0, 6.0)

    WebDriverWait(driver, 1000).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, input_field_selector)
    ))
    print('DEBUG: Webpage refreshed successfully:)')
    wait_between(0.5, 1.0)
    driver.find_element_by_css_selector(input_field_selector).send_keys(topic)
    input_btn_selector = '#plc_top > div > div > div.gn_search_v2 > a'
    WebDriverWait(driver, 1000).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, input_btn_selector)
    ))
    wait_between(0.5, 1.0)
    if driver.find_elements_by_css_selector(input_btn_selector):
        driver.find_element_by_css_selector(input_btn_selector).click()
    wait_between(0.5, 1.0)
    print('DEBUG: topic name sent to weibo.')

    WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '#pl_feedlist_index > div:nth-child(1)')
    ))
    wait_between(1.0, 2.0)
    WebDriverWait(driver, 1000).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '#pl_topic_header > div.m-main-nav > ul > li:nth-child(2) > a')
    )).click()
    wait_between(2.0, 3.0)

    dir_name = '/Users/xinli/Desktop/weibohot/generated/' + topic

    for vip_category in selected_vip_categories:
        dir_name += vip_category[0].upper()
    if post_screenshot:
        dir_name += ' -- 实时榜带截图'
    image_dir = dir_name + '/images'
    global screenshot_cnt
    try:
        os.mkdir(dir_name)
        if post_screenshot:
            os.mkdir(image_dir)
        screenshot_cnt = 1
        print('Directory', dir_name, 'created.')
    except FileExistsError:
        print('Directory', dir_name, 'already exists.')
        img_list = glob.glob(dir_name + '/*.png')
        screenshot_cnt = len(img_list) + 1

    topic_info = []
    excel_path = dir_name + '/' + 'topic_info.xlsx'

    try:
        os.remove(excel_path)
    except OSError:
        pass

    # Deal with the first page.
    first_page = driver.page_source
    first_page_list, screenshot_cnt = topic_info_fetcher(driver, first_page, dir_name + '/', selected_vip_categories,
                                                         time_interval, post_screenshot, screenshot_cnt)
    for row in first_page_list:
        topic_info.append(row)

    wait_between(1.0, 2.0)
    if get_status(driver) == 'Dead' or not driver.find_elements_by_css_selector('#pl_feedlist_index > div.m-page > div > a'):
        if get_status(driver) == 'Alive':
            driver.close()
        if topic_info:
            columns = ['用户名', '时间', 'VIP类别', '转发', '评论', '点赞', '截图', '用户链接', '讨论链接', '粉丝量']
            if not post_screenshot:
                columns = ['用户名', '时间', 'VIP类别', '转发', '评论', '点赞', '用户链接', '讨论链接', '粉丝量']
            if os.path.exists(excel_path):
                original_df = pd.read_excel(excel_path, columns)
                new_df = pd.DataFrame(topic_info, columns=columns)
                topic_df = pd.concat([original_df, new_df]).drop_duplicates(subset=['用户名', '时间', '转发', '评论', '点赞'],
                                                                            keep='last').reset_index(drop=True)
                export_excel(topic_info, topic_df, excel_path, columns, post_screenshot)
            else:
                topic_df = pd.DataFrame(topic_info)
                export_excel(topic_info, topic_df, excel_path, columns, post_screenshot)
        else:
            print("Nothing here.")
        return topic_info
    WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '#pl_feedlist_index > div.m-page > div > a')
    ))
    if driver.find_elements_by_css_selector('#pl_feedlist_index > div.m-page > div > a'):
        driver.find_element_by_css_selector('#pl_feedlist_index > div.m-page > div > a').click()
    WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '#pl_feedlist_index > div.m-page > div')
    ))

    page_cnt = 2
    while driver.find_elements_by_css_selector('#pl_feedlist_index > div.m-page > div') and page_cnt < 50:
        page = driver.page_source
        page_list, screenshot_cnt = topic_info_fetcher(driver, page, dir_name + '/', selected_vip_categories,
                                                       time_interval, post_screenshot, screenshot_cnt)
        for row in page_list:
            topic_info.append(row)
        WebDriverWait(driver, 1000).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#pl_feedlist_index > div.m-page > div')
        ))
        if driver.find_elements_by_css_selector('#pl_feedlist_index > div.m-page > div > a.next'):
            driver.find_element_by_css_selector('#pl_feedlist_index > div.m-page > div > a.next').click()
        else:
            break

        wait_between(1.0, 1.5)
        page_cnt += 1
    # Make up for the final page.
    WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '#pl_feedlist_index')
    ))
    wait_between(1.0, 2.0)
    final_page = driver.page_source
    final_page_list, screenshot_cnt = topic_info_fetcher(driver, final_page, dir_name + '/',
                                                         selected_vip_categories, time_interval, post_screenshot,
                                                         screenshot_cnt)
    for row in final_page_list:
        topic_info.append(row)
    # print(topic_info)

    '''
    Write topic information into excel.
    '''
    # Check if the Excel file already exists.
    if topic_info:
        excel_path = dir_name + '/' + 'topic_info.xlsx'
        columns = ['用户名', '时间', 'VIP类别', '转发', '评论', '点赞', '截图', '用户链接', '讨论链接', '粉丝量']
        if not post_screenshot:
            columns = ['用户名', '时间', 'VIP类别', '转发', '评论', '点赞', '用户链接', '讨论链接', '粉丝量']
        if os.path.exists(excel_path):
            original_df = pd.read_excel(excel_path, columns)
            new_df = pd.DataFrame(topic_info, columns=columns)
            topic_df = pd.concat([original_df, new_df]).drop_duplicates(subset=['用户名', '时间', '转发', '评论', '点赞'],
                                                                        keep='last').reset_index(drop=True)
            export_excel(topic_info, topic_df, excel_path, columns, post_screenshot)
        else:
            topic_df = pd.DataFrame(topic_info)
            export_excel(topic_info, topic_df, excel_path, columns, post_screenshot)
    else:
        print("Nothing here.")

    print('All pages viewed.')

    driver.close()
    # wait_between(1000, 2000)

    return topic_info


def get_status(driver):
    try:
        driver.execute(Command.STATUS)
        return "Alive"
    except (socket.error, http.client.CannotSendRequest, exceptions.MaxRetryError):
        return "Dead"


if __name__ == '__main__':
    screenshot = True
    while True:
        try:
            print('Fetching topic information data...')
            driver, qr_code_src = weibo_login(False)
            topic_scraper_utils(driver, qr_code_src, TOPIC, SELECTED_VIP_CATEGORIES, TIME_INTERVAL, screenshot)
        except TimeoutException:
            print('Timeout Exception occurred, restarting...')
            topic_scraper_utils(driver, qr_code_src, TOPIC, SELECTED_VIP_CATEGORIES, TIME_INTERVAL, screenshot)
        except NoSuchElementException:
            print('NoSuchElement Exception occurred, restarting...')
            topic_scraper_utils(driver, qr_code_src, TOPIC, SELECTED_VIP_CATEGORIES, TIME_INTERVAL, screenshot)
        time.sleep(5 * 60)
