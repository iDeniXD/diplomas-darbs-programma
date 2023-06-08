import re
from classes.Inputs import Checkbox
from driver_helper import find_element

from loggers.error_logger import assert_equals, log, try_fn
import xpaths as x


last_failed_not_found_parent = ''
def not_found(parent, rule): 
    global last_failed_not_found_parent
    if (last_failed_not_found_parent == parent): return
    last_failed_not_found_parent = parent
    log(parent, f'executing {rule} rule', 'such rule does not exist')

last_failed_base_only_parent = ''
def base_only(parent, options_length, get_option, *_, **__):
    # Make sure the first five options (that is enough to detect an error) are all base activities, not sub- ones
    global last_failed_base_only_parent
    # If the rule failed on this parent already, skip checking again
    # Otherwise, keep checking unless failed 
    if (last_failed_base_only_parent == parent): return

    pattern = r"^[A-Z]\. - .*|Select Activity$"
    for i in range(5): 
        opt = get_option(i)
        if not assert_equals(parent+f'@base_only. Failed on option: {opt.text}', re.match(pattern, opt.text)):
            last_failed_base_only_parent = parent
            return
        
last_failed_sub_activity_parent = ''
def sub_activity(parent, cell, options_length, get_option):
    # Goes through the first, some middle and the last sub activities and ensure they all start with the code selected in Base Activity select
    global last_failed_sub_activity_parent
    # If the rule failed on this parent already, skip checking again
    # Otherwise, keep checking unless failed 
    if (last_failed_sub_activity_parent == parent): return

    paths = {
        'base_activity_span': "XP: ./preceding::td[1]/span[contains(@class,'select2')]//span[contains(@class, 'rendered')]"
    }

    base_title = find_element(cell, paths['base_activity_span']).get_attribute('title')

    if not assert_equals(parent+f'@sub_activity. Failed on asserting if there are any options. Base activity selected: {base_title}', options_length):
        # last_failed_sub_activity_parent = parent // the actual test could not happen, there was no options
        return

    # split options into 5 parts, go through each first option, and make sure to take the very last element into iteration, too
    for i in set(range(0, options_length, options_length//5 or 1)) | {options_length-1}:
        opt = get_option(i)
        if not assert_equals(parent+f'@sub_activity. Failed on option: {opt.text}. Base activity selected: {base_title}', opt.text.startswith(base_title[:base_title.index(' ')])):
            last_failed_sub_activity_parent = parent
            return
        
last_failed_toggle_input_parent = ''
def toggle_input(parent, cell, checkboxes: list[Checkbox], on_value):
    # Goes through the first, some middle and the last sub activities and ensure they all start with the code selected in Base Activity select
    global last_failed_toggle_input_parent
    # If the rule failed on this parent already, skip checking again
    # Otherwise, keep checking unless failed 
    if (last_failed_toggle_input_parent == parent): return

    checkbox = {cb.text: cb for cb in checkboxes}[on_value]

    for _ in range(2): # enable, disable
        checkbox.click()
        if not assert_equals(parent+f'@toggle_input. Failed in asserting that input is displayed when the checkbox is {"" if on_value else "not "}clicked', find_element(cell, x.table_paths['cell_input']).is_displayed(), checkbox.is_selected()):
            last_failed_toggle_input_parent = parent
            checkbox.click()
            return

        

def check_rules(parent, rules, entity: dict):
    for rule in rules:
        is_rule, func = rule.split(':')
        is_rule = is_rule == 'rule'
        if (not is_rule):
            continue
        try_fn(
            globals().get(func, lambda *_, rule=rule, parent=parent, **__: not_found(parent, rule)),
            parent,
            try_fn_parent=parent+'@rule:'+rule,
            **entity
        )

def get_rule_checkers(functions):
    events = {
        'options_read': ['base_only', 'sub_activity'], # (get_option, options_length, cell)
        'checkbox_retrieve': ['toggle_input']
        # ...
    }
    requested_callbacks = {}
    for event, callbacks in events.items():
        requested_event_callbacks = []
        for func in functions:
            if func in callbacks:
                requested_event_callbacks.append(globals()[func])
            else:
                requested_event_callbacks.append(lambda parent, rule=func, **__: not_found(parent, rule))
        requested_callbacks[event] = requested_event_callbacks
    return requested_callbacks
    
    


def on(event, callbacks, parent, **kwargs):
    for cb in callbacks.get(event, []):
        try_fn(
            cb,
            parent,
            try_fn_parent=parent+'@rule:'+cb.__name__,
            **kwargs
        )
