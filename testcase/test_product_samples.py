import re
import requests
import pytest
import allure

from common import Assert
from api import api_login, api_product_samples

assertions = Assert.Assertions()
token = api_login.ApiLogin().login()
code = api_login.code
manageid = api_login.manageid
productSampleId = 0


# 场景：学习样例的增查删
@allure.feature("场景：学习样例增改删")
class Test_product_samples:
    @allure.story("新增学习样例")
    def test_samples_add(self):
        addData = api_product_samples.ApiProductSamples().samples_add(token, code, manageid)
        addData_dict = addData.json()
        assertions.assert_code(addData.status_code, 200)
        assertions.assert_in_text(addData_dict['msg'], '成功')
        # print(addData_dict)

    @allure.story("查询学习样例提取刚新增的ID值")
    def test_samples_query(self):
        queryData = api_product_samples.ApiProductSamples().samples_query(token, code, manageid)
        queryData_dict = queryData.json()
        assertions.assert_code(queryData.status_code, 200)
        assertions.assert_in_text(queryData_dict['msg'], '成功')
        query_data_text = queryData.text
        # print(queryData_dict)
        # data_list = queryData_dict['data']
        # list_list = data_list['list']
        # number_list = list_list[0]
        # global productSampleId
        # productSampleId = number_list['productSampleId']

        # 正则提取productSampleId值
        global productSampleId
        productSampleId = re.search('"productSampleId":"(.*?)"', query_data_text).group(1)

    @allure.story("删除刚新增的学习样例")
    def test_samples_delete(self):
        deleteData = api_product_samples.ApiProductSamples().samples_delete(token, code, manageid, productSampleId)
        deleteData_dict = deleteData.json()
        assertions.assert_code(deleteData.status_code, 200)
        assertions.assert_in_text(deleteData_dict['msg'], '成功')
        # print(deleteData_dict)


if __name__ == '__main__':
    pass
