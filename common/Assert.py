"""
封装Assert方法

"""
from common import Log
import json


class Assertions:
    def __init__(self):
        self.log = Log.MyLog()

    @staticmethod
    def assert_is_not_none(value, message):
        """检查值是否为 None，否则抛出断言错误"""
        if value is None:
            raise AssertionError(message)
        return True

    def assert_code(self, code, expected_code):
        """
        验证response状态码
        :param code:
        :param expected_code:
        :return:
        """
        try:
            assert code == expected_code
            return True
        except:
            self.log.error("响应状态码错误, 预期状态码 is %s, 实际状态码 is %s " % (expected_code, code))

            raise

    def assert_body(self, body, body_msg, expected_msg):
        """
        验证response body中任意属性的值
        :param body:
        :param body_msg:
        :param expected_msg:
        :return:
        """
        try:
            msg = body[body_msg]
            assert msg == expected_msg
            return True

        except:
            self.log.error(
                "Response body msg != expected_msg, expected_msg is %s, body_msg is %s" % (expected_msg, body_msg))
            self.log.error(
                "Response body msg != expected_msg, expected_msg is %s, body_msg is %s" % (expected_msg, body_msg))

            raise

    def assert_in_text(self, body, expected_msg):
        """
        验证response body中是否包含预期字符串
        :param body:
        :param expected_msg:
        :return:
        """
        try:
            text = json.dumps(body, ensure_ascii=False)
            # print(text)
            assert expected_msg in text
            return True

        except:
            self.log.error("响应正文不包含期望值, 期望值 是  %s" % expected_msg)

            raise

    def assert_text(self, body, expected_msg):
        """
        验证response body中是否等于预期字符串
        :param body:
        :param expected_msg:
        :return:
        """
        try:
            assert body == expected_msg
            return True

        except:
            self.log.error("Response body != expected_msg, expected_msg is %s, body is %s" % (expected_msg, body))

            raise

    def assert_time(self, time, expected_time):
        """
        验证response body响应时间小于预期最大响应时间,单位：毫秒
        :param body:
        :param expected_time:
        :return:
        """
        try:
            assert time < expected_time
            return True

        except:
            self.log.error("Response time > expected_time, expected_time is %s, time is %s" % (expected_time, time))

            raise
