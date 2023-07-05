import pytest
import os

if __name__ == '__main__':
    # xml_report_path = './report/xml/'
    # html_report_path = './report/html/'
    # pytest.main(['-s', '-q', '--alluredir', xml_report_path, './TestCase/mall/test_means.py'])
    # cmd = "allure generate %s -o %s --clean" % (xml_report_path, html_report_path)
    pytest.main(['--clean-alluredir', './TestCase/mall/test_means.py', "-s", "--alluredir", "./report/tmp"])
    os.system("allure serve ./report/tmp")
