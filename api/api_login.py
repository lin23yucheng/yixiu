"""
一休云登录环境封装
"""

import requests
import configparser

# 读取配置
config = configparser.ConfigParser()
config.read("./config/env_config.ini")
section = "Inspection"

env = config.get(section, "execution_env")
space_name = config.get(section, "space_name")
miai_product_code = config.get(section, "miai-product-code")
miaispacemanageid = config.get(section, "miaispacemanageid")

if env == "dev":
    token_url = "https://dev-sso.svfactory.com:6143/auth/realms/uuam/protocol/openid-connect/token"
    username = "redisredis"
    password = 123456
    # 一休云地址
    url = "https://dev-manage.svfactory.com:6143"
    # 一休云header所需配置
    code = miai_product_code
    manageid = miaispacemanageid
else:
    if env == "fat":
        token_url = "https://fat-sso.svfactory.com:6143/auth/realms/uuam/protocol/openid-connect/token"
        username = "linyucheng"
        password = 123456
        # 一休云地址
        url = "https://fat-manage.svfactory.com:6143"
        # 一休云header所需配置
        code = miai_product_code
        manageid = miaispacemanageid
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
        # print(login_rep.text)
        token_type = login_rep.json()["token_type"]
        access_token = login_rep.json()["access_token"]
        token = token_type + " " + access_token
        # print(token)
        return token


if __name__ == '__main__':
    m = ApiLogin()
    m.login()
