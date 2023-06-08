from selenium import webdriver
from selenium.webdriver.support.events import EventFiringWebDriver
from selenium.webdriver.chrome.options import Options
import loggers.error_logger as error_logger
import loggers.result_logger as result_logger
import xpaths

import pathlib

import json

from classes.classes import runnable_dict, DriverLinkChangeListener

driver = None
scenario = {}
path = ''
date_format = ''
datetime_format = ''

def initialize():
    global path, scenario
    path = pathlib.Path(__file__).parent.resolve()

    with open("scenario.json", "r") as f:
        scenario = json.load(f,object_hook=runnable_dict)

    save_formats(scenario)

    xpaths.load()

    driver = run_driver()
    authorize(driver, scenario["auth"])

    error_logger.initialize()
    result_logger.initialize()

    return scenario, driver

def save_formats(scenario):
    global date_format, datetime_format
    date_format = scenario.get('date_format', "%d-%m-%Y")
    datetime_format = scenario.get('datetime_format', "%d-%m-%Y %H:%M")

def run_driver():
    global driver, path
    options = Options()
    options.add_argument("window-size=1920x1080")
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 1, 
        "profile.default_content_setting_values.media_stream_camera": 1
    })

    # using Chrome driver from ./drivers folder
    # TODO: add exception SessionNotCreatedException here if the chrome is outdated 
    b = webdriver.Chrome(chrome_options=options, executable_path=str(path)+'/drivers/chromedriver.exe')
    b.implicitly_wait(1) # amount of time the driver should wait when searching for an element before throwing an exception 
    b.set_window_position(2000, 0) # TODO: delete. Or change into json settings
    b.maximize_window()

    driver = EventFiringWebDriver(b, DriverLinkChangeListener())

    return driver

def authorize(driver, credentials):
    try:
        # get variables from config file
        user = str(credentials['user']) # TODO: why str? doc
        password = str(credentials['pass'])
        url = str(credentials['url'])
    except KeyError:
        error_logger.log('launching', 'Authorization', 'no credentials provided')
        raise

    # login the site using these credentials
    login_url = f'https://{user}:{password}@{url}'
    driver.get(login_url) # TODO: try-catch if incorrect login

    return driver

