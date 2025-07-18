"""
产品资料接口自动化流程
"""
import re
import pytest
import allure
import time
from common import Assert
from api import api_login, api_product_information
from common.Request_Response import ApiClient
from common.Log import MyLog

assertions = Assert.Assertions()
code = api_login.code
manageid = api_login.manageid
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())

# 初始化全局客户端
base_headers = {
    "Authorization": api_login.ApiLogin().login(),
    "Miai-Product-Code": api_login.code,
    "Miaispacemanageid": api_login.manageid
}
global_client = ApiClient(base_headers=base_headers)


@allure.feature("场景：单产品-产品资料流程")
class TestProductInformation:
    @classmethod
    def setup_class(cls):
        cls.api_product_information = api_product_information.ApiProductInformation(global_client)
        cls.information_name = f"CS_{time_str}"
        cls.productDataId = None

    @allure.story("产品资料增删改查")
    def test_product_samples(self):
        with allure.step(f"步骤1：新增产品资料") as step1:
            information_dataPath = self.api_product_information.upload_pdf()
            response = self.api_product_information.information_add(information_dataPath, self.information_name)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

        with allure.step(f"步骤2：查询产品资料") as step2:
            response = self.api_product_information.information_query(self.information_name)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

            data_list = response_data.get('data', {}).get('list', [])
            for item in data_list:
                if item.get('name') == self.information_name:
                    self.productDataId = item.get('productDataId')
                    break
            else:
                pytest.fail(f"未找到名称为 {self.information_name} 的产品资料")

        with allure.step(f"步骤3：修改产品资料") as step3:
            response = self.api_product_information.information_update(self.productDataId,
                                                                       information_dataPath,
                                                                       f"update_CS_{time_str}")
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')

        with allure.step(f"步骤4：删除产品资料") as step4:
            response = self.api_product_information.information_delete(self.productDataId)
            assertions.assert_code(response.status_code, 200)
            response_data = response.json()
            assertions.assert_in_text(response_data['msg'], '成功')


if __name__ == '__main__':
    pass
