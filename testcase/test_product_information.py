"""
产品资料接口自动化流程
"""
import re
import pytest
import allure
import time
from common import Assert
from api import api_login
from common.Request_Response import ApiClient

assertions = Assert.Assertions()
env = api_login.url
token = api_login.ApiLogin().login()
code = api_login.code
manageid = api_login.manageid
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())

# 初始化API客户端
base_headers = {
    "Authorization": token,
    "Miai-Product-Code": code,
    "Miaispacemanageid": manageid
}
client = ApiClient(base_headers=base_headers)


@allure.feature("场景：产品资料增删改查")
class Test_product_information:
    @classmethod
    def setup_class(cls):
        """类级别初始化：上传图片并获取 data_value（仅执行一次）"""
        cls.upload_pictures()
        cls.productDataId = None

    @classmethod
    def upload_pictures(cls):
        """上传PDF文件（类方法）"""
        url = env + "/miai/brainstorm/knowledgeproductdata/uploadData"
        file_path = r"C:\Users\admin\Desktop\项目文件\一休云\上传使用\Xftp7_en.PDF"

        with allure.step("上传测试文件"):
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = client.post(url, files=files)

            response_data = response.json()
            assertions.assert_code(response.status_code, 200)
            assertions.assert_in_text(response_data['msg'], '成功')
            cls.data_value = response_data['data']
            allure.attach(
                f"上传成功文件路径：{cls.data_value}",
                name="Upload Result",
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.story("新增产品资料")
    def test_information_add(self):
        url = env + "/miai/brainstorm/knowledgeproductdata/addData"
        payload = {
            "name": f"接口自动化_{time_str}",
            "detail": "接口自动化",
            "seatIsUse": 1,
            "dataPath": self.data_value,
            "type": "PDF"
        }

        with allure.step("执行新增操作"):
            response = client.post(url, json=payload)
            response_data = response.json()

            assertions.assert_code(response.status_code, 200)
            assertions.assert_in_text(response_data['msg'], '成功')

    @allure.story("查询产品资料提取刚新增的ID值")
    def test_information_query(self):
        url = env + "/miai/brainstorm/knowledgeproductdata/queryPage"
        payload = {
            "data": {"name": f"接口自动化_{time_str}"},
            "page": {"pageIndex": 1, "pageSize": 100}
        }

        with allure.step("执行查询操作"):
            response = client.post(url, json=payload)
            response_data = response.json()

            assertions.assert_code(response.status_code, 200)
            assertions.assert_in_text(response_data['msg'], '成功')

            # 提取productDataId
            match = re.search('"productDataId":"(.*?)"', response.text)
            if match:
                self.__class__.productDataId = match.group(1)
                allure.attach(
                    f"提取到的productDataId: {self.productDataId}",
                    name="Extracted ID",
                    attachment_type=allure.attachment_type.TEXT
                )
            else:
                pytest.fail("未找到 productDataId")

    @allure.story("修改刚新增的产品资料")
    def test_information_update(self):
        assert self.productDataId is not None, "未获取到 productDataId"
        url = env + f"/miai/brainstorm/knowledgeproductdata/updateData"
        payload = {
            "productDataId": self.productDataId,
            "name": f"接口自动化_修改_{time_str}",
            "type": "PDF",
            "seatIsUse": 0,
            "detail": f"接口_修改_{time_str}",
            "dataPath": self.data_value,
            "grid_order": 1
        }

        with allure.step("执行修改操作"):
            response = client.post(url, json=payload)
            response_data = response.json()

            assertions.assert_code(response.status_code, 200)
            assertions.assert_in_text(response_data['msg'], '成功')

    @allure.story("删除刚新增的产品资料")
    def test_information_delete(self):
        assert self.productDataId is not None, "未获取到 productDataId"
        url = env + f"/miai/brainstorm/knowledgeproductdata/delete/{self.productDataId}"

        with allure.step("执行删除操作"):
            response = client.post(url)
            response_data = response.json()

            assertions.assert_code(response.status_code, 200)
            assertions.assert_in_text(response_data['msg'], '成功')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--alluredir=./allure-results'])