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
            response.raise_for_status()

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

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 人员产品查询
    def query_product_manage_person(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/user/userProductList"
        payload = {"data": {"userId": "1801455539486277634"}, "page": {"pageIndex": 1, "pageSize": 100}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 查看人员计划
    def query_personnel_plan(self):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftList"
        payload = {"data": {"endTime": "", "startTime": ""}, "page": {"pageIndex": 1, "pageSize": 100}}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 生成人员计划 shiftId是班次ID（固定写死白班）
    def create_personnel_plan(self, endTime, startTime):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftAdd"
        payload = {"endTime": endTime, "startTime": startTime, "planNum": "100",
                   "productIds": [], "shiftId": "1854365956311035906"}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 查看人员排班
    def query_personnel_schedule(self, endTime, startTime):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userList"
        payload = {"endTime": endTime, "startTime": startTime}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 修改人员排班
    def update_personnel_schedule(self, endTime, startTime):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftUpdate"
        payload = {"endTime": endTime, "startTime": startTime,
                   "userId": ["1821482508596625410", "1910308599700074498", "1856515927701401602",
                              "1930456820288008194", "1931892539661430786", "1621095121433473025",
                              "1622544867769823234", "1643530947360829441", "1620991769955905537",
                              "1673887244406820865", "1716641081823780866", "1673892773061529601",
                              "1713832822780116993", "1700054528677183490", "1700055862767845378",
                              "1701835492136509441", "1700043518555635713", "1692453759350657025",
                              "1778348304440303619", "1716644887928168449", "1716645111669121025",
                              "1778348305065254913", "1772200936628736001", "1778348304440303618",
                              "1716645361569947649", "1716757351780904961", "1716765262586376194",
                              "1716765600861188097", "1717481206996594690", "1718890481157468162",
                              "1721043446411988994", "1724269360516628482", "1778348304440303633",
                              "1724332012672581633", "1723957942021980161", "1724699287841865730",
                              "1724699539705626625", "1724699665027235841", "1724700364809109506",
                              "1726845864381743105", "1726845989955010561", "1735592069235343361",
                              "1718873840214405122", "1778300682769866753", "1778300956146212865",
                              "1778301047280050177", "1778301154310299649", "1778348305698594817",
                              "1778348306340323329", "1778348306948497410", "1778348307535699969",
                              "1778348308177428482", "1778348308756242433", "1778348309339250689",
                              "1778348309951619074", "1778348348312723457", "1778348442571317249",
                              "1778348514440716290", "1778348675309051906", "1788029532323176450",
                              "1788029750657671170", "1778348276854366210", "1788029671817338882",
                              "1809127353285726210", "1796479055556050945", "1810497084538343425",
                              "1790256543321686017", "1778348593184579586", "1788029597750124546",
                              "1723982965994618882", "1600012552506777602", "1793925286079680513",
                              "1796478942074961921", "1790934216091541505", "1793892131767504898",
                              "1801455539486277634", "1809040760415834113"], "shiftId": "1854365956311035906"}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

    # 发布排班
    def release_personnel_schedule(self, endTime, startTime):
        url = f"http://fat-bash-gw.svfactory.com:6180/manage/productionPlan/userShiftRelease"
        payload = {"endTime": endTime, "startTime": startTime}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response

