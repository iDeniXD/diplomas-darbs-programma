from random import choice, randint
from classes.Inputs import Select2
from classes.classes import Table
from driver_helper import find_element as _find_element, find_element_or_none as _find_element_or_none
from loggers.error_logger import assert_equals, reproduce
import globals as g
from string import ascii_lowercase as letters
from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

paths = {
    'nav_link_list_of_companies': 'XP: .//nav//a[text()="List of Companies"]',
    'entries_label': 'ID: tbl-company-list_info',
    'create_company_button': 'XP: .//button[text()="New Company"]',
    'modal_input_company_name': 'XP: .//form[@id="frm_modal_new_company"]//input[@name="new_company_name"]',
    'modal_input_registration_number': 'XP: .//form[@id="frm_modal_new_company"]//input[@name="new_registration_number"]',
    'modal_input_jurisdiction_select': 'XP: .//form[@id="frm_modal_new_company"]//span[contains(@class, "select2")]',
    'modal_input_jurisdiction_dropdown': 'XP: .//ul[@id="select2-new_company_jurisdiction_ident-results"]',
    'modal_input_jurisdiction_dropdown_option': 'XP: ./li[not(@aria-selected="true" or @aria-disabled="true")][{}]',
    'modal_button_create': 'XP: .//div[@id="modal_confirmation_new_company"]//button[text()="Create"]',

    'company_page_company_name': 'TA: h1',

    'table_indexed_tr_company_link': 'XP: .//table[@id="tbl-company-list"]/tbody/tr[{}]//a',

    'sidebar_holder_tab': 'XP: .//nav//li/a[@id="company--{}-tab"]',
    'holder_edit_button': 'XP: .//form[@id="frm_government_{}"]//button[text()="Edit"]',
    'holder_add_row_button': 'XP: .//form[@id="frm_government_{}"]//button[text()="Add Row"]',
    'holder_type_select': 'XP: .//form[@id="frm_government_{}"]//tr[@class="tr-new"]//select[contains(@name, "destination_type")]',
    'holder_shares_input': 'XP: .//form[@id="frm_government_{}"]//tr[@class="tr-new"]//input[starts-with(@name, "col_new_shares_value_") or starts-with(@name, "col_new_ubo_value_")]',
    'holder_type_of_control_input': 'XP: .//form[@id="frm_government_{}"]//tr[@class="tr-new"]//select[starts-with(@name, "col_new_type_of_control_")]',
    'holder_position_input': 'XP: .//form[@id="frm_government_position"]//tr[@class="tr-new"]//input[starts-with(@name, "col_new_shares_value_")]',
    'holder_shares_unit': 'XP: .//form[@id="frm_{}_unit"]//div'
}

def add_row(self, parent, records, edited_records, **_): 
    table = self

    used_companies = get_used_companies_links(records, edited_records)
    current_company_name = find_element('company_page_company_name').text.split('/')[0]

    old_tab, new_tab = open_list_of_companies()
    holder_name = click_first_or_create_company(parent, used_companies)
    values = add_holder(current_company_name, choice(['shares', 'ubo', 'position']))
    close_switch_tab(new_tab, old_tab)
    
    table.refresh()
    row = find_row_by_company_name(table, holder_name)
    assert_correct_values(row, values)

    return row






def delete_row(self): 
    print('delete_row called')





def edit_row(self): 
    print('edit_row called')


driver = g.driver
def find_element(path, index = None):
    if (index is not None):
        path = paths[path].format(index)
    else:
        path = paths[path]
    return _find_element(driver, path)

def find_element_or_none(path):
    return _find_element_or_none(driver, paths[path])


def get_used_companies_links(records, history):
    return [getattr(r, 'Corporate Name').link for r in reproduce(records, history)]

def open_list_of_companies():
    old_tab = driver.current_window_handle
    window_handles = driver.window_handles

    ActionChains(driver) \
        .key_down(Keys.CONTROL) \
        .click(find_element('nav_link_list_of_companies')) \
        .key_up(Keys.CONTROL) \
        .perform()

    new_tab = list(set(driver.window_handles)-set(window_handles) )[0]
    driver.switch_to.window(new_tab)
    return old_tab, new_tab

