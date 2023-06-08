from random import randint
from driver_helper import find_element, find_element_or_none, find_elements
from selenium.webdriver.support.ui import Select


class Checkbox:
    __checkbox_label_path = 'CS: input[type="checkbox"], input[type="checkbox"] + label'
    __checkbox_label_checked = 'CS: input[type="checkbox"]:checked, input[type="checkbox"]:checked + label'

    def __init__(self, cb, label):
        self.cb = cb
        self.label = label

    @classmethod
    def find(cls, driver, checked=False):
        path = cls.__checkbox_label_path if not checked else cls.__checkbox_label_checked
        cb, label = find_elements(driver, path, False)[:2]
        return Checkbox(cb, label)

    @classmethod
    def find_all(cls, driver, checked=False):
        path = cls.__checkbox_label_path if not checked else cls.__checkbox_label_checked
        cbs_labels = find_elements(driver, path, False)
        arr = []
        for cb, label in zip(cbs_labels[::2], cbs_labels[1::2]):
            arr.append(Checkbox(cb, label)) 
        return arr
    
    def value(self):
        return self.cb.value
    @property
    def text(self):
        return self.label.text
    def click(self):
        return self.label.click()
    def is_selected(self):
        return self.cb.is_selected()
        
class Radio:
    __radio_label_path = 'CS: input[type="radio"], input[type="radio"] + label'
    __radio_label_checked = 'CS: input[type="radio"]:checked, input[type="radio"]:checked + label'

    def __init__(self, rad, label):
        self.rad = rad
        self.label = label

    @classmethod
    def find(cls, driver, checked=False):
        path = cls.__radio_label_path if not checked else cls.__radio_label_checked
        rad, label = find_elements(driver, path, False)[:2]
        return Checkbox(rad, label)

    @classmethod
    def find_all(cls, driver, checked=False):
        path = cls.__radio_label_path if not checked else cls.__radio_label_checked
        radios_labels = find_elements(driver, path, False)
        arr = []
        for rad, label in zip(radios_labels[::2], radios_labels[1::2]):
            arr.append(Checkbox(rad, label)) 
        return arr
    
    def value(self):
        return self.rad.value
    @property
    def text(self):
        return self.label.text
    def click(self):
        return self.label.click()
    def is_selected(self):
        return self.rad.is_selected()
    

class Select2(Select):
    __paths = {
        'select_span': 'XP: ./following::span[1]',
        'dropdown': 'XP: //span[contains(@class, "select2-container") and contains(@style, "position: absolute")]',
        'dropdown_option': 'XP: .//li[not(@aria-selected="true" or @aria-disabled="true")]'
    }
    def __init__(self, el):
        self.select2 = find_element(el, self.__paths['select_span'])
        return super().__init__(el)
    def options_length(self, selected = False, disabled = False):
        script = f"""
            let elements = Array.from(document.querySelectorAll('li'));
            return elements.filter(el => !(el.getAttribute('aria-selected') === '{str(not selected).lower()}' || el.getAttribute('aria-disabled') === '{str(not disabled).lower()}')).length;
        """
        return self.dropdown.wrapped_element._parent.execute_script(script)
    @property
    def dropdown(self):
        return self.open_dropdown()
    def open_dropdown(self):
        if (dd := find_element_or_none(self._el, self.__paths['dropdown'])) is None:
            self.select2.click()
            dd = find_element(self._el, self.__paths['dropdown'])
        return dd
    def select_by_index(self, index):
        opt = find_element(self.dropdown, self.__paths['dropdown_option'] + f'[{index+1}]')
        opt_text = opt.text
        opt.click()
        return opt_text
    def select_by_visible_text(self, text):
        opt = find_element(self.dropdown, self.__paths['dropdown_option'] + f'[@title="{text}"]')
        opt_text = opt.text
        opt.click()
        return opt_text
    def select_random(self):
        return self.select_by_index(randint(0, self.options_length()-1))

class Link:
    def __init__(self, cell):
        self.text = cell.text
        self.link = find_element(cell, 'TA: a').get_attribute('href')