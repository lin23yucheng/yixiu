"""
综合样本库相关接口封装
"""

import requests

from api import api_login
from common import Random
from api.api_space import ApiSpace
from api.api_login import ApiLogin

env = api_login.url
num = Random.random_str_abc(5)

api_space = ApiSpace()
login = ApiLogin()
token = login.login()
manageid = api_login.miaispacemanageid
product_info_id = api_space.product_query(token)


class ApiComprehensiveSampleLibrary:

    # 综合样本库查询
    def comprehensive_sample_query(self, imgName, defectName, photoId):
        url = env + "/miai/brainstorm/es/global/sample/page"

        data = {
            "data": {"endTime": None, "startTime": None, "imgName": imgName, "visualGrade": [], "bashSampleType": [],
                     "productId": [product_info_id], "defectName": defectName, "photoId": photoId, "classifyType": [],
                     "imageDefinition": [],
                     "sampleType": [], "dataAlgorithmSampleType": [], "deepModelSampleType": []},
            "page": {"pageIndex": 1, "pageSize": 10}}

        header = {"content-type": "application/json", "Authorization": token, "Miaispacemanageid": manageid}

        rep_sample_query = requests.post(url=url, json=data, headers=header)
        print(rep_sample_query.text)


if __name__ == '__main__':
    api = ApiComprehensiveSampleLibrary()
    api.comprehensive_sample_query(None, ["huashang"], ["12", "28", "3"])
