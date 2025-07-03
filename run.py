import os
import sys
import time
import pytest
import shutil
from threading import Thread
from common.Log import MyLog, set_log_level  # 导入日志模块

# 设置全局日志级别
set_log_level('info')


# 新增辅助函数：将秒数转换为分秒格式
def format_time(seconds):
    """将秒数转换为 'X分X秒' 格式"""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}分{remaining_seconds}秒"


def reset_logs():
    """清除之前的日志内容（通过关闭处理器并重新初始化）"""
    from common.Log import logger, MyLog

    # 获取正确的日志目录路径
    log_dir = MyLog.get_log_dir()
    print(f"日志目录: {log_dir}")

    # 关闭所有处理器
    for handler in logger.handlers[:]:
        try:
            handler.flush()
            handler.close()
        except Exception as e:
            print(f"关闭日志处理器失败: {e}")
        finally:
            logger.removeHandler(handler)

    # 等待确保文件句柄释放
    time.sleep(1)

    # 删除日志目录
    if os.path.exists(log_dir):
        try:
            shutil.rmtree(log_dir)
            print(f"已删除日志目录: {log_dir}")
        except Exception as e:
            print(f"删除日志目录失败: {e}")

    # 重新创建目录
    os.makedirs(log_dir, exist_ok=True)

    # 重新初始化日志处理器
    MyLog.reinit_handlers()

    MyLog.info("已清除历史日志文件")


def execute_test(test_file, allure_results):
    """执行单个测试文件"""
    MyLog.info(f"开始执行测试文件: {test_file}")

    # 构建目标路径
    target_path = test_file.replace('/', os.sep)
    if not os.path.exists(target_path):
        MyLog.error(f"错误：测试文件 {target_path} 不存在！")
        return 1

    # 执行参数
    pytest_args = [
        "-v",  # 详细输出
        "-s",  # 禁止捕获输出
        "-x",  # 遇到第一个失败时立即退出
        target_path,
        f"--alluredir={allure_results}",  # Allure报告存储路径
    ]

    # 执行测试
    exit_code = pytest.main(pytest_args)

    if exit_code in [0, 1]:
        MyLog.info(f"测试文件 {test_file} 执行完成")
    else:
        MyLog.error(f"测试文件 {test_file} 执行失败，退出码: {exit_code}")

    return exit_code


def run_selected_tests():
    """执行指定测试文件"""
    reset_logs()  # 清除之前的日志
    MyLog.info("===== 开始执行测试任务 =====")

    # 定义要执行的测试文件列表
    # test_files = [
    #     "testcase/test_deep_model_training.py",
    #     "testcase/test_class_cut_model_training.py",
    #     "testcase/test_class_original_model_training.py",
    #     "testcase/test_post_process.py",
    #     "testcase/test_model_base.py",
    #     "testcase/test_data_training_task.py",
    #     "testcase/test_simulation.py",
    #     "testcase/test_product_information.py"
    # ]
    test_files = [
        "testcase/test_model_training_metrics.py"
    ]

    # 添加项目根目录到Python路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # 配置报告路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    allure_results = os.path.join(base_dir, "report", "allure-results")
    allure_report = os.path.join(base_dir, "report", "allure-report")

    # 清空结果目录
    if os.path.exists(allure_results):
        shutil.rmtree(allure_results)
    os.makedirs(allure_results, exist_ok=True)
    MyLog.info("已清理历史报告数据")

    # 记录开始时间
    start_time = time.time()
    MyLog.info(f"开始执行所有测试文件 at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # 初始化耗时统计变量
    total_elapsed_time = 0.0  # 累加总耗时
    file_times = {}  # 存储每个文件的耗时

    # 迭代执行测试文件
    for test_file in test_files:
        # 记录单个文件开始时间
        file_start_time = time.time()

        exit_code = execute_test(test_file, allure_results)

        # 计算单个文件耗时
        file_elapsed_time = time.time() - file_start_time
        total_elapsed_time += file_elapsed_time
        file_times[test_file] = file_elapsed_time

        # 使用新的时间格式
        formatted_time = format_time(file_elapsed_time)
        MyLog.info(f"测试文件 {test_file} 执行完成，耗时: {formatted_time}")

        # 检查退出代码
        if exit_code not in [0, 1]:
            MyLog.critical(f"执行测试文件 {test_file} 发生严重错误，程序终止")
            sys.exit(exit_code)

    # 记录结束时间
    end_time = time.time()
    overall_time = end_time - start_time  # 整体耗时

    # 输出耗时统计（使用新格式）
    MyLog.info("===== 测试文件耗时明细 =====")
    for file, time_taken in file_times.items():
        formatted_time = format_time(time_taken)
        MyLog.info(f"{file}: {formatted_time}")

    # 格式化并输出总耗时
    formatted_total = format_time(total_elapsed_time)
    formatted_overall = format_time(overall_time)

    MyLog.info(f"测试文件累加总耗时: {formatted_total}")
    MyLog.info(f"整体执行耗时: {formatted_overall}")
    MyLog.info(f"完成执行所有测试文件 at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

    # 生成报告
    os.system(f"allure generate {allure_results} -o {allure_report} --clean")
    MyLog.info(f"测试报告生成成功: file://{os.path.abspath(allure_report)}/index.html")
    MyLog.info("===== 测试任务完成 =====")


def run_parallel_tests():
    """并行执行测试文件"""
    reset_logs()  # 清除之前的日志
    MyLog.info("===== 开始并行执行测试 =====")

    # 定义测试文件
    parallel_test_files = ["testcase/test_post_process.py"]

    # 添加项目根目录到Python路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # 配置报告路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    allure_results = os.path.join(base_dir, "report", "allure-results")
    allure_report = os.path.join(base_dir, "report", "allure-report")

    # 清空结果目录
    if os.path.exists(allure_results):
        shutil.rmtree(allure_results)
    os.makedirs(allure_results, exist_ok=True)
    MyLog.info("已清理历史报告数据")

    # 记录开始时间
    start_time = time.time()
    MyLog.info(f"开始并行测试 at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # 并行执行测试文件
    threads = []
    for test_file in parallel_test_files:
        thread = Thread(target=execute_test, args=(test_file, allure_results))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 记录结束时间
    end_time = time.time()
    # 使用新格式输出时间
    formatted_time = format_time(end_time - start_time)
    MyLog.info(f"完成并行测试 at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    MyLog.info(f"总执行耗时: {formatted_time}")

    # 生成报告
    os.system(f"allure generate {allure_results} -o {allure_report} --clean")
    MyLog.info(f"测试报告生成成功: file://{os.path.abspath(allure_report)}/index.html")
    MyLog.info("===== 并行测试完成 =====")


if __name__ == "__main__":
    print("===== 测试执行程序启动 =====")
    MyLog.info("===== 测试执行程序启动 =====")

    # 选择执行模式
    run_selected_tests()  # 顺序执行
    # run_parallel_tests()  # 并行执行

    MyLog.info("===== 测试执行程序结束 =====")
    print("===== 测试执行程序结束 =====")
