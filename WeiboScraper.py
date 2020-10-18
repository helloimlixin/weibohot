import time
from ScrapingUtils import create_webdriver, wait_between
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

class WeiboScraper:
    """Utility class to scrape Weibo.
    """

    DEFAULT_TIMEOUT = 1000
    
    def __init__(self, username, password, headless = False):
        """Class constructor

        Args:
            username (str): Weibo username
            password (str): Weibo password
            headless (bool): headless option for webdriver
        """
        self.username = username
        self.password = password
        self.headless = False

    def render_elements(self, driver, selectors):
        for selector in selectors:
            WebDriverWait(driver, self.DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, selector)
            ))
            wait_between(1.0, 2.0)
    
    def login(self):
        """Utility method to login to the Weibo Mainland China site.
        """
        # Weibo chinese mainland version
        login_url = 'https://weibo.com/cn'
        
        # Create a Selenium Webdriver for advanced scrapping
        # with headless option preconfigured during class instantiation.
        driver = create_webdriver(headless=self.headless)

        # Retrieve URL and render.
        driver.get(login_url)
        username_field_selector = '#loginname'
        password_field_selector = '#pl_login_form > div > div:nth-child(3) > div.info_list.password > div > input'
        login_btn_selector = '#pl_login_form > div > div:nth-child(3) > div.info_list.login_btn > a'
        self.render_elements(driver, [
            username_field_selector,
            password_field_selector,
            login_btn_selector])
        wait_between(2.0, 3.0)
        print('DEBUG: Web page successfully rendered:)')

        # Fill in the login form and submit.
        driver.find_element_by_css_selector(
            username_field_selector).send_keys(self.username)
        wait_between(1.5, 2.0)
        driver.find_element_by_css_selector(
            password_field_selector).send_keys(self.password)
        wait_between(2.0, 3.5)
        driver.find_element_by_css_selector(login_btn_selector).click()
        print('DEBUG: User info entered, proceeding log in.')

        # Perform user account validation.
        sms_code_btn_selector = '#message_sms_login'
        WebDriverWait(driver, self.DEFAULT_TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, sms_code_btn_selector)
        ))
        wait_between(1.0, 2.0)
        driver.find_element_by_css_selector(sms_code_btn_selector).click()
        sms_code_confirm_btn_selector = '#message_confirm'
        WebDriverWait(driver, self.DEFAULT_TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, sms_code_confirm_btn_selector)
        ))
        sms_code = input("Please enter a string:\n")
        
        for i in range(6):
            sms_code_block = driver.find_element_by_css_selector(f'#message_content > div > div.num.clearfix > input[type=text]:nth-child({i + 1})')
            sms_code_block.send_keys(sms_code[i])
            wait_between(0.0, 0.5)
        driver.find_element_by_css_selector(sms_code_confirm_btn_selector).click()

