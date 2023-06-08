from typing import Iterable
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoSuchWindowException
import xpaths as x

BYs = {
        "CL": By.CLASS_NAME,
        "CS": By.CSS_SELECTOR,
        "ID": By.ID,
        "LI": By.LINK_TEXT,
        "NA": By.NAME,
        "PA": By.PARTIAL_LINK_TEXT,
        "TA": By.TAG_NAME,
        "XP": By.XPATH
    }
def get_locator(path: str):
    return BYs[path[:2]], path[4:]


# TODO: see if those three methods ever fail too soon. If they do, create a separate method
# which is going to be the 'safe' one with WebDriverWait and use it wherever the timeout needed.
def find_element(driver: WebElement, path: str, visibility_required = True) -> WebElement:
    if (visibility_required):
        return WebDriverWait(driver, timeout=3).until(
            EC.presence_of_element_located(get_locator(path))
            # EC.visibility_of(element)
        )
    else:
        return driver.find_element(*get_locator(path))
def find_elements(driver: WebElement, path: str, visibility_required = True) -> list[WebElement]:
    elements = driver.find_elements(*get_locator(path))
    if (len(elements) > 0 and visibility_required):
        try: 
            return WebDriverWait(driver, timeout=3).until( #@IgnoreException
                # EC.visibility_of(elements) # checks visibility of a single element, not a list
                EC.visibility_of_all_elements_located(get_locator(path)) # FIXME: bug sometimes on activities
            )
        except TimeoutException: 
            return [el for el in elements if el.is_displayed()]
    return elements
    # try:
    #     return WebDriverWait(driver, timeout=3).until( #@IgnoreException
    #         EC.presence_of_all_elements_located(get_locator(path))
    #     )
    # except TimeoutException:
    #     return []
def find_element_or_none(driver: WebElement, path: str) -> list[WebElement] | None:
    try:
        # return WebDriverWait(driver, timeout=3).until( #@IgnoreException
        #     EC.presence_of_element_located(get_locator(path))
        # )
        return driver.find_element(*get_locator(path)) #@IgnoreException
    except (NoSuchElementException, TimeoutException):
        return None
    
def find_element_timedout(driver: WebElement, path: str) -> WebElement:
    return WebDriverWait(driver, timeout=3).until(
        EC.presence_of_element_located(get_locator(path))
    )
    
    
def find_elements_gen(driver: WebElement, path: str) -> Iterable[WebElement]:
    while (el := find_element_or_none(driver, path)) is not None:
        yield el

class Wait(WebDriverWait):
    def untils(self, methods, message = ''):
        for method in methods:
            try:
                return self.until(method, message) #@IgnoreException
            except TimeoutException:
                if (method != methods[-1]):
                    continue
                else:
                    raise

previous = None
def new_tab(driver: EventFiringWebDriver, full_route=[], switch=False, url=None):
    global previous
    previous = driver.current_window_handle
    
    window_handles = set(driver.window_handles)
    driver.execute_script("window.open('');")
    new_tab = list(set(driver.window_handles)-window_handles )[0]

    driver.switch_to.window(new_tab)
    driver.get(url)
    
    if (type(full_route) is list):
        follow_path(driver, full_route)
    
    if not switch: # switched by default
        switch_to(driver, previous)

    return new_tab

def switch_to(driver: EventFiringWebDriver, tab):
    if (driver.current_window_handle == tab):
        return
    global previous
    previous = driver.current_window_handle
    driver.switch_to.window(tab)

def switch_back(driver: EventFiringWebDriver):
    global previous
    try:
        current = driver.current_window_handle #@IgnoreException
    except NoSuchWindowException:
        current = None
    driver.switch_to.window(previous)
    previous = current

def close_tab(driver: EventFiringWebDriver, tab):
    switch_to(driver, tab)
    driver.close()
    switch_back(driver)

def follow_path(driver, routes):
    temp_found_el = None
    def find(path):
        nonlocal temp_found_el
        temp_found_el = find_element(driver, path)
    def click(path):
        nonlocal temp_found_el
        find_element(temp_found_el or driver, path).click()
        temp_found_el = None
    def input_keys(value):
        nonlocal temp_found_el
        temp_found_el.send_keys(value)
        temp_found_el = None
    def wait_until(path):
        nonlocal temp_found_el
        WebDriverWait(temp_found_el or driver, timeout=5).until(
            EC.visibility_of_element_located(get_locator(path))
        )
        temp_found_el = None
    def wait(entity):
        nonlocal temp_found_el
        match entity:
            case 'datatable':
                WebDriverWait(temp_found_el or driver, timeout=5).until_not(
                    EC.visibility_of_element_located(get_locator(x.table_paths['datatable_processing']))
                )
            case _:
                raise NotImplementedError(entity)
        temp_found_el = None
    def link(url):
        driver.get(url)

    if (not routes):
        return

    route_types = {
        'find': find,
        'click': click,
        'input': input_keys,
        'wait_until': wait_until,
        'wait': wait,
        'link': link
    }

    for route in routes:
        route_type, setting = route.split(': ', 1)
        element = route_types[route_type](setting)
        
        if (route_type == 'return'): return temp_found_el
        
        

def ignore_timeout_exception(wait):
    value = None
    def setval(f):
        nonlocal value
        value = f()
        return value
    try:
        return wait(setval)
    except TimeoutException:
        return value
    