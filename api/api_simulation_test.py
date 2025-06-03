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


class ApiSimulationTest:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 查询测试图集列表页
    def query_test_data(self, product_id):
        url = f"{env}/miai/brainstorm/datalg/dataalgorithmtestdataset/page"
        payload = {"data": {"onlySelf": True, "productInfoId": product_id},
                   "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response
