import requests
import time
from api import api_login, api_space
from common.Request_Response import ApiClient

env = api_login.url
time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())


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
