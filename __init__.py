##
# @author Xin Li <helloimlixin@gmail.com>
# @file Description simple flask web application to switch crawling modes.
# @desc Created on 2020-05-09 5:52:32 am
# @copyright Xin Li
#
import time
import zipfile
from multiprocessing.pool import ThreadPool

from flask import Flask, render_template, request, send_from_directory, jsonify, send_file, flash, redirect, url_for

from ScrapingUtils import export_excel
from config import urls
from keyword_alert import keyword_alert_utils, flatten_list
from topic_scraper import topic_scraper_utils, weibo_login
import os
import pandas as pd
import secrets
import socket
from selenium.webdriver.remote.command import Command
import http.client
from urllib3 import exceptions
from datetime import datetime
import email_sender

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

topic = ""
keywords = None
driver = None
qr_code_src = ""

MY_ADDRESS = "helloimlixin@outlook.com"
PASSWORD = "AndrewLee_94"


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    global driver, qr_code_src
    if driver is not None and get_status(driver) == 'Alive':
        print("DEBUG: driver is still alive, killing...")
        driver.quit()
    print('Performing login procedure ====>')
    driver, qr_code_src = weibo_login(True)
    print(qr_code_src)
    return '''
    <html>
        <head>
            <link href="static/main.css" rel="stylesheet" media="all">
            <title>扫码登陆</title>
        </head>
        <body>
            <p align="center">
                <h1 style="color:#454545;" align="center">请扫描下方二维码进入爬虫系统 &#128526;</h1>
                <p align="center">
                    <img src=%s alt="QR Code">
                    <p align="center">
                        <a href=home><button>扫码完成</button></a>
                    </p>
                </p>
            </p>
        </body>
    </html>
    ''' % qr_code_src


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/download', methods=['GET', 'POST'])
def download_file():
    root = '/Users/xinli/Desktop/weibohot/generated/'
    path = '/Users/xinli/Desktop/weibohot/generated/'

    for directory in os.listdir(root):
        if directory[:len(topic)] == topic and directory[:-4] != '.zip':
            path += directory + '.zip'
            zipped = zipfile.ZipFile(root + directory + '.zip', 'w', zipfile.ZIP_DEFLATED)
            for folder, dirs, files in os.walk(root + directory):
                for file in files:
                    zipped.write(os.path.join(folder, file), arcname=file)

            zipped.close()

    return send_file(path, as_attachment=True)


'''
Weibo Data Fetching System
'''


@app.route('/crawler', methods=['GET', 'POST'])
def crawler():
    print("Crawler rendered :)")
    if request.method == 'POST':
        if driver is None:
            print('DEBUG: No driver exists, go back to home page.')
            return jsonify({"redirect": "/"})
        if request.data.decode('utf-8') == 'stop':
            print("Program execution interrupted, driver closed.")
            driver.quit()
            return jsonify({"redirect": "/"})
        # Check if driver is alive.
        if get_status(driver) == 'Dead':
            print('DEBUG: Driver is dead, return to home page to login.')
            return jsonify({"redirect": "/"})
        # Get topic
        print(request.form)
        global topic
        topic = '#' + request.form['topic'] + '#'
        if len(topic) == 2:
            print("DEBUG: topic is required.")
            flash("Topic is required.")
            return render_template('home.html')
        print(topic)

        # Get time interval for topic scraper.
        all_time_topic = request.form.get('all-time') == 'on'
        start_datetime_topic = request.form['starttime-topic']
        end_datetime_topic = request.form['endtime-topic']
        if not all_time_topic and len(start_datetime_topic) != 0 and len(end_datetime_topic) != 0:
            time_interval_topic = [
                time_format_converter(start_datetime_topic),
                time_format_converter(end_datetime_topic)]
            print(time_interval_topic)
        elif all_time_topic:
            time_interval_topic = ['all']
            print('DEBUG: All time interval is selected.')
        elif len(end_datetime_topic) == 0:
            print('DEBUG: End time is required:(')
            flash("End time is required.")
            return render_template('home.html')
        elif len(start_datetime_topic) == 0:
            print('DEBUG: Start time is required:(')
            flash("Start time is required.")
            return render_template('home.html')

        # Get selected vip categories.
        big = request.form.get('big') == 'on'
        blue = request.form.get('blue') == 'on'
        yellow = request.form.get('yellow') == 'on'
        gold = request.form.get('gold') == 'on'
        normal = request.form.get('normal') == 'on'
        selected_vip_categories = selected_vip(big, blue, yellow, gold, normal)

        if not (big or blue or yellow or gold or normal):
            print("DEBUG: At least one account category is required:(")
            flash("At least one account category is required:(")
            return render_template('home.html')

        # Determine if screenshots are required.
        yes_screenshot = request.form.get('yes-screenshot') == 'on'
        if yes_screenshot:
            print('DEBUG: screenshot required.')

        topic_scraper_utils(driver, qr_code_src, topic, selected_vip_categories, time_interval_topic, yes_screenshot)

        return jsonify(result='Success:)')

    return render_template('home.html')