def click_first_or_create_company(parent, used_companies):
    try:
        return take_random_company(parent, used_companies)
    except IndentationError:
        return create_company(used_companies)
    
def create_company(used_companies):
    def word():
        return ''.join(choice(letters) for _ in range(10))
    def number():
        return ''.join(randint(0,9) for _ in range(10))
    find_element('create_company_button').click()
    while True:
        find_element('modal_input_company_name').send_keys(name := word())
        if name not in used_names: break
    find_element('modal_input_registration_number').send_keys(number())

    Select2(find_element('modal_input_jurisdiction_select')).select_random()

    find_element('modal_button_create').click()

    return find_element('company_page_company_name').text

def take_random_company(parent, used_companies_links):
    listOfCompanies = Table(parent, _find_element(driver, 'CS: #tbl-company-list'), 'datatable', {
        'Company Name': 'link'
    })

    if (listOfCompanies.current_records_len == 0): # Showing 0 out of 0 entries
        raise IndentationError('No companies in the table')

    for row in listOfCompanies.get_rows():
        cell = next(listOfCompanies.get_readable_cells(row)) # get first cell (company name)
        link = cell.value()
        if (link.link not in used_companies_links): break
    else:
        raise IndentationError('No non-used companies in the table')
    _find_element(cell, 'TA: a').click()
    return link.text


def add_holder(company_name_to_add, type):
    def number():
        return ''.join(randint(0,9) for _ in range(randint(1,2)))
    find_element('sidebar_holder_tab', type).click()
    find_element('holder_edit_button', type).click()
    find_element('holder_add_row_button', type).click()

    Select(find_element('holder_type_select', type)).select_by_visible_text('Corporate')

    # select company
    company_select = Select2(find_element('holder_name_select')) # TODO: stopped here
    company_select.select_by_visible_text(company_name_to_add)

    shares = None
    if (shares_inpt := find_element_or_none('holder_shares_input', type)) is not None:
        shares_inpt.send_keys(shares := number())
        shares += ' ' + find_element('holder_shares_unit', type).text

    type_of_control = None
    if (type_of_control_slct := find_element_or_none('holder_type_of_control_input', type)) is not None:
        type_of_control_slct = Select(type_of_control_slct)
        type_of_control = type_of_control_slct.select_by_index(randint(1, len(type_of_control_slct.options)-1))
        type_of_control += ' ' + shares
        shares = None # in participation table, UBO shares are displayed inside UBO column

    position = None
    if (position_inpt := find_element_or_none('holder_position_input')) is not None:
        position_inpt.send_keys(position := number())

    return shares, type_of_control, position
    

def find_row_by_company_name(table, new_company_name):
    for row in table.get_rows():
        if row.text.startswith(new_company_name):
            return row

def assert_correct_values(table, row, values):
    def find(arr, filter):
        for x in arr:
            if (filter(x)):
                return x
        return None
    shares, type_of_control, position = values

    cells = table.get_readable_cells(row)
    if (shares is not None):
        cell = find(cells, lambda cell: cell.header == 'Shares')
        assert_equals(table.parent_path, shares in cell.value)
        return

    if (type_of_control is not None):
        cell = find(cells, lambda cell: cell.header == 'UBO')
        assert_equals(table.parent_path, type_of_control in cell.value)
        return

    if (position is not None):
        cell = find(cells, lambda cell: cell.header == 'Position')
        assert_equals(table.parent_path, position in cell.value)
        return




def open_new_tab():
    old_tab = driver.current_window_handle

    window_handles = set(driver.window_handles)
    driver.execute_script("window.open('');")
    new_tab = list(set(driver.window_handles)-window_handles )[0]

    driver.switch_to.window(new_tab)

    return old_tab, new_tab

def close_switch_tab(to_close_tab, to_switch_to_tab):
    if (driver.current_window_handle != to_close_tab):
        driver.switch_to.window(to_close_tab)
    driver.close()
    driver.switch_to.window(to_switch_to_tab)