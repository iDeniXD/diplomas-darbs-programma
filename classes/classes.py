from selenium.webdriver.support.events import AbstractEventListener
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebElement
from selenium.webdriver.support.wait import WebDriverWait

from json import JSONEncoder
from driver_helper import Wait, find_element, find_element_or_none, find_elements
from tables.value_parser import edit_only_parser, parser, value_changer
from loggers.error_logger import try_fn
from types import MethodType

import tables.table_controls as table_controls
import xpaths as x

def load_file_methods(file_name: str, functions: list[str]):
    module = __import__(file_name, fromlist=functions)
    return [getattr(module, function) for function in functions]

class runnable_dict(dict):
    def run(self, event, module_name, *args, **kwargs):
        if (fn_names := self.get(event)):
            mod = __import__(module_name, fromlist=fn_names)
            for fn_name in fn_names:
                fn = getattr(mod, fn_name)
                result = try_fn(fn, *args, try_fn_parent = module_name, **kwargs)
                if (result is not None): # if nothing returned - either last function or the same args need to be passed
                    args, kwargs = result # TODO: return forgot???
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
class Template:
    def default(self, o):
        # TODO: docs
        return o.__dict__
    def __eq__(self, other):
        other_var = vars(other)
        for key, value in vars(self).items():
            if (value != other_var.get(key)):
                return False
        return True

class DriverLinkChangeListener(AbstractEventListener):
    def execute_scripts(self, driver):
        driver.execute_script('document.getElementsByTagName("html")[0].style.scrollBehavior = "auto"')
    def after_navigate_to(self, url, driver):
        self.execute_scripts(driver)
    def after_navigate_back(self, driver):
        self.execute_scripts(driver)
    def after_navigate_forward(self, driver):
        self.execute_scripts(driver)
    def after_click(self, element, driver):
        try:
            element.tag_name #@IgnoreException
        except StaleElementReferenceException:
            # if the element is no longer attached to the page, most probably it is because
            # it was a link clicked
            self.execute_scripts(driver)

class ResultEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
    
