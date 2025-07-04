"""
bash系统相关接口
"""
from api import api_space
from common.Request_Response import ApiClient


class ApiBashSample:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # 查询产品管理
    def query_product_manage(self, miaispacemanageid, miaiproductcode):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/product/page"
        payload = {"data": {"projectId": miaispacemanageid, "productCode": miaiproductcode, "settingStatus": "1",
                            "productSwitch": "1", "productDetectionType": "", "productHandleType": ""},
                   "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 人员产品查询
    def query_product_manage_person(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/user/userProductList"
        payload = {"data": {"userId": "1801455539486277634"}, "page": {"pageIndex": 1, "pageSize": 50}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 查看人员计划
    def query_personnel_plan(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftList"
        payload = {"data": {"endTime": "", "startTime": ""}, "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 生成人员计划
    def create_personnel_plan(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftAdd"
        payload = {"endTime": "2025-07-06T23:59:00.000Z", "startTime": "2025-07-06T00:00:00.000Z", "planNum": "100",
                   "productIds": [], "shiftId": "1854365956311035906"}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 修改人员排班
    def update_personnel_schedule(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftUpdate"
        payload = {"endTime": "2025-07-04T23:59:00", "startTime": "2025-07-04T00:00:00",
                   "userId": ["1801455539486277634"], "shiftId": "1854365956311035906"}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 查看人员排班
    def query_personnel_schedule(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userList"
        payload = {"endTime": "2025-07-04T23:59:00", "startTime": "2025-07-04T00:00:00"}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 发布排班
    def release_personnel_schedule(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftRelease"
        payload = {"endTime": "2025-07-04T23:59:00", "startTime": "2025-07-04T00:00:00"}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response
