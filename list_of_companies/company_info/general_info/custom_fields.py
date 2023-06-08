from driver_helper import find_element, find_element_timedout, find_elements, find_element_or_none, ignore_timeout_exception
from loggers.error_logger import assert_equals
import globals as g
from tables.table_controls import add_row_simple, delete_last_row
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from random import getrandbits

paths = {
    'checkbox_all': 'XP: .//label[@for="cb_check_all_customfields"]/../*[self::input or self::label]',
    'checkbox_single': 'XP: .//label[starts-with(@for,"cb_check_customfield_")]/../*[self::input or self::label]',
    'add_to_notes': 'XP: .//button[text()="Add to Report Notes"]',
    'report_notes_sidebar': 'XP: .//*[@id="company--note-tab"]',
    'report_notes_table': 'XP: .//*[@id="frm_note_base"]//td',
    'general_info_sidebar': 'XP: .//a[@id="company--baseinfo-tab"]'
}

class Checkbox:
    def __init__(self, input, label):
        self.input = input
        self.label = label

def test_check_all(parent, table):
    """on_start"""
    def assert_checkboxes(checkbox_all, table):
        should_be_checked = checkbox_all.input.is_selected()
        checkboxes = find_elements(table, paths['checkbox_single'], False)
        for input in checkboxes[::2]:
            assert_equals(parent+'.test_check_all', input.is_selected(), should_be_checked)

    table.add_row(times=5, fill=False)
    table.delete_last_row(times=2)
    table.add_row(times=2, fill=False)

    checkbox_all = Checkbox(*find_elements(table, paths['checkbox_all'], False)) # TODO: change to classes.Checkbox

    checkbox_all.label.click()
    assert_checkboxes(checkbox_all, table)

    checkbox_all.label.click()
    assert_checkboxes(checkbox_all, table)

    table.delete_last_row(times=5)

records_checked = []
def check_row(parent, row):
    checkbox = Checkbox(*find_elements(row, paths['checkbox_single'], False))
    old_value = checkbox.input.is_selected()
    checkbox.label.click()
    assert_equals(parent+': asserting checkbox changed its value after click',checkbox.input.is_selected(), not old_value)
def check_first(parent, row, record):
    check_row(parent, row)
    records_checked.append(record)
    global callback
    callback = check_next
def check_next(parent, row, record):
    if (bool(getrandbits(1))):
        return
    check_row(parent, row)
    records_checked.append(record)

    
callback = check_first
def check_checkbox_randomly(parent, row, record):
    """on_iteration"""
    callback(parent, row, record)


def add_to_report_notes(parent, table, records):
    """on_end"""
    find_element(table, paths['add_to_notes']).click()
    find_element(g.driver, paths['report_notes_sidebar']).click()
    # Page might have been loaded, but the block of notes have not. Thus, wait for 2 seconds. If still nothing, return whatever was read
    note = ignore_timeout_exception(
        lambda save: WebDriverWait(g.driver, timeout=2, ignored_exceptions=TimeoutException).until(
            lambda d: save(lambda: find_element_timedout(d, paths['report_notes_table']).text)
        )
    )
    lines = note.split('\n')
    assert_equals(parent, True, len(lines) >= len(records_checked))
    for record, line in zip([r for r in records_checked if r.Name+r.Value != ''], lines): # filter out empty records. They are not added to notes
        # TODO: improve this comparison alhorithm  
        assert_equals(parent+f': asserting that line "{record.Name}: {record.Value}" is un report notes',f'{record.Name}: {record.Value}' == line, True)
    find_element(g.driver, paths['general_info_sidebar']).click()
