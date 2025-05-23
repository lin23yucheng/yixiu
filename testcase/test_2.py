import re
import requests
import pytest
import allure

from common import Assert, Read_excel
from api import api_login, api_product_samples

assertions = Assert.Assertions()
env = api_login.url
token = api_login.ApiLogin().login()
code = api_login.code
manageid = api_login.manageid

list_productSampleId = []

# "cs_" + num
samples_name = "cs_" + api_product_samples.num

# 单独执行写..  用run执行写.
excel_list = Read_excel.read_excel_list('./testdata/samples.xls')
ids_list = []
for i in range(len(excel_list)):
    # 删除excel_list中每个小list的最后一个元素,并赋值给ids_pop
    ids_pop = excel_list[i].pop(0)
    print(type(ids_pop))
    # 将ids_pop添加到 ids_list 里面
    ids_list.append(ids_pop)


# 场景：学习样例的增查删
@allure.feature("场景：学习样例增改删")
class Test_product_samples:
    @allure.story('新增学习样例参数化')
    # 新增学习样例参数化
    @pytest.mark.parametrize('name,detail,sampleType,photoId,msg', excel_list, ids=ids_list)
    def test_samples_more_add(self, name, detail, sampleType, photoId, msg):
        if photoId == "":
            photoId = photoId
        else:
            photoId = int(photoId)
        url = env + "/miai/brainstorm/knowledgeproductsample/add"

        data = {"name": name, "detail": detail, "sampleType": sampleType, "file": [],
                "imgPath": "knowledge/1613771427075735553/King/sample/44352815613748c581e027764fb12ad6/600.png",
                "photoId": photoId, "type": 2}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_add = requests.post(url=url, json=data, headers=header)
        addData_dict = rep_samples_add.json()
        assertions.assert_code(rep_samples_add.status_code, 200)
        assertions.assert_in_text(addData_dict['msg'], msg)
        # print(addData_dict)
        print(rep_samples_add.text)

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

        # 正则提取productSampleId值
        productSampleId = re.search('"productSampleId":"(.*?)"', query_data_text).group(1)
        list_productSampleId.append(productSampleId)

        productSampleId_1 = re.search(
            '"productSampleId":"(\d+)","spaceManageId":"1613771427075735553","productCode":"King","name":"lin01"',
            query_data_text).group(1)
        list_productSampleId.append(productSampleId_1)

        productSampleId_2 = re.search(
            '"productSampleId":"(\d+)","spaceManageId":"1613771427075735553","productCode":"King","name":"lin02"',
            query_data_text).group(1)
        list_productSampleId.append(productSampleId_2)

        productSampleId_3 = re.search(
            '"productSampleId":"(\d+)","spaceManageId":"1613771427075735553","productCode":"King","name":"lin04"',
            query_data_text).group(1)
        list_productSampleId.append(productSampleId_3)

    @allure.story("删除刚新增的学习样例")
    def test_samples_delete(self):
        for i in list_productSampleId:
            deleteData = api_product_samples.ApiProductSamples().samples_delete(token, code, manageid, i)
            deleteData_dict = deleteData.json()
            assertions.assert_code(deleteData.status_code, 200)
            assertions.assert_in_text(deleteData_dict['msg'], '成功')
            # print(deleteData_dict)


if __name__ == '__main__':
    pass
