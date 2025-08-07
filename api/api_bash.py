"""
bash系统相关接口
"""
import requests
from api import api_space
from common.Request_Response import ApiClient

bash_fat = "http://fat-bash-gw.svfactory.com:6180"


class ApiBashSample:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # bash系统登录
    @staticmethod
    def bash_login(account, password):
        bash_url = f"{bash_fat}/auth/login"
        bash_login_data = {"account": account, "password": password}
        bash_login_header = {"content-type": "application/json"}

        try:
            response = requests.post(
                url=bash_url,
                json=bash_login_data,
                headers=bash_login_header,
                timeout=20
            )

            try:
                token_data = response.json()
                accessToken = token_data["data"]["tokenInfo"]["accessToken"]
            except KeyError:
                raise ValueError("响应结构无效：未找到accessToken")
            except ValueError as e:
                raise ValueError(f"JSON 解析异常: {e}")

        except requests.exceptions.RequestException as e:
            # 统一处理网络请求异常
            raise ConnectionError(f"登录请求失败: {e}")

        return accessToken

    # 查询项目管理
    def query_project_manage(self, space_name):
        url = f"{bash_fat}/manage/project/projectList"
        payload = {"data": {"name": space_name}, "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 查询产品管理
    def query_product_manage(self, miaispacemanageid, miaiproductcode):
        url = f"{bash_fat}/manage/product/page"
        payload = {"data": {"projectId": miaispacemanageid, "productCode": miaiproductcode, "settingStatus": "1",
                            "productSwitch": "1", "productDetectionType": "", "productHandleType": ""},
                   "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 修改产品管理 productDetectionType=2 处理模式为“全量”
    def update_product_manage(self, projectId, projectName, productId, productCode):
        url = f"{bash_fat}/manage/product/update"
        payload = {"projectId": projectId, "projectName": projectName, "id": productId,
                   "productCode": productCode, "settingStatus": 1, "productSwitch": 1, "productYield": None,
                   "ctTime": 30,
                   "exactCtTime": None, "imgNumber": None, "seatTime": 30, "exactSeatTime": None,
                   "productDetectionType": 2, "productHandleType": 1, "idleIntervalTime": "", "productLevel": 0,
                   "switchTime": None, "imageTransformTime": 0, "imageTransformSwitch": 2, "productDefectBoxWidth": 100,
                   "productDefectBoxHeight": 100}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 查询人员userId
    def query_personnel_id(self):
        url = f"{bash_fat}/manage/user/userList"
        payload = {"data": {"userId": "", "productId": "", "projectId": "", "source": 1},
                   "page": {"pageIndex": 1, "pageSize": 1000}}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 人员产品查询
    def query_product_manage_person(self, userid):
        url = f"{bash_fat}/manage/user/userProductList"
        payload = {"data": {"userId": userid}, "page": {"pageIndex": 1, "pageSize": 100}}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 人员和产品关联
    def add_personnel_product(self, bash_product_id, priority, userid):
        url = f"{bash_fat}/manage/user/addProductForSeatUser"
        payload = {"list": [
            {"productId": bash_product_id, "priority": priority, "userProductId": "", "isFractionation": False,
             "handleType": ""}], "userId": userid}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 查询班次管理
    def query_shift_management(self):
        url = f"{bash_fat}/manage/shift/list"

        response = self.client.post_with_retry(url, json=None)
        return response

    # 查看人员计划
    def query_personnel_plan(self):
        url = f"{bash_fat}/manage/productionPlan/userShiftList"
        payload = {"data": {"endTime": "", "startTime": ""}, "page": {"pageIndex": 1, "pageSize": 100}}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 生成人员计划
    def create_personnel_plan(self, endTime, startTime, shiftid):
        url = f"{bash_fat}/manage/productionPlan/userShiftAdd"
        payload = {"endTime": endTime, "startTime": startTime, "planNum": "100",
                   "productIds": [], "shiftId": shiftid}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 查看人员排班
    def query_personnel_schedule(self, endTime, startTime):
        url = f"{bash_fat}/manage/productionPlan/userList"
        payload = {"endTime": endTime, "startTime": startTime}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 修改人员排班
    def update_personnel_schedule(self, endTime, startTime, userid_list, shiftid):
        url = f"{bash_fat}/manage/productionPlan/userShiftUpdate"
        payload = {"endTime": endTime, "startTime": startTime,
                   "userId": userid_list, "shiftId": shiftid}

        response = self.client.post_with_retry(url, json=payload)
        return response

    # 发布排班
    def release_personnel_schedule(self, endTime, startTime):
        url = f"{bash_fat}/manage/productionPlan/userShiftRelease"
        payload = {"endTime": endTime, "startTime": startTime}

        response = self.client.post_with_retry(url, json=payload)
        return response
