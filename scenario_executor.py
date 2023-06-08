from driver_helper import find_element, follow_path, get_locator
from loggers.error_logger import try_fn
from tables.tables_helper import test_table
from classes.classes import Template, runnable_dict
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_steps(driver, steps: runnable_dict, parent: str, full_route: list):
    tmp = Template()
    for step_key in steps.keys():
        if (steps[step_key].get('skip')): continue
        # TODO: what happens if try_fn fails?
        # TODO: full_route .copy() required?
        res = try_fn(run_step, driver, steps[step_key], parent+('.' if parent else '')+step_key, full_route.copy(), tmp, try_fn_parent=parent)
        try_fn(setattr, tmp, step_key, res, try_fn_parent=parent)
    return tmp

def run_step(driver, settings: runnable_dict, parent, full_route: list[str], current_step_result: Template):
    follow_path(driver, settings.get('route'))
    full_route += settings.get('route') or []
    def find_index_or_zero(arr: list, lam):
        for i, el in enumerate(arr):
            if (lam(el)):
                return i
        return 0
    full_route = full_route[find_index_or_zero(full_route, lambda route: route.startswith('link: ')):]
    # settings.run('onLoad', parent, driver) # TODO: set WebDriverWait on page load
    
    if ('working_area' in settings):
        driver = find_element(driver, settings.get('working_area'))

    match settings.get('type'):
        case 'table':
            tmp = test_table(driver, settings, parent, full_route, current_step_result)
        case 'documents_storage':
            tmp = read_documents_storage(driver, settings, parent)
        case _:
            tmp = run_steps(driver, settings.get('steps', {}), parent, full_route)

    settings.run('onFinish', parent, driver, tmp)

    return tmp

