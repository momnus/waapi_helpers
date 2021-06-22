from setuptools import setup

from waapi_helpers.proj_info import *

setup(
    name='waapi_helpers',
    version=get_version(),
    packages=['waapi_helpers'],
    url=get_homepage(),
    license='MIT',
    author=get_author(),
    author_email='login@eugn.ch',
    description=get_short_description(),
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    platforms='any',
)
