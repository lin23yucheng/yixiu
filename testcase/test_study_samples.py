"""
学习样例接口自动化流程
"""
import re
import pytest
import allure
import time
from common import Assert
from api import api_login
from common.Request_Response import ApiClient
from common.Log import MyLog

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

@allure.feature("场景：学习样例增删改查")
class TestStudySamples:
    @classmethod
    def setup_class(cls):
        """类级别初始化：上传图片并获取 data_value（仅执行一次）"""
        try:
            cls.upload_pictures()
            cls.productSampleId = None
        except Exception as e:
            MyLog.error(f"类初始化失败: {str(e)}")
            pytest.fail(f"类初始化失败: {str(e)}")

    @classmethod
    def upload_pictures(cls):
        """上传图片（类方法）"""
        url = env + "/miai/brainstorm/knowledgeproductsample/upload"
        file_path = "testdata/上传图片.jpg"

        try:
            with allure.step("上传测试文件"):
                with open(file_path, 'rb') as file:
                    files = {'file': file}
                    response = client.post(url, files=files)
                    response_data = response.json()

                    # 简化断言错误处理
                    try:
                        assertions.assert_code(response.status_code, 200)
                    except AssertionError as ae:
                        MyLog.error(f"状态码断言失败: {str(ae)}")
                        MyLog.error(f"上传响应: {response.text}")
                        raise

                    try:
                        assertions.assert_in_text(response_data['msg'], '成功')
                    except AssertionError as ae:
                        MyLog.error(f"响应内容断言失败: {str(ae)}")
                        MyLog.error(f"上传响应: {response.text}")
                        raise

                    cls.data_value = response_data['data']
                    allure.attach(
                        f"上传成功文件路径：{cls.data_value}",
                        name="Upload Result",
                        attachment_type=allure.attachment_type.TEXT
                    )
        except Exception as e:
            MyLog.error(f"文件上传失败: {str(e)}")
            raise

    @pytest.mark.order(1)
    @allure.story("新增学习样例")
    def test_samples_add(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/add"
        payload = {
            "name": f"CS_{time_str}",
            "detail": "接口自动化" + time_str,
            "sampleType": 1,
            "file": [],
            "imgPath": self.data_value,
            "photoId": 2,
            "type": 2
        }

        try:
            with allure.step("执行新增操作"):
                response = client.post(url, json=payload)
                response_data = response.json()

                # 简化断言错误处理
                try:
                    assertions.assert_code(response.status_code, 200)
                except AssertionError as ae:
                    MyLog.error(f"状态码断言失败: {str(ae)}")
                    MyLog.error(f"新增响应: {response.text}")
                    raise

                try:
                    assertions.assert_in_text(response_data['msg'], '成功')
                except AssertionError as ae:
                    MyLog.error(f"响应内容断言失败: {str(ae)}")
                    MyLog.error(f"新增响应: {response.text}")
                    raise
        except Exception as e:
            MyLog.error(f"新增学习样例失败: {str(e)}")
            pytest.fail(f"新增学习样例失败: {str(e)}")

    @pytest.mark.order(2)
    @allure.story("查询学习样例提取刚新增的ID值")
    def test_samples_query(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/page"
        payload = {
            "data": {"name": f"CS_{time_str}", "type": 2},
            "page": {"pageIndex": 1, "pageSize": 10}
        }

        try:
            with allure.step("执行查询操作"):
                response = client.post(url, json=payload)
                response_data = response.json()

                # 简化断言错误处理
                try:
                    assertions.assert_code(response.status_code, 200)
                except AssertionError as ae:
                    MyLog.error(f"状态码断言失败: {str(ae)}")
                    MyLog.error(f"查询响应: {response.text}")
                    raise

                try:
                    assertions.assert_in_text(response_data['msg'], '成功')
                except AssertionError as ae:
                    MyLog.error(f"响应内容断言失败: {str(ae)}")
                    MyLog.error(f"查询响应: {response.text}")
                    raise

                # 提取productSampleId
                match = re.search('"productSampleId":"(.*?)"', response.text)
                if match:
                    self.__class__.productSampleId = match.group(1)
                    MyLog.info(f"成功提取productSampleId: {self.productSampleId}")
                    allure.attach(
                        f"提取到的productSampleId: {self.productSampleId}",
                        name="Extracted ID",
                        attachment_type=allure.attachment_type.TEXT
                    )
                else:
                    error_msg = "未找到 productSampleId"
                    MyLog.error(error_msg)
                    MyLog.error(f"查询响应: {response.text}")
                    pytest.fail(error_msg)
        except Exception as e:
            MyLog.error(f"查询学习样例失败: {str(e)}")
            pytest.fail(f"查询学习样例失败: {str(e)}")

    @pytest.mark.order(3)
    @allure.story("修改刚新增的学习样例")
    def test_samples_update(self):
        try:
            assert self.productSampleId is not None, "未获取到 productSampleId"
            url = env + f"/miai/brainstorm/knowledgeproductsample/update/{self.productSampleId}"
            payload = {
                "productSampleId": self.productSampleId,
                "spaceManageId": manageid,
                "productCode": code,
                "name": "CS_update_" + time_str,
                "sampleType": 2,
                "detail": "接口自动化update_" + time_str,
                "imgPath": self.data_value,
                "photoId": 5,
                "type": 2,
                "version": 0,
                "jsonInfo": 'null',
                "frameNum": 'null',
                "grid_order": 1,
                "file": [{}]
            }

            with allure.step("执行修改操作"):
                response = client.post(url, json=payload)
                response_data = response.json()

                # 简化断言错误处理
                try:
                    assertions.assert_code(response.status_code, 200)
                except AssertionError as ae:
                    MyLog.error(f"状态码断言失败: {str(ae)}")
                    MyLog.error(f"修改响应: {response.text}")
                    raise

                try:
                    assertions.assert_in_text(response_data['msg'], '成功')
                except AssertionError as ae:
                    MyLog.error(f"响应内容断言失败: {str(ae)}")
                    MyLog.error(f"修改响应: {response.text}")
                    raise
        except Exception as e:
            MyLog.error(f"修改学习样例失败: {str(e)}")
            pytest.fail(f"修改学习样例失败: {str(e)}")

    @pytest.mark.order(4)
    @allure.story("删除刚新增的学习样例")
    def test_samples_delete(self):
        try:
            assert self.productSampleId is not None, "未获取到 productSampleId"
            url = env + f"/miai/brainstorm/knowledgeproductsample/delete/{self.productSampleId}"

            with allure.step("执行删除操作"):
                response = client.post(url)
                response_data = response.json()

                # 简化断言错误处理
                try:
                    assertions.assert_code(response.status_code, 200)
                except AssertionError as ae:
                    MyLog.error(f"状态码断言失败: {str(ae)}")
                    MyLog.error(f"删除响应: {response.text}")
                    raise

                try:
                    assertions.assert_in_text(response_data['msg'], '成功')
                except AssertionError as ae:
                    MyLog.error(f"响应内容断言失败: {str(ae)}")
                    MyLog.error(f"删除响应: {response.text}")
                    raise
        except Exception as e:
            MyLog.error(f"删除学习样例失败: {str(e)}")
            pytest.fail(f"删除学习样例失败: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--alluredir=./allure-results'])
