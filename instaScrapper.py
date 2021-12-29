from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import time
import re
from urllib.request import urlopen
import json
from pandas import json_normalize
import pandas as pd
import numpy as np
import glob
import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# how many pages to scrape
# n_pages = 1
N_PAGES = int(os.getenv('N_PAGES'))

# hashtag / user
# mode = 'hashtag'
# mode = 'user'
MODE = os.getenv('MODE')

# list of hashtags / usernames
# name_list = ['tattoodesign']
# name_list = ['josediazvp666']
NAME_LIST = [os.getenv('NAME_LIST')]

# save info each ... (in case of bad connection or some error during scrapping better do not wait till last /
# also easier to stop script if you want without loosing all data)
# save_after = 100
SAVE_AFTER = int(os.getenv('SAVE_AFTER'))

def set_chrome_options():
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    
    return chrome_options

def print_out(prefix, msg):
    print("================\n{} {}\n================".format(prefix, msg))

def login_browser():
    browser.implicitly_wait(1)

    browser.get('https://www.instagram.com/')

    time.sleep(5)

    browser.save_screenshot("_screen_shots/login_page.png")

    username_input = browser.find_element(By.XPATH, "//input[@name='username']")
    password_input = browser.find_element(By.XPATH, "//input[@name='password']")

    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)

    login_button = browser.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()

    time.sleep(2)

    browser.save_screenshot("_screen_shots/after_login_page.png")

    # time.sleep(9999999)


def login_get_info_browser():
    get_info_browser.implicitly_wait(1)

    get_info_browser.get('https://www.instagram.com/')

    time.sleep(5)

    get_info_browser.save_screenshot("_screen_shots/login_get_info_browser.png")

    username_input = get_info_browser.find_element(By.XPATH, "//input[@name='username']")
    password_input = get_info_browser.find_element(By.XPATH, "//input[@name='password']")

    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)

    login_button = get_info_browser.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()

    time.sleep(2)

    get_info_browser.save_screenshot("_screen_shots/after_login_get_info_browser.png")

def scrollPage(n_pages=1):
    print("PAGE: 0")

    time.sleep(1)

    browser.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )

    source = browser.page_source
    data = bs(source, 'html.parser')
    body = data.find('body')
    
    for link in body.findAll('a'):
        href = link.get('href')

        if re.match("/p", href):
            print('https://www.instagram.com'+href)
            links.append('https://www.instagram.com'+href)

    time.sleep(1)

    if n_pages > 1:
        for i in range(n_pages-1):
            print("PAGE: {}".format(i+1))

            browser.execute_script(
                "window.scrollTo(document.body.scrollHeight/2, document.body.scrollHeight);"
            )

            browser.save_screenshot("_screen_shots/page_{}.png".format(i+1))

            source = browser.page_source
            data = bs(source, 'html.parser')
            body = data.find('body')
            
            for link in body.findAll('a'):
                href = link.get('href')

                if re.match("/p", href):
                    print('https://www.instagram.com'+href)
                    links.append('https://www.instagram.com'+href)

            time.sleep(1)


def getInfo(links, name, save_after):
    # read the file with images we already parsed (use listDirectory.py to create ths file first)
    shortcodes = pd.read_csv('shortcodes.csv')

    # do not replace already existing files
    cur_file = 0
    files = glob.glob("{}/{}_*".format(directory_path, name), recursive=True)
    print("FILES with {} - {}".format(name, len(files)))
    cur_file = len(files)

    links = list(set(links))

    if len(links) > 0:
        login_get_info_browser()

        result = pd.DataFrame()

        q = 0

        for i in range(len(links)):

            # check if we alreay parsed this image
            short = [links[i].split('/')[4]]
            m = shortcodes.isin(short).any()
            cols = m.index[m].tolist()

            # if not
            if len(cols) == 0:

                try:
                    print("{}   {}".format(i, links[i]))

                    get_info_browser.get(links[i])

                    time.sleep(3)

                    page = get_info_browser.page_source
                    data = bs(page, 'html.parser')
                    body = data.find('body')

                    for script in body.find_all("script"):
                        if script.text.startswith("window.__additionalDataLoaded"):
                            raw = script.text.strip().replace("window.__additionalDataLoaded('/p/"+short[0]+"/',", '').replace(');', '')

                            break

                    print_out("Debug:", "After script strip")

                    json_data = json.loads(raw)

                    print_out("Debug:", "After JSON load")

                    print_out("json_data:", json_data)

                    posts = json_data["graphql"]
                    posts = json.dumps(posts)
                    posts = json.loads(posts)

                    x = pd.DataFrame.from_dict(
                        json_normalize(posts),
                        orient='columns'
                    )

                    x.columns = x.columns.str.replace("shortcode_media.", "")
                    result = result.append(x)
                    q += 1

                except Exception as e:
                    print(e)
                    print('     CANT PARSE IMAGE')
                    np.nan
                
                # finally:

                if q > save_after:

                    result = result.drop_duplicates(subset='shortcode')
                    result.to_csv(
                        '{}/{}_{}.csv'.format(directory_path, name, cur_file))
                    print('-' * 30)
                    print("FILE SAVED: {}_{}.csv".format(name, cur_file))
                    cur_file += 1
                    result = pd.DataFrame()
                    q = 0
            else:
                print('{}   {}  Already parsed'.format(i, links[i]))

        result = result.drop_duplicates(subset='shortcode')
        result.to_csv('{}/{}_{}.csv'.format(directory_path, name, cur_file))
        print('-' * 10)
        print("FILE SAVED: {}_{}.csv".format(name, cur_file))

        del links[:]

        get_info_browser.close()
        get_info_browser.quit()

def instaScrapper(name_list, n_pages, mode='hashtag', save_after=100):
    if mode == 'user':
        for name in name_list:
            print(' ')
            print('-' * 30)
            print("PARSING NAME: {}".format(name))
            username = name

            browser.get('https://www.instagram.com/'+username+'/?hl=en')

            browser.save_screenshot('_screen_shots/on_load.png')

            time.sleep(3)

            scrollPage(n_pages)

            print("Link length After scrollPage: {}".format(len(links)))

            getInfo(links, name, save_after)

    else:
        for name in name_list:
            print(' ')
            print('-' * 30)
            print("PARSING NAME: {}".format(name))
            hashtag = name
            browser.get('https://www.instagram.com/explore/tags/'+hashtag)

            scrollPage(n_pages)
            getInfo(links, name, save_after)

# directory where to save files with info
directory_path = '_results_files'

# path to chrome driver
opts = set_chrome_options()
# browser = webdriver.Chrome(options=opts)

ser = Service("/usr/local/bin/chromedriver")
# op = webdriver.ChromeOptions()
browser = webdriver.Chrome(service=ser, options=opts)
login_browser()

get_info_browser = webdriver.Chrome(service=ser, options=opts)
# login_get_info_browser()

links = []

print("Link length Before Start: {}".format(len(links)))

instaScrapper(NAME_LIST, N_PAGES, MODE, SAVE_AFTER)

browser.close()
browser.quit()