# TODO
class Table(EventFiringWebElement):
    def __init__(self, parent: str, initial: EventFiringWebElement, table_type: str, columns: dict | None = None, info_row_columns: dict | None = None):
        super().__init__(initial.wrapped_element, initial._ef_driver)
        columns = {} if columns is None else columns 
        info_row_columns = {} if info_row_columns is None else info_row_columns

        self.parent_path = parent
        self.table_type = table_type
        
        self.__current_records_len = 0

        self.__columns = columns
        self.__info_row_columns = info_row_columns
        self.__setup()

    @property
    def current_records_len(self):
        if (self.table_type != 'datatable'):
            return self.__current_records_len
        
        return self.__get_datatable_length()

    def __get_column_type(self, index, name):
        def coalesce(*values):
            for value in values: 
                if value is not None:
                    return value
        return coalesce(self.__columns.get(str(index)), self.__columns.get(name), 'text')
    def __setup(self):
        setupers = {
            'horizontal': self.__setup_horizontal_table,
            'vertical': self.__setup_vertical_table, 
            'info-rows': self.__setup_horizontal_table, #self.__setup_info_rows_table,
            'one-celled': self.__setup_one_celled_table, #self.__setup_one_celled_table,
            'datatable': self.__setup_data_table, #self.__setup_dataTable_table,
            'edit-only-horizontal': self.__setup_edit_only_horizontal,
            'edit-only-textarea': self.__setup_edit_only_textarea,
            'edit-only-vertical': self.__setup_edit_only_vertical
        }
        setupers[self.table_type]()
    def __setup_horizontal_table(self):
        self.__rows_path = x.table_paths['visible_rows']
        self.__headers_path = x.table_paths['table_headers']
        self.__editing_cells_path = x.table_paths['cells_editing']
        self.__cell_edit_div_path = x.table_paths['edit_div']
        self.__cell_input_path = x.table_paths['cell_input']
        self.get_readable_cells = self.__get_readable_cells_horizontal
        self.get_editable_cells = self.__get_editable_cells_horizontal
        self.get_rows = self.__get_rows_horizontal
        self.add_row = self.__add_row_horizontal
        self.delete_row = self.__delete_row
        self._get_edit_button = self.__get_edit_button
        self._get_save_button = self.__get_save_button
        self.is_refreshable = True # identifies if a new tab should be opened after or before 'save' button is clicked
        self.__setup_headers_horizontal()
    def __setup_vertical_table(self):
        self.__rows_path = x.table_paths['vertical_row']
        self.__headers_path = x.table_paths['table_vertical_headers']
        self.__cell_edit_div_path = x.table_paths['edit_div']
        self.__cell_input_path = x.table_paths['cell_input']
        self.get_readable_cells = self.__get_readable_cells_vertical
        self.get_editable_cells = self.__get_editable_cells_vertical
        self.get_row = self.__get_rows_vertical
        self.add_row = self.__add_row_horizontal
        self.delete_row = self.__delete_row
        self._get_edit_button = self.__get_edit_button
        self._get_save_button = self.__get_save_button
        self.is_refreshable = True
        self.__setup_headers_vertical()
    def __setup_info_rows_table(self):
        pass
        self.__setup_headers()
    def __setup_one_celled_table(self):
        self.__cell_path = x.table_paths['one_celled']
        self.__header_path = x.table_paths['one_celled_title']
        self.__cell_edit_div_path = x.table_paths['edit_div']
        self.__cell_input_path = x.table_paths['cell_input']
        self.get_readable_cell = self.__get_readable_cell
        self.get_editable_cell = self.__get_editable_cell
        self._get_edit_button = self.__get_edit_button
        self._get_save_button = self.__get_save_button
        self.is_refreshable = True
        self.__setup_header_one_celled()
    def __setup_data_table(self):
        self.__rows_path = x.table_paths['visible_rows']
        self.__headers_path = x.table_paths['table_headers']
        self.get_readable_cells = self.__get_readable_cells_horizontal
        self.get_rows = self.__get_rows_datatable
        self.is_refreshable = True # identifies if a new tab should be opened after or before 'save' button is clicked
        self.container = find_element(self, x.table_paths['datatable_container'])
        self.__setup_headers_datatable()
        self.__setup_datatable_editor_methods()
    def __setup_edit_only_horizontal(self):
        # self.add_row = self.__add_row_save
        self.__rows_path = x.table_paths['visible_rows']
        self.__headers_path = x.table_paths['table_headers']
        self.__editing_cells_path = x.table_paths['edit_only_row_cells_editing']
        self.__cell_edit_div_path = 'XP: .'
        self.__cell_input_path = x.table_paths['cell_input']
        self.get_readable_cells = self.__get_readable_cells_edit_only_horizontal
        self.get_editable_cells = self.__get_editable_cells_horizontal
        self.get_rows = self.__get_rows_horizontal
        self.add_row = self.__add_row_edit_only
        self.delete_row = self.__delete_row
        self._get_edit_button = lambda: lambda: None # should return a button callback which set table into editing mode
        self._get_save_button = self.__get_save_button_edit_only_horizontal
        self.is_refreshable = False
        self.__setup_headers_horizontal()
        self.__setup_headers_edit_only_horizontal()
    def __setup_edit_only_textarea(self):
        self.__cell_path = 'XP: .'
        self.__cell_edit_div_path = 'XP: .'
        self.__cell_input_path = 'XP: .'
        self.get_readable_cell = self.__get_readable_cell
        self.get_editable_cell = self.__get_editable_cell
        self._get_edit_button = lambda: lambda: None # should return a button callback which set table into editing mode
        self._get_save_button = self.__get_save_button_edit_only_horizontal
        self.is_refreshable = False
        self.__setup_header_edit_only_textarea()
    def __setup_edit_only_vertical(self):
        self.__rows_path = x.table_paths['vertical_row']
        self.__headers_path = x.table_paths['table_vertical_headers']
        self.__cell_edit_div_path = 'XP: .'
        self.__cell_input_path = x.table_paths['cell_input']
        self.get_readable_cells = self.__get_readable_cells_vertical
        self.get_editable_cells = self.__get_editable_cells_vertical
        self.get_row = self.__get_rows_vertical
        self.add_row = self.__add_row_edit_only
        self._get_edit_button = lambda: lambda: None # should return a button callback which set table into editing mode
        self._get_save_button = self.__get_save_button_edit_only_horizontal
        self.is_refreshable = False 
        self.__setup_headers_vertical()
        self.__setup_headers_edit_only_horizontal()

    def __setup_headers_horizontal(self):
        headers_elements = [h.text for h in find_elements(self, self.__headers_path)]
        if (headers_elements == []):
            headers_elements = list(self.__columns.keys())
        self.headers = []

        if (rows := self.get_rows()):
            template_row = rows[0]
        else:
            template_row = self.add_row(fill=False)
        cells = [c.id for c in find_elements(template_row, x.table_paths['row_cells'])]
        editable_cells = [c.id for c in find_elements(template_row, self.__editing_cells_path)]

        for i, header_el in enumerate(headers_elements):
            header = Template()
            header.value = header_el
            header.type = self.__get_column_type(i, header.value)
            # header.colspan = int(header_el.get_attribute('colspan') or 1)
            header.parse = parser(header.type)
            header.change_value = value_changer(header.type, self.parent_path)
            header.reading = header.value != ''
            header.editing = cells[i] in editable_cells # TODO: test
            self.headers.append(header)
        if (not rows):
            self.delete_last_row()
    def __setup_headers_vertical(self):
        headers_elements = [h.text for h in find_elements(self, self.__headers_path)]
        self.headers = []

        for i, header_el in enumerate(headers_elements):
            header = Template()
            header.value = header_el
            header.type = self.__get_column_type(i, header.value)
            # header.colspan = int(header_el.get_attribute('colspan') or 1)
            header.parse = parser(header.type)
            header.change_value = value_changer(header.type, self.parent_path)
            header.reading = True
            header.editing = True
            self.headers.append(header)

    def __setup_header_one_celled(self):
        header_el = find_element(self, self.__header_path)      

        header = Template()
        header.value = header_el.text
        header.type = self.__get_column_type(0, header.value)
        header.parse = parser(header.type)
        header.change_value = value_changer(header.type, self.parent_path)
        header.reading = True
        header.editing = True

        self.header = header

    def __setup_header_edit_only_textarea(self):
        value, column_type = next(iter(self.__columns.items())) # get first dict element

        header = Template()
        header.value = value
        header.type = column_type
        header.parse = parser(header.type)
        header.change_value = value_changer(header.type, self.parent_path)
        header.reading = True
        header.editing = True

        self.header = header
    
    def __setup_headers_edit_only_horizontal(self):
        for header in self.headers:
            header.parse = edit_only_parser(header.type)
            
    def __setup_headers_datatable(self):
        headers_elements = [h.text for h in find_elements(self, self.__headers_path)]
        if (headers_elements == []):
            headers_elements = list(self.__columns.keys())
        self.headers = []

        for i, header_el in enumerate(headers_elements):
            header = Template()
            header.value = header_el
            header.type = self.__get_column_type(i, header.value)
            header.parse = parser(header.type)
            header.reading = header.value != ''
            self.headers.append(header)

    def __setup_datatable_editor_methods(self):
        add_row, edit_row, delete_row = load_file_methods(self.parent_path, ['add_row', 'edit_row', 'delete_row'])
        self.add_row = MethodType(add_row, self)
        self.edit_row = MethodType(edit_row, self)
        self.delete_row = MethodType(delete_row, self)



    def __get_datatable_length(self):
        self.__datatable__get_rows_awaited() # wait till loaded
        entries_label = find_element_or_none(self.container, x.table_paths['datatable_entries_label'])
        if (entries_label is None):
            return 0
        
        return int(entries_label.text.split(' ')[-2])



    def filler(self,row,*args):
        for cell in self.get_editable_cells(row):
            cell.change_value(*args)
    def __add_row_horizontal(self, *args, times = 1, fill = True):
        add_row = list(table_controls.get_controls(self, ['add_row']))[0]

        self.edit()
        for _ in range(times):
            add_row()
            if (fill):
                self.filler(self.get_rows()[-1], *args)
        self.save()

        self.__current_records_len+=1
        return self.get_rows()[-1]
    def __get_new_row(self, old_rows):
        for row in self.get_rows():
            if row.id in old_rows:
                continue
            return row
        raise RuntimeError('No new error was added')
    def __add_row_edit_only(self, *args, times = 1, fill = True):
        add_row = list(table_controls.get_controls(self, ['add_row']))[0]
        old_rows = [r.id for r in self.get_rows()]

        self.edit()
        for _ in range(times):
            add_row()
            if (fill):
                self.filler(self.__get_new_row(old_rows), args)
        self.save()

        self.__current_records_len+=1
        return self.__get_new_row(old_rows)
    def delete_last_row(self, times = 1):
        self.edit()
        rows_to_delete = find_elements(self, self.__rows_path)
        for row_to_delete in rows_to_delete[::-1][:times]:
            delete_btn = find_element(row_to_delete, x.table_paths['row_delete_button'])
            delete_btn.click()
        self.save()

    def __delete_row(self, row):
        self.edit()
        delete_btn = find_element(row, x.table_paths['row_delete_button'])
        delete_btn.click()
        
        self.save()
        self.__current_records_len-=1

    def __get_edit_button(self):
        return list(table_controls.get_controls(self, ['edit']))[0] # TODO: get rid of this function, use the prepare button function
    def edit(self):
        self._get_edit_button()()
    def __get_save_button(self):
        return table_controls.prepare_rows_refreshable(self,table_controls.prepare_spinnable(find_element(self, x.table_paths['footer']['save'])))
    def __get_save_button_edit_only_horizontal(self):
        return table_controls.prepare_spinnable(find_element(self, x.table_paths['footer']['save']))
    def save(self):
        self._get_save_button()()
    
    def clone(self):
        self.edit()
        clone = list(table_controls.get_controls(self, ['clone']))[0]
        clone()

    def __get_rows_horizontal(self):
        rows = find_elements(self, self.__rows_path)
        self.__current_records_len = len(rows)
        return rows
    def __get_rows_vertical(self):
        return find_elements(self, self.__rows_path)
    def __get_readable_cell(self):
        cell = find_element(self, self.__cell_path)
        cell.header = self.header.value
        cell.value = lambda c=cell, h=self.header: h.parse(c)
        return cell
    

    def __datatable__get_rows_awaited(self):
        def loaded(_):
            rows = find_elements(self, self.__rows_path)
            if (len(rows) > 0):
                if (rows[0].text == 'Loading...'):
                    return False
            elif (not find_element(self.container, x.table_paths['datatable_entries_label']).text):
                return False
            return rows

        """
        Wait till:
        * there are >1 rows
        OR
        * there is one row 
        * it says anything other than 'Loading...'
        OR
        * at least the 'showing entries' label is not empty
        """
        rows = WebDriverWait(self, timeout=5).until(loaded) # TODO: change to 5
        return rows
    def __get_rows_datatable(self):
        def pages(container):
            yield
            while (btn := find_element_or_none(container, x.table_paths['datatable_container_next_page_btn'])) is not None:
                # if the button is disabled it will not be found due to its path
                btn.click()
                yield
        
        for _ in pages(self.container):
            for row in self.__datatable__get_rows_awaited():
                yield row
        if (first_page := find_element_or_none(self.container, x.table_paths['datatable_container_first_page_btn'])) is not None:
            first_page.click()

    

    def get_all_cells(self, row):
        for cell, header in zip(find_elements(row, x.table_paths['row_cells']), self.headers):
            cell.header = header.value
            yield cell

    def __get_readable_cells_horizontal(self, row):
        cells = find_elements(row, x.table_paths['row_cells'])
        for cell, header in zip(cells, self.headers):
            if (not header.reading):
                continue
            else:
                cell.header = header.value
                cell.value = lambda c=cell, h=header: h.parse(c)
                yield cell
    def __get_readable_cells_vertical(self, cells):
        for cell, header in zip(cells, self.headers):
            if (not header.reading):
                continue
            else:
                cell.header = header.value
                cell.value = lambda c=cell, h=header: h.parse(c)
                yield cell
    def __get_readable_cells_edit_only_horizontal(self, row): # TODO: del?
        cells = find_elements(row, x.table_paths['row_cells'])
        for cell, header in zip(cells, self.headers):
            if (not header.reading):
                continue
            else:
                cell.header = header.value
                cell.value = lambda c=cell, h=header: h.parse(c)
                yield cell
    def __get_editable_cells_horizontal(self, row):
        cells = find_elements(row, x.table_paths['row_cells'])
        for cell, header in zip(cells, self.headers):
            if (not header.editing):
                continue
            else:
                cell.change_value = lambda *args, c=cell, h=header: h.change_value(c, *args)
                cell.edit_div_path = self.__cell_edit_div_path
                cell.input_path = self.__cell_input_path
                yield cell
    def __get_editable_cells_vertical(self, cells):
        for cell, header in zip(cells, self.headers):
            if (not header.editing):
                continue
            else:
                cell.change_value = lambda *args, c=cell, h=header: h.change_value(c, *args)
                cell.edit_div_path = self.__cell_edit_div_path
                cell.input_path = self.__cell_input_path
                yield cell
    def __get_editable_cell(self):
        cell = find_element(self, self.__cell_path)
        cell.change_value = lambda *args, c=cell, h=self.header: h.change_value(c, *args)
        cell.edit_div_path = self.__cell_edit_div_path
        cell.input_path = self.__cell_input_path
        return cell




