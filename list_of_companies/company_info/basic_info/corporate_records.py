from classes.classes import Table
from driver_helper import find_element
from loggers.error_logger import assert_equals
import globals as g


paths = {
    'name_path': 'TA: h1',
    'government_corporate_name': 'XP: .//td[text()="Corporate Name"]/following-sibling::td/div[@class="show-mode"]'
}

old_name = None
def readName(parent: str, table: Table):
    global old_name
    # cannot split by ' / ', because name might be absent: '/ America' will be formatted into ['/ America']
    old_name = find_element(g.driver, paths['name_path']).text.split('/')[0].strip()
def checkName(parent: str, table: Table, records: list):
    global old_name
    gov_corp_name = find_element(g.driver, paths['government_corporate_name']).text
    if (gov_corp_name):
        same_name = find_element(g.driver, paths['name_path']).text.split('/')[0].strip()
        assert_equals(
            parent+f'. Asserting that company <h1> name was not changed after Corporate Records change, since the Government Records "Corporate Name" field is present',
            old_name, 
            same_name
        )
    else:
        records = vars(records)

        old_record_name = records[next(val for val in records if val.endswith('Corporate Name') and val.startswith('old'))]
        new_record_name = records[next(val for val in records if val.endswith('Corporate Name') and val.startswith('new'))]

        new_name = find_element(g.driver, paths['name_path']).text.split(' / ')[0]
        assert_equals(
            parent+f'. Asserting that company <h1> name was the same as the Corporate Record field "Corporate Record" old value',
            old_name, 
            old_record_name
        )
        assert_equals(
            parent+f'. Asserting that company <h1> name changes along with the Corporate Record change "Corporate Record" field change',
            new_name, 
            new_record_name
        )
