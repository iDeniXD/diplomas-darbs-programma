from random import choice, getrandbits, randint, sample
import string
from classes.Inputs import Checkbox, Link, Radio
from driver_helper import find_element, find_element_or_none, find_elements, find_elements_gen
from rules import  get_rule_checkers, on
import xpaths as x
from scenario_reader_helper import get_dependencies
from selenium.webdriver.support.ui import Select


def parser(type):
    type, dependencies = get_dependencies(type)
    match(type):
        case 'select2m':
            return lambda cell: [s.text for s in find_elements(cell, x.table_paths['tags'])]
        # case 'null':
        #     pass
        case 'textarea':
            return lambda cell: cell.get_attribute('value')
        case 'link':
            return lambda cell: Link(cell)
        case _:
            return lambda cell: cell.text
        
def value_changer(type, parent):
    def count_options(edit_div):
            script = """
                let elements = Array.from(document.querySelectorAll('span.select2-container--open[style*="position: absolute;"] li'));
                return elements.filter(el => !(el.getAttribute('aria-selected') === 'true' || el.getAttribute('aria-disabled') === 'true')).length;
            """
            return edit_div.wrapped_element._parent.execute_script(script)
    def option_getter(edit_div, select2_paths):
        def callback(index):
            return find_element(edit_div, select2_paths['available_tags']+f'[{index+1}]')
        return callback
    
    def change_select2_multiple(cell, *_):
        # FIXME: slow
        select2_paths = x.table_paths['select2']
        edit_div = find_element(cell, cell.edit_div_path)

        # selected tags are refreshed with each click
        # TODO: change this
        chosens = find_elements_gen(edit_div, select2_paths['selected_tags'])
        for chosen in chosens:
            chosen.click() # deselect all



        select = find_element(edit_div, select2_paths['input'])
        if (find_element_or_none(edit_div, select2_paths['block']) is None):
            select.click()


        # options_len = len(find_elements(edit_div, select2_paths['available_tags'])) # TODO: change to JS code
        options_len = count_options(edit_div)
        first = True
        selected = []
        to_select_indexes = [0] + sample(range(1, options_len), randint(0, 5))
        get_option = option_getter(edit_div, select2_paths)
        for option_index in to_select_indexes: # choose some random options (the first one will be always selected)
            if first or bool(getrandbits(1)):
                option = get_option(option_index)
                selected.append(option.text)
                option.click()
                select.click()
            first = False
        select.click() # close dropdown, so that it does not cover other elements
        return selected
    def change_select2(cell, *_):
        select2_paths = x.table_paths['select2']
        edit_div = find_element(cell, cell.edit_div_path)
        select = find_element(edit_div, select2_paths['input'])
        select.click()
        get_option = option_getter(edit_div, select2_paths)
        options_length = count_options(edit_div)
        on('options_read', rule_callbacks, parent+'.change_select2', **{'get_option': get_option, 'options_length': options_length, 'cell': cell})
        if options_length == 0:
            return ''
        option = get_option(randint(0,options_length-1))

        t = option.text
        option.click()
        return t
    def change_select2_taggable(specify_option):
        def changer(cell, count):
            while True:
                selected = change_select2(cell)
                if count != 0:
                    break
                if selected == specify_option:
                    return f'{selected}: {change_text(cell)}'
            return selected
        return changer
    def change_date(cell, *_):
        datepicker_paths = x.table_paths['datepicker']
        edit_div = find_element(cell, cell.edit_div_path)
        inpt = find_element(edit_div, datepicker_paths['input'])
        inpt.click()
        available_dates = find_elements(edit_div, datepicker_paths['available_dates'])
        available_dates[randint(0, len(available_dates)-1)].click()
        return inpt.get_attribute('value')
    def change_cb(specify_option):
        def changer(cell, *_):
            edit_div = find_element(cell, cell.edit_div_path)
            cbs = Checkbox.find_all(edit_div)
            on('checkbox_retrieve', rule_callbacks, parent+'.change_bool', **{'cell': cell, 'checkboxes': cbs, 'on_value': specify_option})
            res = []
            for cb in cbs:
                if bool(getrandbits(1)): cb.click()
                if not cb.is_selected(): continue

                res.append(cb.text)
                if (cb.text == specify_option):
                    res[-1] += f' ({change_text(cell)})'
            return res
        return changer
    def change_bool(specify_option):
        cb_changer = change_cb(specify_option)
        def changer(cell, *_):
            if (res := cb_changer(cell, *_)):
                res = res[0]
            else:
                return 'No'
            if (specify_option in res):
                return res.replace(specify_option, 'Yes')
            else:
                return 'Yes'
        return changer


    def change_radio(cell, *_):
        edit_div = find_element(cell, cell.edit_div_path)
        radios = Radio.find_all(edit_div)
        radios[randint(0,len(radios)-1)].click()


    def change_text(cell, *_):
        edit_div = find_element(cell, cell.edit_div_path)
        inpt = find_element(edit_div, cell.input_path)
        inpt.clear()
        letters = string.ascii_lowercase
        inpt.send_keys(text := ''.join(choice(letters) for _ in range(10)))
        return text

    def change_number_grid(cell, *_):
        edit_div = find_element(cell, cell.edit_div_path)
        table = find_element(edit_div, 'TA: table')
        res = {}
        for tr in find_elements(table, 'TA: tr'):
            key = find_element(tr, 'XP: ./td[2]').text
            inpt = find_element(tr, 'TA: input')
            inpt.clear()
            inpt.send_keys(value := str(randint(0,1000)))
            res[key] = value
        return res
    def change_select(cell, *_): 
        edit_div = find_element(cell, cell.edit_div_path)
        select = Select(find_element(edit_div, x.table_paths['cell_select']))

        random_option = choice(select.options)
        select.select_by_visible_text(random_option.text)

        return random_option.text


                





    type, dependencies = get_dependencies(type)
    rule_callbacks = get_rule_checkers(dependencies.get('rule', []))
    match (type):
        case 'select2m':
            return change_select2_multiple
        case 'select2':
            return change_select2
        case 'select2t':
            return change_select2_taggable(dependencies['specify'][0])
        case 'date':
            return change_date
        case 'cb':
            return change_cb(dependencies.get('specify', [None])[0])
        case 'bool':
            return change_bool(dependencies['specify'][0])
        case 'radio':
            return change_radio
        case 'number-grid':
            return change_number_grid
        case 'select':
            return change_select
        # case 'datetime':
        #     return CustomDateTime.strptime(cell.text, g.datetime_format)
        # case 'null':
        #     pass
        case 'skip':
            return lambda: ""
        case _:
            return change_text
        

