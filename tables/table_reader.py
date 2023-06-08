from typing import Callable
from classes.classes import Table, Template, runnable_dict
from driver_helper import find_element, find_element_or_none, find_elements
from loggers.error_logger import try_fn
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
import xpaths as x


def read_table(settings: runnable_dict, parent, table, events_enabled = True):
    args = get_args(parent, table, settings, events_enabled)

    match(settings['table_type']):
        case 'horizontal' | 'edit-only-horizontal' | 'datatable':
            records = _read_horizontal(**args)
        case 'vertical' | 'edit-only-vertical':
            records = _read_vertical(**args)
        case 'info-rows':
            records = _read_info_rowed(**args)
        case 'one-celled' | 'edit-only-textarea':
            records = _read_one_celled(**args)
        case _:
            raise ValueError(f'Table of type "{settings["table_type"]}" does not exist')
    
    return records
    
        

def _read_horizontal(
    parent: str,
    table: Table,
    
    on_start: Callable,
    on_iteration: Callable,
    on_end: Callable,

    columns: dict, # TODO: del
    **_
):
    on_start(parent, table)

    records = []
    for row in table.get_rows():
        record = Template()
        for cell in table.get_readable_cells(row):
            setattr(record, cell.header, cell.value())
        on_iteration(parent, row, record)
        records.append(record)

    on_end(parent, table, records)

    return records
def _read_vertical(
    parent: str,
    table,
    
    on_start: Callable,
    on_iteration: Callable,
    on_end: Callable,

    columns: dict,
    **_
):    
    on_start(parent, table)

    record = Template()
    row = table.get_row()
    for cell in table.get_readable_cells(row):
        setattr(record, cell.header, cell.value())
    on_iteration(parent, row, record)

    on_end(parent, table, record)

    return record
def _read_info_rowed(
    parent: str,
    table,
    
    on_start: Callable,
    on_iteration: Callable,
    on_end: Callable,

    columns: dict,
    info_row_columns: dict,
    **_
):
    def get_cells(table, main, info):
        main_cells = find_elements(main, x.table_paths['cells_reading'])
        info_cells = find_elements(info, x.table_paths['cells_reading'])
        for cell, header in table.zip(main_cells+info_cells, table.reading_headers):
            if (header.skip):
                continue
            cell.header = header.value
            cell.value = header.parse(main_cells)
            yield cell
        return
    
    on_start(parent, table)

    records = []
    all_rows = table.get_rows()
    for main, info in zip(all_rows[::2],all_rows[1::2]):
        record = Template()
        for cell in get_cells(table, main, info):
            setattr(record, cell.header, cell.value)
        on_iteration(parent, (main, info), record)
        records.append(record)

    on_end(parent, table, records)
def _read_one_celled(
    parent: str,
    table,
    
    on_start: Callable,
    on_end: Callable,

    columns: dict,
    **_
):   
    on_start(parent, table)

    cell = table.get_readable_cell()

    record = Template()
    setattr(record, cell.header, cell.value())

    on_end(parent, table, record)

    return record


def get_args(parent, table, settings: runnable_dict, events_enabled):
    return {
        'parent': parent,
        'table': table,

        'on_start': lambda *args, **kwargs: settings.run('on_start', parent, *args, **kwargs) if events_enabled else lambda: None,
        'on_iteration': lambda *args, **kwargs: settings.run('on_iteration', parent, *args, **kwargs) if events_enabled else lambda: None,
        'on_end': lambda *args, **kwargs: settings.run('on_end', parent, *args, **kwargs) if events_enabled else lambda: None,

        'columns': settings.get('columns') or {},
        'info_row_columns': settings.get('infoRowColumns') or {}
    }