from classes.classes import Table
from driver_helper import find_element
from loggers.error_logger import assert_equals
import globals as g


paths = {
    'name_path': 'TA: h1'
}

old_name = None
def readName(parent: str, table: Table):
    global old_name
    old_name = find_element(g.driver, paths['name_path']).text.split(' / ')[0]
def checkName(parent: str, table: Table, records: list):
    global old_name
    new_name = find_element(g.driver, paths['name_path']).text.split(' / ')[0]
    records = vars(records)

    old_record_name = records[next(val for val in records if val.endswith('Corporate Name') and val.startswith('old'))]
    new_record_name = records[next(val for val in records if val.endswith('Corporate Name') and val.startswith('new'))]

    if (old_record_name): # previously was null, hence the name could be anything
        assert_equals(
            parent+f'. Asserting that company <h1> name was the same as the Government Record field "Corporate Record" old value',
            old_name, 
            old_record_name
        )
    assert_equals(
        parent+f'. Asserting that company <h1> name changes along with the Government Record change "Corporate Record" field change',
        new_name, 
        new_record_name
    )