import json
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


class ApiDeepTrainTasks:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 查询深度训练任务
    def query_train_tasks(self, task_name, page_size=10):
        url = f"{env}/miai/brainstorm/train/task/page"
        payload = {
            "data": {
                "productCode": "",
                "onlySelf": True,
                "onlyMachineTable": False,
                "taskName": task_name,
                "caseId": ""
            },
            "page": {
                "pageIndex": 1,
                "pageSize": page_size
            }
        }
        return self.client.post(url, json=payload)


class ApiModelTrain:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 模型方案查询
    def query_model(self):
        url = f"{env}/miai/brainstorm/newmodelcasetemplate/list/1"
        response = self.client.post(url, json=None)
        response.raise_for_status()  # 检查HTTP状态码（如果状态码不是200，会抛出HTTPError）
        return response

    # 训练机器查询
    def query_machine(self):
        url = f"{env}/miai/brainstorm/computingpower/enabledcomputinglist"
        response = self.client.post(url, json=None)
        response.raise_for_status()  # 检查HTTP状态码（如果状态码不是200，会抛出HTTPError）
        return response

    # 开始模型训练
    def start_train(self, caseId, modelSize, computingPowerId, trainTaskId):
        url = f"{env}/miai/brainstorm/newmodeltrain/startTrain"
        payload = {"resizeWidth": "", "resizeHeight": "", "caseId": caseId, "modelSize": modelSize,
                   "gpuCount": "1", "gpuSize": 1024, "source": 0, "keepLabels": [],
                   "computingPowerId": computingPowerId, "trainParams": True, "schemePhase": 1,
                   "paramSetting1": {"epoch": 30, "batchSize": 16, "lr": 0.0002}, "paramSetting2": None,
                   "trainTaskId": trainTaskId, "remark": f"接口自动化训练-{time_str}",
                   "modelCaseTemplateId": "1704414001586651234"}
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 训练记录查询
    def query_train_records(self, trainTaskId):
        url = f"{env}/miai/brainstorm/newmodeltrain/page"
        payload = {"data": {"trainTaskId": trainTaskId, "onlyMachineTable": False},
                   "page": {"pageIndex": 1, "pageSize": 100}}
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 模型提交
    def submit_model(self, modelName, modelTrainId):
        url = f"{env}/miai/brainstorm/newmodeltrain/submit"
        payload = {"modelName": modelName, "sides": [{"photoId": "", "productCode": "", "productId": 0}],
                   "modelThreshold": 0.1, "iouThreshold": 0.45, "modelTrainId": modelTrainId}
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response


if __name__ == '__main__':
    product_id = api_space.ApiSpace().product_query()
    api = ApiModelTrain(global_client)  # 使用 global_client 而不是新建实例

    query_model_data = api.query_model()
    print("模型方案接口返回JSON:")
    print(json.dumps(query_model_data, indent=2, ensure_ascii=False))
    print('-' * 100)
    query_machine_data = api.query_machine()
    print("训练机器接口返回JSON:")
    print(json.dumps(query_machine_data, indent=2, ensure_ascii=False))
