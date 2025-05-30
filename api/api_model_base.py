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


class ApiModelBase:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 模型库查询
    def query_model_base(self):
        url = f"{env}/miai/brainstorm/newmodelmanage/modelManagePage"
        payload = {"data": {"showSelf": True}, "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 部署测试
    def deploy_test(self, modelManageId):
        url = f"{env}/miai/brainstorm/newmodelmanage/test/{modelManageId}"

        response = self.client.post(url, json=None)
        response.raise_for_status()
        return response

    # 模型撤回
    def model_withdraw(self, modelManageId):
        url = f"{env}/miai/brainstorm/newmodelmanage/withdrawAndDelete"
        payload = {"flag": 1, "modelManageId": modelManageId}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response
