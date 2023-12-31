import allure
import pytest
import requests

from api import api_login
from common import Read_excel, Assert

assertions = Assert.Assertions()
env = api_login.url
token = api_login.ApiLogin().login()
code = api_login.code
manageid = api_login.manageid

# 单独执行写..  用run执行写.
excel_list = Read_excel.read_excel_list('./testdata/samples.xls')
ids_list = []
for i in range(len(excel_list)):
    # 删除excel_list中每个小list的最后一个元素,并赋值给ids_pop
    ids_pop = excel_list[i].pop(0)
    print(type(ids_pop))
    # 将ids_pop添加到 ids_list 里面
    ids_list.append(ids_pop)


@allure.feature("知识库-产品样例模块")
class TestProductSamples:
    @allure.story('新增学习样例')
    # 新增学习样例参数化
    @pytest.mark.parametrize('name,detail,sampleType,photoId,msg', excel_list, ids=ids_list)
    def test_samples_add(self, name, detail, sampleType, photoId, msg):
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
