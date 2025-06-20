import json
import requests
import time
from api import api_login, api_space
from common.Request_Response import ApiClient

env = api_login.url
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())

# 初始化全局客户端
base_headers = {
    "Authorization": api_login.ApiLogin().login(),
    "Miai-Product-Code": api_login.code,
    "Miaispacemanageid": api_login.manageid
}
global_client = ApiClient(base_headers=base_headers)


class ApiDataTrainTasks:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 查询数据训练任务
    def query_data_tasks(self):
        url = f"{env}/miai/brainstorm/datalg/dataalgorithmtraintask/page"
        payload = {"data": {"onlySelf": True}, "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 拷贝数据训练任务
    def copy_data_tasks(self, modelManageId, deepModelName, deepModelVersion, tritonPath, TrainTaskId):
        url = f"{env}/miai/brainstorm/datalg/dataalgorithmtraintask/copy"
        payload = {"taskName": f"接口自动化-数据-{time_str}", "modelManageId": modelManageId,
                   "deepModelName": deepModelName, "deepModelVersion": deepModelVersion, "combineType": None,
                   "isCombine": False,
                   "tritonPath": tritonPath,
                   "deepModelSource": "2", "isAllinPhoto": True, "checkScope": "ALL",
                   "displayName": f"{deepModelName} V{deepModelVersion} ",
                   "dataAlgorithmTrainTaskId": TrainTaskId}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 删除数据训练任务
    def delete_data_tasks(self, data_task_id):
        url = f"{env}/miai/brainstorm/datalg/dataalgorithmtraintask/delete/{data_task_id}"

        response = self.client.post(url, json=None)
        response.raise_for_status()
        return response

    # 生成下载数据包
    def create_data_zip(self, data_task_id):
        url = f"{env}/miai/brainstorm/datalg/dataAlgorithmCollect/createCollectTask/{data_task_id}"

        response = self.client.post(url, json=None)
        response.raise_for_status()
        return response

    # 上传数据算法
    def upload_data_algorithm(self, data_task_id):
        url = f"{env}/miai/brainstorm/datalg/dataalgorithmmodel/uploadDataAlgorithm"
        model_file_path = "./testdata/数据模型.zip"

        # 打开文件以二进制模式读取
        with open(model_file_path, 'rb') as model_file:
            files = {
                'modelFile': ('modelFile', model_file, 'application/octet-stream')
            }
            data = {
                'remark': f"接口自动化_{time_str}",
                'dataAlgorithmTrainTaskId': data_task_id
            }

            headers = self.client.base_headers.copy()
            headers.pop('Content-Type', None)

            response = requests.post(url, headers=headers, data=data, files=files)
            response.raise_for_status()
            return response

    # 查询上传记录
    def query_upload_record(self, data_task_id):
        url = f"{env}/miai/brainstorm/datalg/dataalgorithmmodel/page"
        payload = {"data": {"dataAlgorithmTrainTaskId": data_task_id}, "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 查询下载记录
    def query_download_record(self, data_task_id):
        url = f"{env}/miai/brainstorm/datalg/dataAlgorithmCollect/page"
        payload = {"data": {"dataAlgorithmTrainTaskId": data_task_id}, "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response
