import allure
import requests


def log_allure_request_response(func):
    """
    Allure请求响应记录装饰器
    功能：自动记录接口的请求参数和响应结果
    适用：支持requests的get/post/put/delete等所有方法
    """

    def wrapper(*args, **kwargs):
        # 捕获请求参数
        request_args = {
            'method': kwargs.get('method', 'GET').upper(),
            'url': kwargs.get('url', ''),
            'headers': kwargs.get('headers', {}),
            'json': kwargs.get('json'),
            'data': kwargs.get('data'),
            'params': kwargs.get('params'),
            'files': kwargs.get('files')
        }

        # 记录请求信息
        request_info = (
            f"Request Method: {request_args['method']}\n"
            f"Request URL: {request_args['url']}\n"
            f"Request Headers: {request_args['headers']}\n"
            f"Request Body: {request_args['json'] or request_args['data']}\n"
            f"Query Params: {request_args['params']}\n"
            f"Upload Files: {list(request_args['files'].keys()) if request_args['files'] else None}"
        )
        allure.attach(request_info, "Request Details", allure.attachment_type.TEXT)

        # 执行请求
        response = func(*args, **kwargs)

        # 记录响应信息
        try:
            response_body = response.json()
            attach_type = allure.attachment_type.JSON
        except ValueError:
            response_body = response.text
            attach_type = allure.attachment_type.TEXT

        response_info = (
            f"Status Code: {response.status_code}\n"
            f"Response Headers: {dict(response.headers)}\n"
            f"Response Body:\n{response_body}"
        )
        allure.attach(response_info, "Response Details", attach_type)

        return response

    return wrapper


class ApiClient:
    """封装的请求客户端"""

    def __init__(self, base_headers=None):
        self.session = requests.Session()
        self.base_headers = base_headers or {}

    @log_allure_request_response
    def request(self, method, url, **kwargs):
        """统一请求方法"""
        headers = {**self.base_headers, **kwargs.pop('headers', {})}
        return self.session.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )

    # 常用方法快捷方式
    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def put(self, url, **kwargs):
        return self.request('PUT', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)
