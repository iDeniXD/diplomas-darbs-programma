from datetime import datetime
import json
from copy import deepcopy
import logging

class Template: pass

def log(parent, what, message):
    full_message = (
        f"Error in {what} "
        f"of {parent} "
        f"Error message: {message}")
    print(full_message)
    logging.error(full_message)

def initialize():
    with open('errors.log', 'a') as f:
        f.write(f'\n------ {datetime.now().isoformat()} ------\n')
        
    logging.basicConfig(filename='errors.log', level=logging.ERROR, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.error('test')
    logging.error('test')
    logging.error('test')

def try_fn(callback, *args, try_fn_parent = '', **kwargs):
    try:
        return callback(*args, **kwargs) 
    except Exception as e:
        # TODO: log errors
        full_message = (
            f'Error in calling {callback.__name__} '
            f'of {try_fn_parent} ' if try_fn_parent else ''
            'with args: \n[' + ", ".join(str(arg) for arg in args) + ']\n'
            'and kwargs: \n' + json.dumps(kwargs, indent=2, default=lambda a: str(type(a))) +'\n'
            f'Error message: {e}'
        )
    print(full_message)
    logging.error(full_message)

def assert_equals(parent, left, right=None, custom_message=None):
    try:
        if (right is not None):
            assert left == right #@IgnoreException
        else:
            assert left #@IgnoreException
        return True
    except AssertionError:
        # TODO: log errors
        full_message = (
            f'Error in asserting {left}{f" == {right}" if right is not None else ""} ' +
            f'of {parent} ' if parent else '')
        if (custom_message):
            full_message += f'\nComment: {custom_message}'
        print(full_message)
        logging.error(full_message)
        return False

def reproduce(originals: list, changes: list):

    """
    changes looks like this:
    {[
        {
            old_field1: value1,
            old_field2: value2,
            new_field1: value11,
            new_field2: value22,
            xStatus: edited
        },
        {
            old_field1: value1,
            old_field2: value2,
            xStatus: deleted
        },
        {
            new_field1: value11,
            new_field2: value22,
            xStatus: added
        },
    ]}
    """
    def find(records, record_to_find: list[tuple[str, str]]):
        for record in records:
            record_as_dict = vars(record)
            for key, value in record_to_find:
                if record_as_dict.get(key) != value:
                    break
            else:
                return record
        raise Exception('History does not correspond to the original records')
    for change in changes:
        if change.xStatus == 'added':
            t = Template()
            for key, value in vars(change).items():
                if (key == 'xStatus'):
                    continue
                setattr(t, key[4:], value)
            originals.append(t)
            continue

        # get old fields to search by. 
        # {old_field1: value1, new_field1: value11} => {field1: value1}
        old_fields = [(key[4:], value) for key,value in vars(change).items() if key.startswith('old_')]
        
        if change.xStatus == 'deleted':
            originals.remove(find(originals, old_fields))
            continue
        if change.xStatus == 'edited':
            original = find(originals, old_fields)
            # iterate through each old field key, find a new value using it, and assign it 
            for key, new_value in {key: getattr(change, 'new_'+key) for key, _ in old_fields}.items():
                setattr(original, key, new_value)
    return originals

def assert_records_changed(parent, originals: list, changes: list, actuals: list):
    listify = lambda r: [r] if type(r) != list else r
    originals = listify(originals) # for vertical tables
    changes = listify(changes) # for vertical tables
    actuals = listify(actuals) # for vertical tables
    



    local_actuals = reproduce(deepcopy(originals), changes)
    try:
        for actual in actuals:
            assert_equals(parent, actual in local_actuals, custom_message=f'A record with field {vars(actual)} was expected')
    except:
        # TODO: log errors
        print(
            f'Error in finding {vars(actual)} \n\nin \n\n{local_actuals}' +
            f' of {parent} ' if parent else '')
        