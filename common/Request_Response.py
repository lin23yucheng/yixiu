import allure
import requests
import time
from requests.exceptions import HTTPError
from requests.exceptions import ConnectionError, Timeout

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

        # 添加重试配置
        self.max_retry_seconds = 60  # 最大重试时间60秒
        self.retry_interval = 5  # 重试间隔5秒

    @log_allure_request_response
    def request_with_retry(self, method, url, **kwargs):
        """
        带重试机制的请求方法
        """
        start_time = time.time()
        attempt = 0

        while True:
            attempt += 1
            try:
                headers = {**self.base_headers, **kwargs.pop('headers', {})}
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()  # 触发HTTP异常
                return response
            except (HTTPError, ConnectionError, Timeout) as e:
                # 处理503错误和网络错误
                error_type = "503错误" if isinstance(e, HTTPError) and e.response.status_code == 503 else "网络错误"

                elapsed = time.time() - start_time

                # 检查是否超过最大重试时间
                if elapsed > self.max_retry_seconds:
                    raise Exception(f"重试超过{self.max_retry_seconds}秒仍然失败") from e

                # 打印重试信息
                print(f"\r{error_type}: 正在重试 (尝试 {attempt}次, 已等待 {int(elapsed)}秒)", end="")
                time.sleep(self.retry_interval)
            except Exception as e:
                # 其他异常直接抛出
                raise

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

    # 常用方法快捷方式（添加带重试版本）
    def post_with_retry(self, url, **kwargs):
        return self.request_with_retry('POST', url, **kwargs)

    def get_with_retry(self, url, **kwargs):
        return self.request_with_retry('GET', url, **kwargs)

    # 常用方法快捷方式
    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def put(self, url, **kwargs):
        return self.request('PUT', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)
