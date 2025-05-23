import re
import requests
import pytest
import allure
from common import Random
from common import Assert
from api import api_login

assertions = Assert.Assertions()
env = api_login.url
token = api_login.ApiLogin().login()
code = api_login.code
manageid = api_login.manageid
num = Random.random_str_abc(5)


@allure.feature("场景：检测样例增删改查")
class Test_check_samples:
    @classmethod
    def setup_class(cls):
        """类级别初始化：上传图片并获取 data_value（仅执行一次）"""
        cls.upload_pictures()  # 调用类方法
        cls.productSampleId = None  # 初始化类属性

    @classmethod
    def upload_pictures(cls):
        """上传图片（类方法，非测试用例）"""
        url = env + "/miai/brainstorm/knowledgeproductsample/upload"
        file_path = r"C:\Users\admin\Desktop\1.png"

        with open(file_path, 'rb') as file:
            files = {'file': file}
            header = {
                "Authorization": token,
                "Miai-Product-Code": code,
                "Miaispacemanageid": manageid
            }
            upload_response = requests.post(url, headers=header, files=files)

        upload_response_dict = upload_response.json()
        assertions.assert_code(upload_response.status_code, 200)
        assertions.assert_in_text(upload_response_dict['msg'], '成功')

        # 使用类属性存储结果（cls 替代 self）
        cls.data_value = upload_response_dict['data']
        print(f"提取的文件路径: {cls.data_value}")

    @allure.story("新增检测样例")
    def test_samples_add(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/add"
        data = {
            "name": f"CS_{num}",
            "detail": "接口自动化" + num,
            "sampleType": 1,
            "file": [],
            "imgPath": self.data_value,  # 使用类属性
            "photoId": 2,
            "type": 1
        }
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_add = requests.post(url, json=data, headers=header)
        rep_samples_add_dict = rep_samples_add.json()
        print(rep_samples_add_dict)
        assertions.assert_code(rep_samples_add.status_code, 200)
        assertions.assert_in_text(rep_samples_add_dict['msg'], '成功')

    @allure.story("查询检测样例提取刚新增的ID值")
    def test_samples_query(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/page"
        data = {"data": {"name": f"CS_{num}", "type": 1}, "page": {"pageIndex": 1, "pageSize": 10}}
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_query = requests.post(url, json=data, headers=header)
        rep_samples_query_dict = rep_samples_query.json()
        print(rep_samples_query_dict)
        assertions.assert_code(rep_samples_query.status_code, 200)
        assertions.assert_in_text(rep_samples_query_dict['msg'], '成功')

        query_data_text = rep_samples_query.text
        # 使用正则表达式提取 productSampleId
        match = re.search('"productSampleId":"(.*?)"', query_data_text)
        if match:
            # 存储到类属性中
            self.__class__.productSampleId = match.group(1)
            print(f"提取到的 productSampleId: {self.productSampleId}")
        else:
            pytest.fail("未找到 productSampleId")

    @allure.story("修改刚新增的检测样例")
    def test_samples_update(self):
        # 确保 productSampleId 已获取
        assert self.productSampleId is not None, "未获取到 productSampleId"

        url = env + f"/miai/brainstorm/knowledgeproductsample/update/{self.productSampleId}"
        data = {
            "productSampleId": self.productSampleId,
            "spaceManageId": manageid,
            "productCode": code,
            "name": "CS_update_" + num,
            "sampleType": 2,
            "detail": "接口自动化update_" + num,
            "imgPath": self.data_value,
            "photoId": 5,
            "type": 1,
            "version": 0,
            "jsonInfo": 'null',
            "frameNum": 'null',
            "grid_order": 1,
            "file": [{}]
        }
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_update = requests.post(url, json=data, headers=header)
        rep_samples_update_dict = rep_samples_update.json()
        print(rep_samples_update.text)
        assertions.assert_code(rep_samples_update.status_code, 200)
        assertions.assert_in_text(rep_samples_update_dict['msg'], '成功')

    @allure.story("删除刚新增的检测样例")
    def test_samples_delete(self):
        # 确保 productSampleId 已获取
        assert self.productSampleId is not None, "未获取到 productSampleId"

        url = env + f"/miai/brainstorm/knowledgeproductsample/delete/{self.productSampleId}"
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_delete = requests.post(url, headers=header)
        print(rep_samples_delete.text)
        delete_data_dict = rep_samples_delete.json()
        assertions.assert_code(rep_samples_delete.status_code, 200)
        assertions.assert_in_text(delete_data_dict['msg'], '成功')


# -------------------------------------------------------------------#

@allure.feature("场景：学习样例增删改查")
class Test_study_samples:
    @classmethod
    def setup_class(cls):
        """类级别初始化：上传图片并获取 data_value（仅执行一次）"""
        cls.upload_pictures()  # 调用类方法
        cls.productSampleId = None  # 初始化类属性

    @classmethod
    def upload_pictures(cls):
        """上传图片（类方法，非测试用例）"""
        url = env + "/miai/brainstorm/knowledgeproductsample/upload"
        file_path = r"C:\Users\admin\Desktop\项目文件\一休云\上传使用\上传图片\图片\555.jpg"

        with open(file_path, 'rb') as file:
            files = {'file': file}
            header = {
                "Authorization": token,
                "Miai-Product-Code": code,
                "Miaispacemanageid": manageid
            }
            upload_response = requests.post(url, headers=header, files=files)

        upload_response_dict = upload_response.json()
        assertions.assert_code(upload_response.status_code, 200)
        assertions.assert_in_text(upload_response_dict['msg'], '成功')

        # 使用类属性存储结果（cls 替代 self）
        cls.data_value = upload_response_dict['data']
        print(f"提取的文件路径: {cls.data_value}")

    @allure.story("新增学习样例")
    def test_samples_add(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/add"
        data = {
            "name": f"CS_{num}",
            "detail": "接口自动化" + num,
            "sampleType": 1,
            "file": [],
            "imgPath": self.data_value,  # 使用类属性
            "photoId": 2,
            "type": 2
        }
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_add = requests.post(url, json=data, headers=header)
        rep_samples_add_dict = rep_samples_add.json()
        print(rep_samples_add_dict)
        assertions.assert_code(rep_samples_add.status_code, 200)
        assertions.assert_in_text(rep_samples_add_dict['msg'], '成功')

    @allure.story("查询学习样例提取刚新增的ID值")
    def test_samples_query(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/page"
        data = {"data": {"name": f"CS_{num}", "type": 2}, "page": {"pageIndex": 1, "pageSize": 10}}
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_query = requests.post(url, json=data, headers=header)
        rep_samples_query_dict = rep_samples_query.json()
        print(rep_samples_query_dict)
        assertions.assert_code(rep_samples_query.status_code, 200)
        assertions.assert_in_text(rep_samples_query_dict['msg'], '成功')

        query_data_text = rep_samples_query.text
        # 使用正则表达式提取 productSampleId
        match = re.search('"productSampleId":"(.*?)"', query_data_text)
        if match:
            # 存储到类属性中
            self.__class__.productSampleId = match.group(1)
            print(f"提取到的 productSampleId: {self.productSampleId}")
        else:
            pytest.fail("未找到 productSampleId")

    @allure.story("修改刚新增的学习样例")
    def test_samples_update(self):
        # 确保 productSampleId 已获取
        assert self.productSampleId is not None, "未获取到 productSampleId"

        url = env + f"/miai/brainstorm/knowledgeproductsample/update/{self.productSampleId}"
        data = {
            "productSampleId": self.productSampleId,
            "spaceManageId": manageid,
            "productCode": code,
            "name": "CS_update_" + num,
            "sampleType": 2,
            "detail": "接口自动化update_" + num,
            "imgPath": self.data_value,
            "photoId": 5,
            "type": 2,
            "version": 0,
            "jsonInfo": 'null',
            "frameNum": 'null',
            "grid_order": 1,
            "file": [{}]
        }
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_update = requests.post(url, json=data, headers=header)
        rep_samples_update_dict = rep_samples_update.json()
        print(rep_samples_update.text)
        assertions.assert_code(rep_samples_update.status_code, 200)
        assertions.assert_in_text(rep_samples_update_dict['msg'], '成功')

    @allure.story("删除刚新增的学习样例")
    def test_samples_delete(self):
        # 确保 productSampleId 已获取
        assert self.productSampleId is not None, "未获取到 productSampleId"

        url = env + f"/miai/brainstorm/knowledgeproductsample/delete/{self.productSampleId}"
        header = {
            "content-type": "application/json",
            "Authorization": token,
            "Miai-Product-Code": code,
            "Miaispacemanageid": manageid
        }
        rep_samples_delete = requests.post(url, headers=header)
        print(rep_samples_delete.text)
        delete_data_dict = rep_samples_delete.json()
        assertions.assert_code(rep_samples_delete.status_code, 200)
        assertions.assert_in_text(delete_data_dict['msg'], '成功')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--alluredir=./allure-results'])
