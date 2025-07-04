"""
bash样本库相关接口
"""
import time
import random
from api import api_login, api_space
from common.Request_Response import ApiClient

env = api_login.url
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())


class ApiBashSample:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 查询bash样本库-原始样本/分拣后样本
    def query_bash_sample(self):
        url = f"{env}/miai/brainstorm/sampleproductsyncmanage/sample/page"
        payload = {"data": {"dataType": 1, "sceneSampleType": "",
                            "date": ["2025-05-08T16:00:00.000Z", "2025-05-15T16:00:00.000Z"], "statusList": [],
                            "sampleSource": 1, "bashSampleType": "", "dataAlgorithmSampleType": "", "taskId": "",
                            "channelId": "", "deviceId": "", "photoId": "", "opticsSchemeId": "", "workpieceId": "",
                            "cameraId": "", "status": 1, "labelNames": [], "isUse": None, "sortingSampleType": "",
                            "productInfoId": self.product_info_id, "deepModelSampleType": "", "cvSampleType": "",
                            "bashUser": "", "isRelateOpticalSurface": False,
                            "startDateTime": "2025-05-08T16:00:00.000Z", "endDateTime": "2025-05-15T16:00:00.000Z"},
                   "page": {"pageIndex": 1, "pageSize": 15}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # bash样本库-分拣样本
    def bash_sorting_sample(self, sampledatasyncid, sortingsampletype):
        # 定义类型到详细值的映射规则
        type_detail_map = {
            "ng": [0, 8, 9],
            "ok": [1, 2, 3, 4]
        }

        # 验证输入类型是否有效
        if sortingsampletype not in type_detail_map:
            raise ValueError(f"无效的 sortingSampleType: {sortingsampletype}。只接受 'ng' 或 'ok'")

        # 随机选择对应的详细值
        sortingSampleTypeDetail = random.choice(type_detail_map[sortingsampletype])

        url = f"{env}/miai/brainstorm/sampleproductsyncmanage/classify"
        payload = {
            "productInfoId": self.product_info_id,
            "sampleDataSyncId": sampledatasyncid,
            "sortingSampleType": sortingsampletype,
            "sortingSampleTypeDetail": sortingSampleTypeDetail
        }

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # bash样本库-创建标注任务
    def create_label_task(self, sampledatasyncid):
        url = f"{env}/miai/brainstorm/sampleproductsyncmanage/addSampleToTask"
        payload = {"taskName": f"接口自动化标注-{time_str}", "dimensionTaskList": [
            {"labelUsers": [{"labelUserId": "1740299785966981121", "labelUserName": "林禹成测试使用"}],
             "taskName": f"接口自动化标注-{time_str}-1"}], "subTaskNum": 1, "subTaskSampleNum": 100,
                   "sceneSampleType": "",
                   "date": ["2025-05-08T16:00:00.000Z", "2025-05-15T16:00:00.000Z"], "statusList": [],
                   "sampleSource": 1, "bashSampleType": "", "dataAlgorithmSampleType": "", "taskId": "",
                   "channelId": "", "deviceId": "", "photoId": "", "opticsSchemeId": "", "workpieceId": "",
                   "cameraId": "", "status": 2, "labelNames": [], "isUse": False, "sortingSampleType": "ng",
                   "productInfoId": self.product_info_id, "dataType": 1, "deepModelSampleType": "", "cvSampleType": "",
                   "bashUser": "", "startDateTime": "2025-05-08T16:00:00.000Z",
                   "endDateTime": "2025-05-15T16:00:00.000Z", "excludeDataSyncIds": [],
                   "dataSyncIds": [sampledatasyncid]}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response
