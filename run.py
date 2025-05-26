"""
修改后支持硬编码路径的run.py
"""
import os
import sys
import pytest


def run_tests():
    # ================== 配置区（直接修改这里即可）================== #
    target_file = "testcase/test_product_samples.py"  # 要执行的测试文件路径
    target_class = None  # 要执行的测试类名（如：Test_check_samples）
    target_method = None  # 要执行的测试方法名（如：test_samples_add）
    # ================== 以下代码无需修改 ================== #

    # 添加项目根目录到Python路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # 构建目标路径
    target_path = target_file.replace('/', os.sep)
    if not os.path.exists(target_path):
        print(f"错误：测试文件 {target_path} 不存在！")
        sys.exit(1)

    # 组合执行目标
    target = target_path
    if target_class:
        target += f"::{target_class}"
        if target_method:
            target += f"::{target_method}"

    # 配置报告路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    allure_results = os.path.join(base_dir, "report", "allure-results")
    allure_report = os.path.join(base_dir, "report", "allure-report")

    # 执行参数
    pytest_args = [
        "-v",
        "-s",
        target,
        f"--alluredir={allure_results}",
        "--clean-alluredir"
    ]

    # 执行测试
    exit_code = pytest.main(pytest_args)

    # 生成报告
    if exit_code in [0, 1]:
        os.system(f"allure generate {allure_results} -o {allure_report} --clean")
        print(f"报告路径：file://{os.path.abspath(allure_report)}/index.html")
    else:
        print("执行过程发生严重错误")


if __name__ == "__main__":
    run_tests()
