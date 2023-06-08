from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from driver_helper import find_element, find_elements, find_element_or_none, get_locator
import xpaths as x

class Template: pass

def prepare_spinnable(btn):
    def cb(btn):
        spinner_tag = find_element(btn, 'TA: i')
        btn.click()
        WebDriverWait(driver=spinner_tag, timeout=5).until_not(
            lambda btn: 'fa-spinner' in btn.get_attribute('class')
        )
    return lambda btn=btn: cb(btn) # btn=btn - so that the yielded lambdas are not the same

def prepare_rows_refreshable(table, click_fn):
    def cb(table, click_fn):
        old_rows = find_elements(table, x.table_paths['rows'], False)

        click_fn()
        # FIXME: order: spinning stops -> rows update(?) -> show mode -> rows get updated again

        return WebDriverWait(driver=table, timeout=2).until(
            # 1) get new rows
            # 2) check if new rows are the same as the rows read before clicking the pagination button (comparing only first rows)
            # 3) if they are it means that new rows have not been loaded, yet, so None is to be returned, so that 
            # WebDriverWait knows that no satisfying result has been achieved, yet
            # 4) otherwise return those newly read rows. WebDriverWait exits, returning those rows.
            # BUG: if no rows
            lambda table: new_rows if (new_rows := find_elements(table, x.table_paths['rows'], False))[0].id != old_rows[0].id else None
        )
    return lambda click_fn=click_fn: cb(table, click_fn) # click_fn=click_fn - so that the yielded lambdas are not the same

def get_controls(table, requested_controls: set):
    def click_and_wait_to_disappear(btn):
        def cb(btn):
            t = table.text
            btn.click()
            WebDriverWait(driver=btn, timeout=5).until(
                EC.invisibility_of_element(btn)
            )
            # WebDriverWait(driver=table, timeout=5).until(
            #     lambda: t != table.text
            # )
        return lambda btn=btn: cb(btn) # btn=btn - so that the yielded lambdas are not the same


    footer_controls = x.table_paths['footer']

    controls = ['save', 'edit', 'cancel', 'refresh']
    absent_controls = getattr(table, 'absent_buttons', [])
    for control in controls:
        if control not in requested_controls:
            continue
        if control in absent_controls:
            yield lambda: ''
            continue
        control_btn = WebDriverWait(driver=table, timeout=2, ignored_exceptions=NoSuchElementException).until(
            EC.presence_of_element_located(get_locator(footer_controls[control]))
        )
        control_click = prepare_spinnable(control_btn)
        if (control == 'save'):
            control_click = prepare_rows_refreshable(table, control_click)
        yield control_click
    
    omissibles = {'add_row': prepare_spinnable, 'clone': click_and_wait_to_disappear}
    for omissible in omissibles.keys() & requested_controls:
        if omissible in absent_controls:
            yield lambda: ''
            continue
        wait_func = omissibles[omissible]
        try:
            omissible_btn = WebDriverWait(driver=table, timeout=2, ignored_exceptions=NoSuchElementException).until( #@IgnoreException
                EC.presence_of_element_located(get_locator(footer_controls[omissible]))
            )
        except TimeoutException:
            continue
        omissible_click = wait_func(omissible_btn) # control_btn=control_btn - so that the yielded lambdas are not the same
        yield omissible_click
        
def edit(table):
    edit = list(get_controls(table, ['edit']))[0]
    edit()
def save(table):
    save = list(get_controls(table, ['save']))[0]
    save()

def read_row(table, row, status, prefix, existing=None):
    if (existing is not None):
        t = existing
    else:
        t = Template()
    t.xStatus = status
    for cell, header in table.zip(find_elements(row, x.table_paths['cells_reading']), table.reading_headers):
        setattr(t, prefix+header.value, header.parse(cell))
    return t

def add_row_simple(table, times=1):
    save, edit, add_row = list(get_controls(table, ['save', 'edit', 'add_row']))
    edit()
    for _ in range(times):
        add_row()
    save()

def add_row(table, filler):
    save, edit, add_row = list(get_controls(table, ['save', 'edit', 'add_row']))

    edit()
    add_row()
    filler(find_elements(table, x.table_paths['visible_rows'])[-1])
    save()

    table.current_records_len+=1
    return find_elements(table, x.table_paths['visible_rows'])[-1]

def delete_last_row(table, times = 1):
    save, edit = list(get_controls(table, ['save', 'edit']))
    edit()
    rows_to_delete = find_elements(table, x.table_paths['visible_rows'])
    for row_to_delete in rows_to_delete[::-1][:times]:
        delete_btn = find_element(row_to_delete, x.table_paths['row_delete_button'])
        delete_btn.click()
    save()
    
def delete_row(table, row):
    save, edit = list(get_controls(table, ['save', 'edit']))

    edit()
    delete_btn = find_element(row, x.table_paths['row_delete_button'])
    delete_btn.click()
    
    save()
    table.current_records_len-=1

def clone(table):
    edit, clone = list(get_controls(table, ['edit', 'clone']))
    edit()
    clone()