def edit_only_parser(type):
    def read_select2_value(cell):
        select = find_element(cell, x.table_paths['select2']['title_span'])
        return select.get_attribute('title')
    def read_input_value(cell):
        inpt = find_element(cell, x.table_paths['cell_input'])
        return inpt.get_attribute('value')
    def read_select2m_value(cell):
        selected_options = find_elements(cell, x.table_paths['select2']['multiple_title_option'], False)
        return [opt.text for opt in selected_options]
    def read_cb(specify_option):
        def reader(cell):
            cbs = Checkbox.find_all(cell, True)
            res = []
            for cb in cbs:
                res.append(cb.text)
                if (cb.is_selected() and cb.text == specify_option):
                    res[-1] += f' ({read_input_value(cell)})'
            return res
        return reader
    def read_bool(specify_option):
        cb_reader = read_cb(specify_option)
        def reader(cell):
            if (cb := cb_reader(cell)):
                cb = cb[0]
            else:
                cb = 'No'
            return cb.replace(f'{specify_option}', 'Yes')
        return reader
    def read_radio(cell, *_):
        radio = Radio.find(cell, True)
        return radio.text
    def read_number_grid(cell, *_):
        table = find_element(cell, 'TA: table')
        res = {}
        for tr in find_elements(table, 'TA: tr'):
            td1, td2 = find_elements(tr, 'TA: td')
            res[td2.text] = find_element(td1, 'TA: input').get_attribute('value')
        return res



    type, dependencies = get_dependencies(type)
    match(type):
        case 'select2':
            return read_select2_value
        case 'select2m':
            return read_select2m_value
        case 'cb':
            return read_cb(dependencies.get('specify', [None])[0])
        case 'bool':
            return read_bool(dependencies.get('specify', [None])[0])
        case 'radio':
            return read_radio
        case 'number-grid':
            return read_number_grid
        case _:
            return read_input_value
