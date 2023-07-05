import pytest


@pytest.fixture(scope="session", autouse=True)
def start_running():
    print("---马上开始执行自动化测试---")
    yield
    print("---自动化测试完成，开始处理本次测试数据---")
