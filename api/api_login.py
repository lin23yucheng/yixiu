"""
一休云fat环境登录封装
"""

import requests

env = "fat"

if env == "dev":
    token_url = "https://dev-sso.svfactory.com:6143/auth/realms/uuam/protocol/openid-connect/token"
    username = "redisredis"
    password = 123456
    # 一休云地址
    url = "https://dev-manage.svfactory.com:6143"
    # 一休云header所需配置
    code = "tttttest"
    manageid = "1675763220799774721"
else:
    if env == "fat":
        token_url = "https://fat-sso.svfactory.com:6143/auth/realms/uuam/protocol/openid-connect/token"
        username = "19166459858"
        password = 123456
        # 一休云地址
        url = "https://fat-manage.svfactory.com:6143"
        # 一休云header所需配置
        code = "King"
        manageid = "1613771427075735553"
    else:
        print("环境不正确，请重新输入")


class ApiLogin:
    def __init__(self):
        pass

    def login(self):
        login_data = {"client_id": "brainstorm-fe", "username": username, "password": password,
                      "grant_type": "password"}
        login_header = {"content-type": "application/x-www-form-urlencoded"}

        login_rep = requests.post(url=token_url, data=login_data, headers=login_header)
        print(login_rep.text)
        token_type = login_rep.json()["token_type"]
        access_token = login_rep.json()["access_token"]
        token = token_type + " " + access_token
        print(token)
        return token


if __name__ == '__main__':
    m = ApiLogin()
    m.login()
