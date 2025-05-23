"""
综合样本库相关接口封装
"""

import requests
import time
from api import api_login
from api import api_space

env = api_login.url
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())

login = api_login.ApiLogin()
token = login.login()
manageid = api_login.miaispacemanageid
api_space = api_space.ApiSpace()
product_info_id = api_space.product_query()
print(time)


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

    # 综合样本库-创建深度训练任务(目标检测)
    def create_deep_training_tasks(self, defectName, photoId, cut):
        url = env + "/miai/brainstorm/global/sample/createTrainTask"

        data = {"endTime": None, "startTime": None, "imgName": "", "visualGrade": [], "bashSampleType": [],
                "productId": ["1873905708948852738"], "defectName": defectName, "photoId": photoId, "classifyType": [],
                "imageDefinition": [], "sampleType": [], "dataAlgorithmSampleType": [], "deepModelSampleType": [],
                "selectIds": [], "notSelectIds": [], "taskName": "接口自动化-" + time_str, "testSetMinValue": 0,
                "testSetProportion": 30,
                "caseId": "detection", "caseName": "目标检测/分割", "cut": True, "filter": False, "remark": "",
                "defectCount": "[{\"labelName\":\"\",\"count\":\"\"}]", "cutHeight": cut, "cutWidth": cut, "type": 1}

        header = {"content-type": "application/json", "Authorization": token, "Miaispacemanageid": manageid}

        rep_create_deep = requests.post(url=url, json=data, headers=header)
        print(rep_create_deep.text)


if __name__ == '__main__':
    api = ApiComprehensiveSampleLibrary()
    # api.comprehensive_sample_query(None, ["shang"], ["1", "2", "3"])
    api.create_deep_training_tasks(["shang"], ["1", "2", "3"], 1024)
