"""
2d标注相关接口
"""
import time
import random
from api import api_login, api_space
from common.Request_Response import ApiClient

env = api_login.url
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())


class Api2DLabel:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 查询2D标注任务
    def query_2d_task(self, taskName):
        url = f"{env}/miai/brainstorm/dimensiontask/page"
        payload = {"data": {"taskStatus": None, "labelUser": "", "startTime": "", "endTime": "", "taskName": taskName},
                   "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 查询标注图片
    def query_2d_sample(self, dimensionTaskId):
        url = f"{env}/miai/brainstorm/dimensiontaskdatalist/page"
        payload = {"data": {"imgName": "", "labelNames": [], "status": "2", "dimensionTaskId": dimensionTaskId},
                   "page": {"pageIndex": 1, "pageSize": 9999, "total": 0, "pages": 0}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 标注多边形
    def label_2d_polygon(self, dataId, label, shape_type, points, isDispute):
        url = f"{env}/miai/brainstorm/dimensiontaskdatalist/saveLabelJson"
        payload = {"dataId": dataId, "shapes": [
            {"disputeProcessTime": None, "disputeResult": None, "radius": "", "attributeP": "", "attributeM": "",
             "Smoothness": "", "ContrastRatio": "", "IsUneven": "", "DefectWidth": "", "DefectLength": "",
             "Brightness": "", "Area": "", "Shape": "", "confusionType": "", "checkType": "", "grade": "GQX",
             "isDispute": isDispute, "visualGrade": "S2", "definition": "QX", "customDefectField": {}, "label": label,
             "shape_type": shape_type, "width": 1,
             "points": points}],
                   "classifyType": label, "timeConsuming": 2400, "imageProperties": {"": ""}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 标注矩形
    def label_2d_rectangle(self, dataId, label, shape_type, points, isDispute):
        url = f"{env}/miai/brainstorm/dimensiontaskdatalist/saveLabelJson"
        payload = {"dataId": dataId, "shapes": [
            {"label": label, "shape_type": shape_type, "width": 1, "radius": "",
             "points": points, "attributeP": "", "attributeM": "", "Smoothness": "",
             "ContrastRatio": "", "IsUneven": "", "DefectWidth": "", "DefectLength": "", "Brightness": "", "Area": "",
             "Shape": "", "confusionType": "", "checkType": "", "grade": "", "isDispute": isDispute, "visualGrade": "",
             "definition": "", "customDefectField": {}}], "classifyType": label, "timeConsuming": 200,
                   "imageProperties": {"": ""}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 提交复核
    def submit_review(self, dimensionTaskId):
        url = f"{env}/miai/brainstorm/dimensiontask/update1"
        payload = {"dimensionTaskId": dimensionTaskId, "taskStatus": 3}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 复核判定（taskStatus：8-不通过，taskStatus：4-通过）
    def review_judge(self, dimensionTaskId, taskStatus):
        url = f"{env}/miai/brainstorm/dimensiontask/update2"
        payload = {"dimensionTaskId": dimensionTaskId, "taskStatus": taskStatus}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 标注/重标（变更状态为：进行中）
    def re_label(self, dimensionTaskId):
        url = f"{env}/miai/brainstorm/dimensiontask/update3"
        payload = {"dimensionTaskId": dimensionTaskId, "taskStatus": 2}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 创建&提交数据集
    def create_dataset(self, name, dimensionTaskId):
        url = f"{env}/miai/brainstorm/dimensiontask/addTaskDataListToDataset"
        payload = {"type": 0, "name": name, "trainPercent": 50, "testPercent": 50, "dimensionTaskId": dimensionTaskId,
                   "dataAlgorithmTestDatasetId": ""}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response
