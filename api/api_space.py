"""
空间的相关接口封装
"""
import requests
from api import api_login
from api.api_login import ApiLogin

env = api_login.url
product_code = api_login.miai_product_code
manageid = api_login.miaispacemanageid
login = ApiLogin()
token = login.login()


# 代码推送
# git push -u gitlab main
# git push -u origin main

class ApiSpace:
    # 产品查询
    def product_query(self):
        url = env + "/miai/brainstorm/productinfo/page"

        data = {"data": {"spaceManageId": manageid}, "page": {"pageIndex": 1, "pageSize": 100}}

        header = {"content-type": "application/json", "Authorization": token, "Miaispacemanageid": manageid}

        rep_product_query = requests.post(url=url, json=data, headers=header)
        rep_json = rep_product_query.json()
        # print(rep_product_query.text)
        if rep_json.get("success"):
            product_list = rep_json["data"]["list"]
            # 遍历查找目标产品
            for product in product_list:
                if product["productName"] == product_code:
                    return product["productInfoId"]  # 找到后直接返回
            return None  # 未找到返回None
        else:
            print("请求失败：", rep_json.get("msg"))
            return None


if __name__ == '__main__':
    api = ApiSpace()
    product_info_id = api.product_query()
    print("产品ID：", product_info_id)
