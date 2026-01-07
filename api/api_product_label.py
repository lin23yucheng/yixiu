"""
产品标签相关接口
"""
from api import api_login, api_space
from common.Request_Response import ApiClient

env = api_login.url
product_code = api_login.miai_product_code
manageid = api_login.miaispacemanageid
space_name = api_login.space_name


class ApiProductLabel:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 查询产品标签
    def query_product_label(self):
        url = f"{env}/miai/brainstorm/labelinfo/page"
        payload = {"data": {"productCode": ""}, "page": {"pageIndex": 1, "pageSize": 100}}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 添加产品标签
    def add_product_label(self):
        url = f"{env}/miai/brainstorm/labelinfo/add"
        payload = {"labelNameList": ["suokong", "maoci"], "productCode": product_code, "spaceType": 1}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 修改产品标签
    def modify_product_label(self, priority, labelId):
        url = f"{env}/miai/brainstorm/labelinfo/update"
        payload = {"labelCnName": "缩孔", "hotKey": None, "labelName": "suokong", "markMethod": "多边形",
                   "labelColor": "#FF0000", "lableType": "polygon", "productCode": product_code, "priority": priority,
                   "spaceManageId": manageid, "labelId": labelId, "status": 1}

        response = self.client.post_with_retry(url, json=payload)
        return response
