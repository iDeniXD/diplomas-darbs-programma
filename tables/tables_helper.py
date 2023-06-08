from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

from classes.classes import Table, Template, runnable_dict
from random import choice, randint, sample, getrandbits

from driver_helper import close_tab, find_element, find_elements, find_element_or_none, new_tab, switch_back, switch_to
from loggers.error_logger import assert_equals, assert_records_changed, try_fn, log
from scenario_reader_helper import find_preference, preference_exists
from tables.table_controls import clone
from tables.table_reader import read_table
from tables.tables_editor import edit_table
import xpaths as x

from tables.value_parser import parser, value_changer


last_parent = None
another_tab = None
def test_table(driver, settings: runnable_dict, parent: str, full_route: dict, current_step_result: Template):
    global last_parent, another_tab
    table = Table(parent, find_element(driver, settings['table_path']), settings['table_type'], settings.get('columns'), settings.get('info_row_columns'))

    args = {
        'settings': settings, 
        'parent': parent, 
        'table': table,
        'try_fn_parent': parent
    }
    table_records = try_fn(
        read_table,
        **args
    )



    if not preference_exists(settings['to_test'], 'edit'):
        return table_records
    



    def safe_rindex(str, substr):
        try:
            return str.rindex(substr) #@IgnoreException
        except ValueError:
            pass
    # open new tab before editing if the table can be refreshed and the last checked table did not have the same parent as the current
    if (table.is_refreshable and last_parent != parent[:safe_rindex(parent, '.')]):
        # if checking tab has already been opened, close it and open another with a new parent
        if (another_tab is not None):
            close_tab(driver, another_tab)
        another_tab = new_tab(driver, full_route, url='/'.join(driver.current_url.split('/')[:3]))
        last_parent = parent[:parent.rindex('.')] # save the new parent used last to open another tab
    
    # edit the table, save editing history
    edited_history = try_fn(
        edit_table,
        table_records=table_records,
        **args
    )
    # read the same table once again, after saving
    table_new_records = try_fn(
        read_table,
        events_enabled = False,
        **args
    )
    # if the table is refreshable, another tab with the same table was opened, switch to it and read the same table once again
    if (table.is_refreshable):
        switch_to(driver, another_tab)
        args['table'] = table = Table(parent, find_element(driver, settings['table_path']), settings['table_type'], settings.get('columns'), settings.get('info_row_columns'))
        try_fn(refresh, table, settings['to_test'], try_fn_parent = parent)
    else:
        # otherwise, if the table does not have 'Refresh' button, another tab must be opened now
        if (another_tab is not None): # close whatever another tab opened
            close_tab(driver, another_tab)
        # duplicate tab with the current table
        another_tab = new_tab(driver, full_route, url='/'.join(driver.current_url.split('/')[:3]), switch=True)
        last_parent = parent[:parent.rindex('.')]
        args['table'] = table = Table(parent, find_element(driver, settings['table_path']), settings['table_type'], settings.get('columns'), settings.get('info_row_columns'))
        
    # read the same table on the another tab
    another_tab_records = try_fn(
        read_table,
        events_enabled = False,
        **args
    )
    # TODO: parent title
    # Take the records read before editing, recreate the editing history and compare them to the recrods read AFTER editing. They should be the same
    assert_records_changed(parent, table_records, edited_history, table_new_records)
    # Take the records read before editing, recreate the editing history and compare them to the recrods read AFTER editing in the another tab. They should be the same
    assert_records_changed(parent, table_records, edited_history, another_tab_records)
    switch_back(driver) # switch to the original tab




    if not preference_exists(settings['to_test'], 'clone'):
        return table_new_records
    
    # get the PREVIOUSLY read record of a table to be copied
    table_records = getattr(current_step_result, clonable_table := (find_preference(settings['to_test'], 'clone')['table'][0]), None)
    if (table_records is None): # if None, log the error and exit
        log(
            parent, 
            f'trying to clone records from {clonable_table}', 
            f'the table {clonable_table} has either been not read, yet, or an error was encountered when working with it'
        )
        return table_new_records
    
    args['table'] = table = Table(parent, find_element(driver, settings['table_path']), settings['table_type'], settings.get('columns'), settings.get('info_row_columns'))
    table.clone()
    table_new_records = try_fn( # read the cloned records
        read_table,
        events_enabled = False,
        **args
    )

    switch_to(driver, another_tab)

    args['table'] = table = Table(parent, find_element(driver, settings['table_path']), settings['table_type'], settings.get('columns'), settings.get('info_row_columns'))
    try_fn(refresh, table, settings['to_test'], try_fn_parent = parent)
    another_tab_records = try_fn( # read the cloned records in the another tab
        read_table,
        events_enabled = False,
        **args
    )
    # assert that cloned records are the same as in the original table
    assert_equals(parent, table_records, table_new_records)
    # assert that cloned records in the another tab are the same as in the original table
    assert_equals(parent, table_records, another_tab_records)

    switch_back(driver)
    return table_new_records


def refresh(table, to_test: list[str]): # TODO
    def get_rows(table: WebElement):
        return find_elements(table, x.table_paths['rows'], False)
    found = preference_exists(to_test, 'refresh')
    if (not found):
        return

    refresh_btn = find_element(table, x.table_paths["refresh_button"]) # TODO: refresh_type with find_preference

    old_rows = get_rows(table)
    refresh_btn.click()

    return WebDriverWait(driver=table, timeout=2).until(
        # 1) get new rows
        # 2) check if new rows are the same as the rows read before clicking the pagination button (comparing only first rows)
        # 3) if they are it means that new rows have not been loaded, yet, so None is to be returned, so that 
        # WebDriverWait knows that no satisfying result has been achieved, yet
        # 4) otherwise return those newly read rows. WebDriverWait exits, returning those rows.
        lambda table: new_rows if (new_rows := get_rows(table))[0].id != old_rows[0].id else None
    )
    
    # TODO: test if waits till new rows loaded or skips. If skips write that down in docstring
    # match test_opt.split('|')[1:]:
    #     case ['static'] | []:
    #         press_refresh_button()
    #     case ['spinning']:
    #         press_refresh_button()