@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
    print('Monitor rendered :)')
    if request.method == 'POST':
        if driver is None:
            print('DEBUG: No driver exists, go back to home page.')
            return jsonify({"redirect": "/"})
        if request.data.decode('utf-8') == 'halt':
            print("Program execution interrupted, driver closed.")
            driver.quit()
            return jsonify({"redirect": "/"})
        # Check if driver is alive.
        if get_status(driver) == 'Dead':
            print('DEBUG: Driver is dead, return to home page to login.')
            return jsonify({"redirect": "/"})
        # Get topic
        print(request.form)
        global keywords
        keywords = request.form['keywords'].split(', ')
        if keywords is None or len(keywords) == 0:
            print("DEBUG: Keywords are required.")
            flash("Keywords are required.")
            return render_template('home.html')
        print(keywords)

        # Get time interval for keyword monitor.
        start_datetime_keywords = request.form['starttime-keywords']
        end_datetime_keywords = request.form['endtime-keywords']
        if len(start_datetime_keywords) != 0 and len(end_datetime_keywords) != 0:
            time_interval_keywords = [
                time_format_converter(start_datetime_keywords),
                time_format_converter(end_datetime_keywords)]
            print(time_interval_keywords)
        else:
            return render_template('home.html')

        # Get alert contact for keyword monitor.
        alert_contacts = request.form['alert-contacts'].split(', ')
        print(alert_contacts)

        keywords_str = ''
        for keyword in keywords:
            keywords_str += keyword
        dir_name = keywords_str
        try:
            os.mkdir(dir_name)
            print('Directory', dir_name, 'created.')
        except FileExistsError:
            print('Directory', dir_name, 'already exists.')
        excel_path = dir_name + '/' + 'keyword_alert.xlsx'
        current_time = datetime.now().month + '月' + datetime.now().day + '日 ' + datetime.now().hour + '时' + \
                       datetime.now().minute + '分'
        while time_interval_keywords[0] <= current_time <= time_interval_keywords[1]:
            for key in urls:
                urls[key]['keywords'] = keywords
                urls[key]['driver'] = driver
            pool = ThreadPool(8)
            result = pool.map(keyword_alert_utils, urls)
            pool.close()
            pool.join()
            result_list = flatten_list(result)
            for result in result_list:
                for email in alert_contacts:
                    email_sender.send_email(email, result, MY_ADDRESS, PASSWORD)
            if result_list:
                if os.path.exists(excel_path):
                    original_df = pd.read_excel(excel_path, columns=['话题词', '关键词', '排名', '榜单'])
                    new_df = pd.DataFrame(result_list, columns=['话题词', '关键词', '排名', '榜单'])
                    result_df = pd.concat(
                        [original_df, new_df]).drop_duplicates(subset=['话题词', '关键词', '排名', '榜单'],
                                                               keep='last').reset_index(drop=True)
                    export_excel(result_list, result_df, excel_path)
                else:
                    result_df = pd.DataFrame(result_list)
                    export_excel(result_list, result_df, excel_path)
            else:
                print('Nothing here.')
            time.sleep(60 * 5)

    return jsonify(result='Success.')


def selected_vip(big, blue, yellow, gold, normal):
    if big:
        print('DEBUG: Big selected.')
        return ['蓝V', '黄V', '金V']
    else:
        selected_vip_categories = []
        if blue:
            selected_vip_categories.append('蓝V')
            print('DEBUG: Blue selected.')
        if yellow:
            selected_vip_categories.append('黄V')
            print('DEBUG: yellow selected.')
        if gold:
            selected_vip_categories.append('金V')
            print('DEBUG: gold selected.')
        if normal:
            selected_vip_categories.append('普通')
            print('DEBUG: normal selected.')

        return selected_vip_categories


def export2Excel(topic_info, topic_df, excel_path):
    topic_df.columns = ['话题词', '关键词', '排名', '榜单']
    writer = pd.ExcelWriter(excel_path)
    topic_df.to_excel(writer, sheet_name='bonjour', index=False)
    writer.save()


def time_format_converter(time_str):
    date_list = time_str[:-5].split('-')
    time_list = time_str[-5:].split(':')
    # Get month.
    month = date_list[1]

    # Get day.
    day = date_list[2][:-1]

    # Get Hour.
    hour = time_list[0]
    minute = time_list[1]

    return month + '月' + day + '日 ' + hour + '时' + minute + '分'


def get_status(driver):
    try:
        driver.execute(Command.STATUS)
        return "Alive"
    except (socket.error, http.client.CannotSendRequest, exceptions.MaxRetryError):
        return "Dead"


if __name__ == '__main__':
    app.run()
