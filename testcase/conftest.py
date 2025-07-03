import pytest
import time
from common.Log import MyLog


def format_time(seconds):
    """将秒数转换为 'X分X秒' 格式"""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}分{remaining_seconds}秒"


@pytest.fixture(scope="session", autouse=True)
def start_running():
    try:
        start_time = time.time()
        MyLog.info("---马上开始执行自动化测试---")
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        formatted_duration = format_time(duration)
        MyLog.info(f"---自动化测试完成，总耗时: {formatted_duration}---")
