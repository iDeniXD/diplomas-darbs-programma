from typing import Callable
from classes.classes import Table, Template, runnable_dict
from driver_helper import find_element, find_elements, new_tab
from loggers.error_logger import try_fn
from tables.table_controls import add_row, delete_row, edit, save
from random import choice, randint
import xpaths as x

def edit_table(settings: runnable_dict, parent: str, table, table_records):
    args = get_args(parent, table, settings, table_records) # TODO: edit_times int

    match(settings['table_type']):
        case 'horizontal' | 'edit-only-horizontal':
            return _edit_horizontal(**args)
        case 'vertical' | 'edit-only-vertical':
            return _edit_vertical(**args)
        case 'info-rows':
            return _edit_info_rowed(**args)
        case 'one-celled' | 'edit-only-textarea':
            return _edit_one_celled(**args)
        case 'datatable':
            return _edit_datatable(**args)
        case _:
            raise ValueError(f'Table of type "{settings["table_type"].join(", ")}" does not exist')

def get_args(parent, table, settings, records):
    return {
        'parent': parent,
        'table': table,
        'records': records, 

        'on_before_edit': lambda *args, **kwargs: settings.run('on_before_edit', parent, *args, **kwargs),
        'on_after_edit': lambda *args, **kwargs: settings.run('on_after_edit', parent, *args, **kwargs),

        'columns': settings.get('columns') or {},
        'info_row_columns': settings.get('infoRowColumns') or {}
    }
        

def _edit_horizontal(
    parent,
    table,
    records,

    on_before_edit: Callable,
    on_after_edit: Callable,

    edit_times = 5,
    **_
):   
    def read_row(table, row, status, prefix, existing=None):
        if (existing is not None):
            t = existing
        else:
            t = Template()
        t.xStatus = status
        for cell in table.get_readable_cells(row):
            setattr(t, prefix+cell.header, cell.value())
        return t
    

    available_actions = [
        'add_row',
        'delete_row',
        'edit_row'
    ]
    if (table.current_records_len < 5):
        available_actions.append('add_row')
    if (table.current_records_len > 10):
        available_actions.append('delete_row')   
    
    on_before_edit(parent, table)

    edited_records = []
    for i in range(edit_times):
        while True:
            match choice(available_actions):
                case 'add_row':
                    row = table.add_row(i)
                    edited_records.append(read_row(table, row, 'added', 'new_'))
                case 'delete_row':
                    if (table.current_records_len == 0):
                        continue
                    row = table.get_rows()[randint(0, table.current_records_len-1)]
                    edited_records.append(read_row(table, row, 'deleted', 'old_'))

                    table.delete_row(row)
                case 'edit_row':
                    if (table.current_records_len == 0):
                        continue
                    row = table.get_rows()[row_index := randint(0, table.current_records_len-1)]
                    edited_record = read_row(table, row, 'edited', 'old_')

                    table.edit()

                    for cell in table.get_editable_cells(row):
                        cell.change_value(i)

                    table.save()

                    row = table.get_rows()[row_index]
                    read_row(table, row, 'edited', 'new_', edited_record)
                    edited_records.append(edited_record)
            break

    on_after_edit(parent, table, records) # TODO: records or edited_records ?

    return edited_records


def _edit_vertical(
    parent,
    table,
    records,

    on_before_edit: Callable,
    on_after_edit: Callable,

    **_
):
    def read_column(table, prefix, existing=None):
        if (existing is not None):
            t = existing
        else:
            t = Template()
        t.xStatus = 'edited'
        for cell in table.get_readable_cells(table.get_row()):
            setattr(t, prefix+cell.header, cell.value())
        return t
    
    on_before_edit(parent, table)

    edited_record = read_column(table, 'old_')

    table.edit()
    for cell in table.get_editable_cells(table.get_row()):
        cell.change_value(0)
    table.save()

    read_column(table, 'new_', edited_record)

    on_after_edit(parent, table, edited_record)

    return edited_record


def _edit_one_celled(
    parent,
    table,
    records,

    on_before_edit: Callable,
    on_after_edit: Callable,

    **_
): 
    def read_cell(table, prefix, existing=None):
        if (existing is not None):
            t = existing
        else:
            t = Template()
        t.xStatus = 'edited'
        cell = table.get_readable_cell()
        setattr(t, prefix+cell.header, cell.value())
        return t
    
    on_before_edit(parent, table)

    edited_record = read_cell(table, 'old_')

    table.edit()
    table.get_editable_cell().change_value(0)
    table.save()

    read_cell(table, 'new_', edited_record)

    on_after_edit(parent, table, records)

    return edited_record

def _edit_datatable(
    parent,
    table: Table,
    records,

    on_before_edit: Callable,
    on_after_edit: Callable,

    edit_times = 5,
    **_
):
    def read_row(table, row, status, prefix, existing=None):
        if (existing is not None):
            t = existing
        else:
            t = Template()
        t.xStatus = status
        for cell in table.get_readable_cells(row):
            setattr(t, prefix+cell.header, cell.value())
        return t
    

    available_actions = [
        'add_row',
        # 'delete_row',
        # 'edit_row'
    ]
    # if (table.current_records_len < 5):
    #     available_actions.append('add_row')
    # if (table.current_records_len > 10):
    #     available_actions.append('delete_row')   
    
    on_before_edit(parent, table)

    edited_records = []
    for i in range(edit_times):
        while True:
            match choice(available_actions):
                case 'add_row':
                    row = table.add_row(index=i, records=records, edited_records=edited_records, parent=parent)
                    edited_records.append(read_row(table, row, 'added', 'new_'))
                case 'delete_row':
                    if (table.current_records_len == 0):
                        continue
                    row = table.get_rows()[randint(0, table.current_records_len-1)]
                    edited_records.append(read_row(table, row, 'deleted', 'old_'))

                    table.delete_row(row)
                case 'edit_row':
                    if (table.current_records_len == 0):
                        continue
                    row = table.get_rows()[row_index := randint(0, table.current_records_len-1)]
                    edited_record = read_row(table, row, 'edited', 'old_')

                    table.edit()

                    for cell in table.get_editable_cells(row):
                        cell.change_value(i)

                    table.save()

                    row = table.get_rows()[row_index]
                    read_row(table, row, 'edited', 'new_', edited_record)
                    edited_records.append(edited_record)
            break

    on_after_edit(parent, table, records) # TODO: records or edited_records ?

    return edited_records