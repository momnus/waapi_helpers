import os
import subprocess
import time
from unittest import TestCase

from waapi import WaapiClient


def _norm_path(path):
    return os.path.normpath(os.path.realpath(path))


def get_res_path():
    return _norm_path(os.path.join(os.path.dirname(__file__), '../res'))


def get_wproj_path():
    return os.path.join(get_res_path(), 'test_wproj', 'test_waapi_helpers.wproj')


def get_wwise_sdk_path():
    assert 'WWISEROOT' in os.environ, 'Environment variable WWISEROOT is undefined'
    return os.environ['WWISEROOT']


def get_wwise_exe():
    return _norm_path(os.path.join(
        get_wwise_sdk_path(), 'Authoring\\x64\\Release\\bin\\Wwise.exe'))


def get_wwise_cli_exe():
    return _norm_path(os.path.join(
        get_wwise_sdk_path(), 'Authoring\\x64\\Release\\bin\\WwiseConsole.exe'))


# ------------------------------------------

class WaapiTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen([
            get_wwise_cli_exe(), 'waapi-server', get_wproj_path()
        ])
        cls.client = None

        while cls.client is None or not cls.client.is_connected():
            if cls.client is not None:
                cls.client.disconnect()
                time.sleep(0.5)
            cls.client = WaapiClient()
            time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if cls.client is not None:
            cls.client.disconnect()
            cls.client = None
        cls.proc.kill()
        cls.proc = None
