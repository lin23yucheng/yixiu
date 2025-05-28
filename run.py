import os
import sys
import pytest


def run_test():
    # target_file = "testcase/test_deep_model_training.py"
    target_file = "testcase/test_post_process.py"
    target_class = None  # 要执行的测试类名
    target_method = None  # 要执行的测试方法名

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


def run_tests():
    # 定义按顺序执行的测试文件列表
    test_files = [
        "testcase/test_deep_model_training.py",
        "testcase/test_post_process.py"
    ]

    # 添加项目根目录到Python路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # 配置报告路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    allure_results = os.path.join(base_dir, "report", "allure-results")
    allure_report = os.path.join(base_dir, "report", "allure-report")

    # 在执行任何测试前，先清空结果目录（确保新执行不会包含旧结果）
    if os.path.exists(allure_results):
        import shutil
        shutil.rmtree(allure_results)
    os.makedirs(allure_results, exist_ok=True)

    # 迭代执行测试文件
    for test_file in test_files:
        # 构建目标路径
        target_path = test_file.replace('/', os.sep)
        if not os.path.exists(target_path):
            print(f"错误：测试文件 {target_path} 不存在！")
            sys.exit(1)

        print(f"\n开始执行测试文件：{test_file}")

        # 执行参数（不再使用--clean-alluredir）
        pytest_args = [
            "-v",
            "-s",
            target_path,
            f"--alluredir={allure_results}",
        ]

        # 执行测试
        exit_code = pytest.main(pytest_args)

        # 检查退出代码，非0/1表示严重错误，终止执行
        if exit_code not in [0, 1]:
            print(f"执行测试文件 {test_file} 发生严重错误，程序终止")
            sys.exit(exit_code)

    # 所有测试执行完毕后生成合并报告
    os.system(f"allure generate {allure_results} -o {allure_report} --clean")
    print(f"\n所有测试执行完毕，合并报告路径：file://{os.path.abspath(allure_report)}/index.html")


if __name__ == "__main__":
    run_test()
    # run_tests()
