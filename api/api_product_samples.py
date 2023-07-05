import requests
from api import api_login
from common import random

fat = api_login.fat
num = random.random_str_abc(5)


class ApiProductSamples:
    # 新增学习样例
    def samples_add(self, token, code, manageid):
        url = fat + "/miai/brainstorm/knowledgeproductsample/add"

        data = {"name": "cs_" + num, "detail": "说明说明说明", "sampleType": 1, "file": [],
                "imgPath": "knowledge/1613771427075735553/King/sample/44352815613748c581e027764fb12ad6/600.png",
                "photoId": 24, "type": 2}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_add = requests.post(url=url, json=data, headers=header)
        print(rep_samples_add.text)
        return rep_samples_add

    # 查询学习样例
    def samples_query(self, token, code, manageid):
        url = fat + "/miai/brainstorm/knowledgeproductsample/page"

        data = {"data": {"name": "", "type": 2}, "page": {"pageIndex": 1, "pageSize": 10}}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_query = requests.post(url=url, json=data, headers=header)
        print(rep_samples_query.text)
        return rep_samples_query

    # 删除学习样例
    def samples_delete(self, token, code, manageid, productSampleId):
        url = fat + "/miai/brainstorm/knowledgeproductsample/delete/" + productSampleId

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_delete = requests.post(url=url, headers=header)
        print(rep_samples_delete.text)
        return rep_samples_delete


if __name__ == '__main__':
    pass
    # m = ApiProductSamples()
    # m.samples_add(token, "King", "1613771427075735553")
