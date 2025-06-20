"""
综合样本库相关接口封装
"""

import requests
import time
from api import api_login, api_space
from common.Request_Response import ApiClient

env = api_login.url
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())


class ApiComprehensiveSampleLibrary:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 综合样本库查询
    def comprehensive_sample_query(self, imgName, defectName, photoId):
        url = f"{env}/miai/brainstorm/es/global/sample/page"

        payload = {
            "data": {"endTime": None, "startTime": None, "imgName": imgName, "visualGrade": [], "bashSampleType": [],
                     "productId": [self.product_info_id], "defectName": defectName, "photoId": photoId,
                     "classifyType": [],
                     "imageDefinition": [],
                     "sampleType": [], "dataAlgorithmSampleType": [], "deepModelSampleType": []},
            "page": {"pageIndex": 1, "pageSize": 10}}
        return self.client.post(url, json=payload)

    # 综合样本库-创建深度训练任务(目标检测)
    def create_deep_training_tasks(self, defectName, photoId, cut, taskName, classifyType, caseId, caseName, type,
                                   iscut):
        url = f"{env}/miai/brainstorm/global/sample/createTrainTask"
        payload = {"endTime": None, "startTime": None, "imgName": "", "visualGrade": [], "bashSampleType": [],
                   "productId": [self.product_info_id], "defectName": defectName, "photoId": photoId,
                   "classifyType": classifyType,
                   "imageDefinition": [], "sampleType": [], "dataAlgorithmSampleType": [], "deepModelSampleType": [],
                   "selectIds": [], "notSelectIds": [], "taskName": taskName, "testSetMinValue": 0,
                   "testSetProportion": 30,
                   "caseId": caseId, "caseName": caseName, "cut": iscut, "filter": False, "remark": "",
                   "defectCount": "[{\"labelName\":\"\",\"count\":\"\"}]", "cutHeight": cut, "cutWidth": cut,
                   "typeMapping": "{\"liangdian\":\"liangdian\",\"liebian\":\"liebian\"}", "type": type}
        return self.client.post(url, json=payload)

    # 综合样本库-追加到深度训练任务(目标检测-按比例划分)
    def append_deep_training_tasks1(self, defectName, photoId, trainId):
        url = f"{env}/miai/brainstorm/global/sample/addition"

        payload = {"endTime": None, "startTime": None, "imgName": "", "visualGrade": [], "bashSampleType": [],
                   "productId": [self.product_info_id], "defectName": defectName, "photoId": photoId,
                   "classifyType": [],
                   "imageDefinition": [], "sampleType": [], "dataAlgorithmSampleType": [], "deepModelSampleType": [],
                   "selectIds": [], "notSelectIds": [], "testSetMinValue": 0, "testSetProportion": 40,
                   "trainId": trainId, "datasetType": 3, "filter": False, "defectCount": "[]"}

        return self.client.post(url, json=payload)

    # 综合样本库-追加到深度训练任务(目标检测-划分训练集1/验证集2)
    def append_deep_training_tasks2(self, defectName, photoId, sampleType, trainId, datasetType):
        url = f"{env}/miai/brainstorm/global/sample/addition"

        payload = {"imgName": "", "endTime": None, "startTime": None, "visualGrade": [], "bashSampleType": [],
                   "productId": [self.product_info_id], "defectName": defectName, "photoId": photoId,
                   "classifyType": [],
                   "sampleType": sampleType, "imageDefinition": [], "dataAlgorithmSampleType": [],
                   "deepModelSampleType": [],
                   "selectIds": [], "notSelectIds": [], "trainId": trainId, "datasetType": datasetType,
                   "filter": False, "defectCount": "[]"}

        return self.client.post(url, json=payload)


if __name__ == '__main__':
    pass
    # api = ApiComprehensiveSampleLibrary()
    # api.comprehensive_sample_query(None, ["shang"], ["1", "2", "3"])
    # api.create_deep_training_tasks(["shang"], ["1", "2", "3"], 1024)
    # api.append_deep_training_tasks(["yimo"], ["1", "2"], None)
    # api.append_deep_training_tasks2(None, ["3"], ["ok"], None, 1)
