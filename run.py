import pytest
import os

if __name__ == '__main__':

    pytest.main(['--clean-alluredir', './testcase/test_one_samples.py', "-s", "--alluredir", "./report/tmp"])
    os.system("allure serve ./report/tmp")
