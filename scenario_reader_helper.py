def find_preference(settings: list[str], preference: str):
    for setting in settings:
        name, dependancies = get_dependencies(setting)
        if preference == name:
            return dependancies
    raise ValueError(f'The preference {preference} does not exist on this settings: {settings}')
def preference_exists(settings: list[str], preference: str):
    for setting in settings:
        if setting.startswith(preference):
            return True
    return False

def get_dependencies(preference: str):
    main, *dependencies = preference.split('|')
    dependencies_dict = {}
    for dependency in dependencies:
        key, value = dependency.split(':')
        if key in dependencies_dict:
            dependencies_dict[key].append(value)
        else:
            dependencies_dict[key] = [value]

    return main, dependencies_dict