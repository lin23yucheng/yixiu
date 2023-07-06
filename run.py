import pytest
import os

if __name__ == '__main__':

    pytest.main(['--clean-alluredir', './testcase', "-s", "--alluredir", "./report/tmp"])
    os.system("allure serve ./report/tmp")
