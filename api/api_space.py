"""
空间的相关接口封装
"""
import requests
from api import api_login

env = api_login.url
product_code = api_login.miai_product_code
manageid = api_login.miaispacemanageid


class ApiSpace:
    # 产品查询
    def product_query(self, token):
        url = env + "/miai/brainstorm/productinfo/page"

        data = {"data": {"spaceManageId": manageid}, "page": {"pageIndex": 1, "pageSize": 100}}

        header = {"content-type": "application/json", "Authorization": token, "Miaispacemanageid": manageid}

        rep_product_query = requests.post(url=url, json=data, headers=header)
        rep_json = rep_product_query.json()
        print(rep_product_query.text)
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
    product_info_id = api.product_query(
        "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJQaW13SEZ5Wk1jdlNRRklJWUdFWW1fdGZNTFBldEU0ck5aMlphd3lVRXB3In0.eyJleHAiOjE3NDgwMDc2MTEsImlhdCI6MTc0Nzk4MjQxMSwiYXV0aF90aW1lIjoxNzQ3OTgxODI4LCJqdGkiOiJlZTk1ODliYS1mNjk3LTQzOTctODhjNC1iM2I2NDNhY2YyNjMiLCJpc3MiOiJodHRwczovL2ZhdC1zc28uc3ZmYWN0b3J5LmNvbTo2MTQzL2F1dGgvcmVhbG1zL3V1YW0iLCJzdWIiOiJmOjExMTQ0YmJjLWFkN2UtNDJkYS05ZTEyLWI3Y2Q5OWE5NWRiYzoxNzQwMjk5Nzg1OTY2OTgxMTIxIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiYnJhaW5zdG9ybS1mZSIsIm5vbmNlIjoiYzhjYzFlMTktZmFhNS00YzRhLTk5NzktOTc3NzZhNWRiMzc2Iiwic2Vzc2lvbl9zdGF0ZSI6ImU2MmVkZjg5LWYwMDItNDliZS1hMjE1LWUwOTllNzk1M2U3MSIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6ImU2MmVkZjg5LWYwMDItNDliZS1hMjE1LWUwOTllNzk1M2U3MSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6Iuael-emueaIkOa1i-ivleS9v-eUqCIsInByZWZlcnJlZF91c2VybmFtZSI6Imxpbnl1Y2hlbmciLCJnaXZlbl9uYW1lIjoi5p6X56a55oiQ5rWL6K-V5L2_55SoIiwiZW1haWwiOiI4NDkyMzYwMDBAcXEuY29tIn0.Sscy781CZHVYErn75K1mfwL-GdcCSCzEvZem4hLgaBwv_LWm8lEqxB6CypoxYw-fmsxRTDdSr_i_bKYoUw6ZDvWCf8K18oWgGRMY1D_WBYSPCh3Hu_9qg2YowV8uRjAMKyXqKK_1sZ-jTawD2QBAF2_5nEd_a8eu0-75RZhMyQZ7fl1aMxhqNUNWTibe2dc8yKDHkumc5gh_l_jAcM721Pi3kNrhSQa0kVpiuOgqO9hUITtAUWaXSDhI1AIUt3WCFcPFQA56EEG62eGrwJ9FewUW95tb5p6cqQkRMeGkG0-6jyNyo7T1tlmnKPOZrkBmt6zxBSZPsBfI4fxpbKjcCQ",
    )
    print("产品ID：", product_info_id)
