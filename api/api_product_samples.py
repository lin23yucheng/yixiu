import requests

from api import api_login
from common import Random

env = api_login.url
num = Random.random_str_abc(5)


class ApiProductSamples:
    # 上传图片
    def upload_pictures(self, token, code, manageid):
        url = env + "/miai/brainstorm/knowledgeproductsample/upload"

        file_path = r"C:\Users\admin\Desktop\1.png"

        with open(file_path, 'rb') as file:
            # 构造文件上传参数，键名需与接口期望的键一致
            files = {'file': file}
            header = {"Authorization": token, "Miai-Product-Code": code,
                      "Miaispacemanageid": manageid}

            response = requests.post(url=url, headers=header, files=files)

        # 输出响应状态码和内容
        # print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        # 断言
        assert response.status_code == 200, f"接口返回状态码异常，期望 200，实际 {response.status_code}"

        # 验证响应并提取 data
        response_data = response.json()

        # 直接提取 data（断言通过后执行）
        data_value = response_data['data']
        print(f"提取的文件路径: {data_value}")

        return data_value

    # 新增学习样例
    def samples_add(self, token, code, manageid, data_value):
        url = env + "/miai/brainstorm/knowledgeproductsample/add"

        data = {"name": "CS_" + num, "detail": "接口自动化" + num, "sampleType": 1, "file": [],
                "imgPath": data_value,
                "photoId": 2, "type": 1}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_add = requests.post(url=url, json=data, headers=header)
        print(rep_samples_add.text)
        return rep_samples_add

    # 查询学习样例
    def samples_query(self, token, code, manageid):
        url = env + "/miai/brainstorm/knowledgeproductsample/page"

        data = {"data": {"name": "", "type": 2}, "page": {"pageIndex": 1, "pageSize": 10}}

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_query = requests.post(url=url, json=data, headers=header)
        print(rep_samples_query.text)
        return rep_samples_query

    # 修改学习样例
    def samples_update(self, token, code, manageid, productSampleId, data_value):
        url = env + "/miai/brainstorm/knowledgeproductsample/update/" + productSampleId

        data = {
            "productSampleId": productSampleId, "spaceManageId": manageid,
            "productCode": code, "name": "CS_update_" + num, "sampleType": 2, "detail": "接口自动化update_" + num,
            "imgPath": data_value,
            "photoId": 5,
            "type": 1, "version": 0, "jsonInfo": 'null', "frameNum": 'null', "grid_order": 1, "file": [{}]}
        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_update = requests.post(url=url, json=data, headers=header)
        print(rep_samples_update.text)
        return rep_samples_update

    # 删除学习样例
    def samples_delete(self, token, code, manageid, productSampleId):
        url = env + "/miai/brainstorm/knowledgeproductsample/delete/" + productSampleId

        header = {"content-type": "application/json", "Authorization": token, "Miai-Product-Code": code,
                  "Miaispacemanageid": manageid}

        rep_samples_delete = requests.post(url=url, headers=header)
        print(rep_samples_delete.text)
        return rep_samples_delete


if __name__ == '__main__':
    # pass
    m = ApiProductSamples()
    m.samples_update(
        "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJQaW13SEZ5Wk1jdlNRRklJWUdFWW1fdGZNTFBldEU0ck5aMlphd3lVRXB3In0.eyJleHAiOjE3NDc5MTkyNjgsImlhdCI6MTc0Nzg5NDA2OCwiYXV0aF90aW1lIjoxNzQ3ODc2MzUzLCJqdGkiOiIyNDE1MWJiNi1kOTJmLTQ1ODYtYTBmYi1lYWViZmRiZmUyNmEiLCJpc3MiOiJodHRwczovL2ZhdC1zc28uc3ZmYWN0b3J5LmNvbTo2MTQzL2F1dGgvcmVhbG1zL3V1YW0iLCJzdWIiOiJmOjExMTQ0YmJjLWFkN2UtNDJkYS05ZTEyLWI3Y2Q5OWE5NWRiYzoxNzQwMjk5Nzg1OTY2OTgxMTIxIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiYnJhaW5zdG9ybS1mZSIsIm5vbmNlIjoiNDI0ZDgzY2YtNjE1NS00MzY2LTk3ZGEtODYwNDc3NzMwMzlkIiwic2Vzc2lvbl9zdGF0ZSI6IjgwNDQ0MTRmLTUwMGEtNGVjMC1iNmIxLTgzZjU1ZWYxNTcyYSIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6IjgwNDQ0MTRmLTUwMGEtNGVjMC1iNmIxLTgzZjU1ZWYxNTcyYSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6Iuael-emueaIkOa1i-ivleS9v-eUqCIsInByZWZlcnJlZF91c2VybmFtZSI6Imxpbnl1Y2hlbmciLCJnaXZlbl9uYW1lIjoi5p6X56a55oiQ5rWL6K-V5L2_55SoIiwiZW1haWwiOiI4NDkyMzYwMDBAcXEuY29tIn0.amxny7HWdOGWe2AqW6JdpQEXWa4_BLa-e6SbGxowBaeZDZFddwsnw-3kr09heGoH6JtWFlzq3TP3swStgUFJtxZr4Yke6vpTyKG8QPefnSesqzu9b4iPtlyUuBMzBy2DgZif6V6VRnjty1we2wU9FgrmlEJHo_9xQhrWjCN8yTh5Re3yvf2VqGi9xHCHyjSgqsH81i8ctAxSgqWwr9GI6LMd2J2QxtgJ4bhS15_2kGnhJRxhmtn71Y5Pudw5r0bNlzWtHBXm4y9DyLVpD06bd7kfII434pW-S_p5mAlLOXcxLxm9UH3zHhLrtNmbvNpt30a_9bHremmuew4s5LKLng",
        "JHOCT001", "1873905652887785473", "1925445114763345922",
        "knowledge/1873905652887785473/JHOCT001/sample/6e73f39b84944e2190f4b9b0c622f5ab/1.png")
