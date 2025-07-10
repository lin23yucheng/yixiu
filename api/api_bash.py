"""
bash系统相关接口
"""
import requests

from api import api_space
from common.Request_Response import ApiClient


class ApiBashSample:
    def __init__(self, client: ApiClient):
        self.client = client
        self.product_info_id = api_space.ApiSpace().product_query()

    # bash系统登录
    @staticmethod
    def bash_login(account, password):
        bash_url = f"http://fat-bash-gw.svfactory.com:6180/auth/login"
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

    # 查询产品管理
    def query_product_manage(self, miaispacemanageid, miaiproductcode):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/product/page"
        payload = {"data": {"projectId": miaispacemanageid, "productCode": miaiproductcode, "settingStatus": "1",
                            "productSwitch": "1", "productDetectionType": "", "productHandleType": ""},
                   "page": {"pageIndex": 1, "pageSize": 10}}

        response = self.client.post_with_retry(url, json=payload)
         
        return response

    # 查询人员userId
    def query_personnel_id(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/user/userList"
        payload = {"data": {"userId": "", "productId": "", "projectId": "", "source": 1},
                   "page": {"pageIndex": 1, "pageSize": 1000}}

        response = self.client.post_with_retry(url, json=payload)
         
        return response

    # 人员产品查询
    def query_product_manage_person(self,userid):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/user/userProductList"
        payload = {"data": {"userId": userid}, "page": {"pageIndex": 1, "pageSize": 100}}

        response = self.client.post_with_retry(url, json=payload)
         
        return response

    # 查看人员计划
    def query_personnel_plan(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftList"
        payload = {"data": {"endTime": "", "startTime": ""}, "page": {"pageIndex": 1, "pageSize": 100}}

        response = self.client.post_with_retry(url, json=payload)
         
        return response

    # 生成人员计划 shiftId是班次ID（固定写死白班）
    def create_personnel_plan(self, endTime, startTime):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftAdd"
        payload = {"endTime": endTime, "startTime": startTime, "planNum": "100",
                   "productIds": [], "shiftId": "1854365956311035906"}

        response = self.client.post_with_retry(url, json=payload)
         
        return response

    # 查看人员排班
    def query_personnel_schedule(self, endTime, startTime):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userList"
        payload = {"endTime": endTime, "startTime": startTime}

        response = self.client.post_with_retry(url, json=payload)
         
        return response

    # 修改人员排班
    def update_personnel_schedule(self, endTime, startTime,userid_list):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftUpdate"
        payload = {"endTime": endTime, "startTime": startTime,
                   "userId": userid_list, "shiftId": "1854365956311035906"}

        response = self.client.post_with_retry(url, json=payload)
         
        return response

    # 发布排班
    def release_personnel_schedule(self, endTime, startTime):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftRelease"
        payload = {"endTime": endTime, "startTime": startTime}

        response = self.client.post_with_retry(url, json=payload)
         
        return response
