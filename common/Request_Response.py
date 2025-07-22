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
        self.max_retry_seconds = 10  # 最大重试时间60秒
        self.retry_interval = 5  # 重试间隔5秒

    @log_allure_request_response
    def request_with_retry(self, method, url, **kwargs):
        """
        带重试机制的请求方法
        """
        start_time = time.time()
        attempt = 0

        # 需要重试的状态码列表
        retry_status_codes = [422, 503]

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

                # 检查是否需要重试的特定状态码
                if response.status_code in retry_status_codes:
                    raise HTTPError(f"需要重试的状态码: {response.status_code}", response=response)

                response.raise_for_status()  # 触发HTTP异常
                return response


            except (HTTPError, ConnectionError, Timeout) as e:
                # 判断是否可重试
                is_retryable = False
                # 1. 网络错误总是可重试
                if isinstance(e, (ConnectionError, Timeout)):
                    is_retryable = True
                    error_type = "网络错误"

                # 2. HTTP错误根据状态码判断
                elif isinstance(e, HTTPError) and hasattr(e, 'response'):
                    status_code = e.response.status_code
                    # 可重试状态码
                    if status_code in retry_status_codes:
                        is_retryable = True
                        error_type = f"{status_code}错误"

                    # 400错误特殊处理
                    elif status_code == 400:
                        # 直接抛出，不重试
                        raise ValueError("客户端请求错误，请检查参数") from e

                    # 其他HTTP错误
                    else:
                        error_type = f"HTTP错误({status_code})"
                # 不可重试的错误直接抛出
                if not is_retryable:
                    raise
                # 以下为可重试错误的处理逻辑
                elapsed = time.time() - start_time
                if elapsed > self.max_retry_seconds:
                    raise Exception(f"重试超过{self.max_retry_seconds}秒仍然失败") from e

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
