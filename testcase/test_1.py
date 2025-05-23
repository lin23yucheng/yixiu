import re
import requests
import pytest
import allure
from common import Random

from common import Assert
from api import api_login, api_product_samples

assertions = Assert.Assertions()
env = api_login.env
token = api_login.ApiLogin().login()
code = api_login.code
manageid = api_login.manageid
num = Random.random_str_abc(5)


# 场景：检测样例的增查删
@allure.feature("场景：检测样例增删改查")
class Test_check_samples:
    @allure.story("上传检测样例")
    def test_upload_pictures(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/upload"

        file_path = r"C:\Users\admin\Desktop\1.png"

        with open(file_path, 'rb') as file:
            # 构造文件上传参数，键名需与接口期望的键一致
            files = {'file': file}
            header = {"Authorization": token, "Miai-Product-Code": code,
                      "Miaispacemanageid": manageid}

            upload_response = requests.post(url=url, headers=header, files=files)

        upload_response_dict = upload_response.json()

        assertions.assert_code(upload_response.status_code, 200)
        assertions.assert_in_text(upload_response_dict['msg'], '成功')

        data_value = upload_response_dict['data']
        print(f"提取的文件路径: {data_value}")

        global data_value

    @allure.story("新增检测样例")
    def test_samples_add(self):
        # addData = api_product_samples.ApiProductSamples().samples_add(token, code, manageid)
        url = env + "/miai/brainstorm/knowledgeproductsample/add"

        data = {"name": "CS_" + num, "detail": "接口自动化" + num, "sampleType": 1, "file": [],
                "imgPath": data_value,
                "photoId": 2, "type": 1}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_add = requests.post(url=url, json=data, headers=header)
        rep_samples_add_dict = rep_samples_add.json()
        print(rep_samples_add_dict)
        assertions.assert_code(rep_samples_add.status_code, 200)
        assertions.assert_in_text(rep_samples_add_dict['msg'], '成功')

    @allure.story("查询检测样例提取刚新增的ID值")
    def test_samples_query(self):
        # queryData = api_product_samples.ApiProductSamples().samples_query(token, code, manageid)
        url = env + "/miai/brainstorm/knowledgeproductsample/page"

        data = {"data": {"name": "", "type": 2}, "page": {"pageIndex": 1, "pageSize": 10}}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_query = requests.post(url=url, json=data, headers=header)
        rep_samples_query_dict = rep_samples_query.json()
        print(rep_samples_query_dict)
        assertions.assert_code(rep_samples_query.status_code, 200)
        assertions.assert_in_text(rep_samples_query_dict['msg'], '成功')

        # 正则提取productSampleId值
        query_data_text = rep_samples_query.text
        productSampleId = re.search('"productSampleId":"(.*?)"', query_data_text).group(1)
        global productSampleId

    @allure.story("修改刚新增的检测样例")
    def test_samples_update(self):
        url = env + "/miai/brainstorm/knowledgeproductsample/update/" + productSampleId

        data = {
            "productSampleId": productSampleId, "spaceManageId": manageid,
            "productCode": code, "name": "CS_update_" + num, "sampleType": 2, "detail": "接口自动化update_" + num,
            "imgPath": data_value,
            "photoId": 5,
            "type": 1, "version": 0, "jsonInfo": 'null', "frameNum": 'null', "grid_order": 1, "file": [{}]}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_update = requests.post(url=url, json=data, headers=header)
        rep_samples_update_dict = rep_samples_update.json()
        print(rep_samples_update.text)
        assertions.assert_code(rep_samples_update.status_code, 200)
        assertions.assert_in_text(rep_samples_update_dict['msg'], '成功')

    @allure.story("删除刚新增的检测样例")
    def test_samples_delete(self):
        # deleteData = api_product_samples.ApiProductSamples().samples_delete(token, code, manageid, productSampleId)
        url = env + "/miai/brainstorm/knowledgeproductsample/delete/" + productSampleId

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_delete = requests.post(url=url, headers=header)
        print(rep_samples_delete.text)
        deleteData_dict = rep_samples_delete.json()
        assertions.assert_code(rep_samples_delete.status_code, 200)
        assertions.assert_in_text(deleteData_dict['msg'], '成功')


if __name__ == '__main__':
    # pass
    Test_check_samples()
