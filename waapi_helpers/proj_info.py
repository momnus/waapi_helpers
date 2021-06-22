def get_author() -> str:
    return 'Eugene Cherny'


def get_homepage() -> str:
    return 'https://github.com/ech2/waapi_helpers'


def get_short_description() -> str:
    return 'A small utility function library for working with Wwise Authoring API'


def get_long_description() -> str:
    from os.path import join, dirname
    with open(join(dirname(__file__), '..', 'README.md'), 'r') as f:
        return f.read()


def get_version() -> str:
    return '0.1.0'  # TODO
