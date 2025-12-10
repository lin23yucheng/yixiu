import os
import sys
import time
import json
import pytest
import shutil
import psutil
import signal
from common.Log import MyLog, set_log_level, logger
from multiprocessing import Process, Manager

# ========== 核心路径重构（解决Allure并行冲突） ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Allure根结果目录（最终合并后的目录）
ALLURE_RESULTS_ROOT = os.path.join(BASE_DIR, "report", "allure-results")
# Allure临时目录（存放各进程的独立结果）
ALLURE_TEMP_ROOT = os.path.join(BASE_DIR, "report", "allure-temp")
allure_report = os.path.join(BASE_DIR, "report", "allure-report")
junit_root = os.path.join(BASE_DIR, "report", "junit")

# 添加全局变量来跟踪是否需要生成报告
should_generate_report = True
# 设置全局日志级别
set_log_level('info')


def signal_handler(sig, frame):
    """处理中断信号"""
    global should_generate_report
    MyLog.info("接收到中断信号，正在优雅退出...")
    print("\n接收到中断信号，正在生成测试报告...")

    # 设置标志位，让程序知道需要生成报告
    should_generate_report = True

    # 如果已经初始化了报告路径，则生成报告
    if ALLURE_RESULTS_ROOT and allure_report:
        generate_report_on_exit()

    MyLog.info("测试报告已生成，程序退出")
    sys.exit(0)


def generate_report_on_exit():
    """在退出时生成报告"""
    if ALLURE_RESULTS_ROOT and os.path.exists(ALLURE_RESULTS_ROOT):
        try:
            os.system(f"allure generate {ALLURE_RESULTS_ROOT} -o {allure_report} --clean")
            MyLog.info(f"测试报告生成成功: file://{os.path.abspath(allure_report)}/index.html")
            print(f"测试报告生成成功: file://{os.path.abspath(allure_report)}/index.html")
        except Exception as e:
            MyLog.error(f"生成报告时出错: {e}")


def format_time(seconds):
    """将秒数转换为 'X分X秒' 格式"""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}分{remaining_seconds}秒"


def reset_logs():
    """清除之前的日志内容（通过关闭处理器并重新初始化）"""
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


def merge_allure_results(src_dir, dest_dir):
    """
    安全合并Allure结果文件（解决文件名冲突）
    :param src_dir: 源目录（进程专属的allure-results）
    :param dest_dir: 目标目录（根allure-results）
    """
    if not os.path.exists(src_dir):
        MyLog.warning(f"源目录不存在，跳过合并: {src_dir}")
        return

    # 确保目标目录存在
    os.makedirs(dest_dir, exist_ok=True)

    # 遍历源目录所有文件
    for filename in os.listdir(src_dir):
        src_file = os.path.join(src_dir, filename)
        if os.path.isfile(src_file):
            # 处理重复文件名（比如多个进程生成的相同名称的JSON）
            dest_file = os.path.join(dest_dir, filename)
            counter = 1
            while os.path.exists(dest_file):
                # 重命名重复文件（如 test-result.json → test-result_1.json）
                name, ext = os.path.splitext(filename)
                dest_file = os.path.join(dest_dir, f"{name}_{counter}{ext}")
                counter += 1

            # 移动文件到目标目录
            shutil.move(src_file, dest_file)
            MyLog.debug(f"合并Allure文件: {src_file} → {dest_file}")

    # 删除空的源目录
    shutil.rmtree(src_dir, ignore_errors=True)
    MyLog.info(f"已合并进程Allure结果: {src_dir} → {dest_dir}")


def execute_test(test_file, allure_results, junit_file=None):
    """
    执行单个测试文件（最终版：资源隔离+自定义JUnit文件名+适配并行）
    :param test_file: 测试文件路径
    :param allure_results: 当前进程专属的allure-results目录
    :param junit_file: 自定义JUnit报告路径（None则不生成）
    :return: pytest执行退出码
    """
    MyLog.info(f"开始执行测试文件: {test_file}")

    # 1. 校验测试文件是否存在
    target_path = test_file.replace('/', os.sep)
    if not os.path.exists(target_path):
        MyLog.error(f"错误：测试文件 {target_path} 不存在！")
        return 1

    # 2. 创建独立工作目录（避免文件冲突）
    test_name = os.path.splitext(os.path.basename(test_file))[0]
    test_workspace = os.path.join(os.path.dirname(allure_results), "workspaces", test_name)
    os.makedirs(test_workspace, exist_ok=True)

    # 3. 设置环境变量（供测试用例内部使用）
    os.environ["TEST_WORKSPACE"] = test_workspace
    os.environ["CURRENT_TEST_FILE"] = test_file

    # 4. 构建pytest执行参数
    log_file = os.path.join(str(test_workspace), 'pytest.log')
    pytest_args = [
        "-v", "-s", "-x",  # 基础参数：详细输出、显示打印、第一个失败就停止当前文件执行
        target_path,  # 要执行的测试文件
        f"--alluredir={allure_results}",  # 当前进程专属的allure目录
        "--random-order",  # 随机执行用例（可选）
        f"--log-file={log_file}"  # pytest日志文件
    ]

    # 5. 新增：如果传入junit_file，则添加JUnit报告参数（核心优化）
    if junit_file:
        # 确保JUnit目录存在（防止外部传的路径目录不存在）
        junit_dir = os.path.dirname(junit_file)
        os.makedirs(junit_dir, exist_ok=True)
        pytest_args.append(f"--junitxml={junit_file}")
        MyLog.info(f"当前测试文件的JUnit报告路径: {junit_file}")

    # 6. 执行pytest测试
    exit_code = pytest.main(pytest_args)

    # 7. 执行结果日志
    if exit_code == 0:
        MyLog.info(f"测试文件 {test_file} 全部通过")
    elif exit_code == 1:
        MyLog.error(f"测试文件 {test_file} 存在失败用例")
    else:
        MyLog.critical(f"测试文件 {test_file} 执行错误，退出码: {exit_code}")

    # 8. 清理环境变量（避免影响后续测试）
    os.environ.pop("TEST_WORKSPACE", None)
    os.environ.pop("CURRENT_TEST_FILE", None)

    # 9. 最终状态日志
    if exit_code in [0, 1]:
        MyLog.info(f"测试文件 {test_file} 执行完成")
    else:
        MyLog.error(f"测试文件 {test_file} 执行失败，退出码: {exit_code}")

    return exit_code


def process_task(file, deps, require_success, event_dict, result_dict):
    """执行测试并处理依赖关系（进程版本+JUnit防冲突+Allure独立目录）"""
    import multiprocessing
    global junit_root, ALLURE_RESULTS_ROOT, ALLURE_TEMP_ROOT

    # ========== 1. 处理依赖逻辑 ==========
    deps = deps or []
    if deps:
        MyLog.info(f"任务 {file} 依赖: {deps}")
        for dep in deps:
            event_dict[dep].wait()  # 等待依赖事件完成
            dep_result = result_dict.get(dep)
            MyLog.info(f"依赖 {dep} 执行结果: {dep_result}")

            if require_success:
                # 严格检查：只有0才是完全成功，非0则跳过当前任务
                if dep_result != 0:
                    MyLog.warning(f"跳过 {file}：依赖 {dep} 执行失败（结果码: {dep_result}）")
                    result_dict[file] = -1
                    event_dict[file].set()
                    return
            else:
                # 宽松检查：依赖未执行/执行错误才跳过
                if dep_result in [-1, None] or dep_result > 1:
                    MyLog.warning(f"跳过 {file}：依赖 {dep} 未完成/执行错误（结果码: {dep_result}）")
                    result_dict[file] = -1
                    event_dict[file].set()
                    return

    # ========== 2. 生成进程专属的Allure/JUnit目录 ==========
    pid = multiprocessing.current_process().pid
    # 进程专属的Allure临时目录
    process_allure_results = os.path.join(ALLURE_TEMP_ROOT, f"pid_{pid}")
    os.makedirs(process_allure_results, exist_ok=True)
    # 进程专属的JUnit文件名
    test_name = os.path.splitext(os.path.basename(file))[0]
    junit_file = os.path.join(junit_root, f"junit_{test_name}_pid{pid}.xml")

    MyLog.info(f"进程 {pid} 执行 {file} → Allure目录: {process_allure_results}, JUnit: {junit_file}")

    # ========== 3. 执行测试 ==========
    MyLog.info(f"开始执行测试文件: {file}")
    exit_code = execute_test(file, process_allure_results, junit_file=junit_file)
    result_dict[file] = exit_code
    event_dict[file].set()

    # ========== 4. 合并当前进程的Allure结果到根目录 ==========
    merge_allure_results(process_allure_results, ALLURE_RESULTS_ROOT)

    # ========== 5. 校验JUnit文件生成结果 ==========
    if os.path.exists(junit_file):
        MyLog.info(f"进程 {pid} 已生成JUnit报告: {junit_file}")
    else:
        MyLog.warning(f"进程 {pid} 未生成JUnit报告: {junit_file}")


def run_together_tests():
    """使用进程实现依赖关系的并行测试执行"""
    reset_logs()  # 清除之前的日志
    MyLog.info("===== 开始并行执行测试（带依赖关系） =====")

    # 定义任务依赖关系
    tasks = [
        # 第一组：无依赖任务（并行执行）
        {"file": "testcase/test_bash.py", "deps": None, "require_success": False},
        {"file": "testcase/test_standard_push_map.py", "deps": None, "require_success": False},
        {"file": "testcase/test_deep_model_training_v8.py", "deps": None, "require_success": False},
        {"file": "testcase/test_deep_model_training_v11.py", "deps": None, "require_success": False},
        {"file": "testcase/test_deep_model_training_v12.py", "deps": None, "require_success": False},
        {"file": "testcase/test_class_cut_model_training_v8.py", "deps": None, "require_success": False},
        {"file": "testcase/test_class_original_model_training_v8.py", "deps": None, "require_success": False},
        {"file": "testcase/test_model_base.py", "deps": None, "require_success": False},
        {"file": "testcase/test_data_training_task.py", "deps": None, "require_success": False},
        # {"file": "testcase/test_simulation.py", "deps": None, "require_success": False},
        {"file": "testcase/test_product_information.py", "deps": None, "require_success": False},
        {"file": "testcase/test_product_samples.py", "deps": None, "require_success": False},
        {"file": "testcase/test_eiir_label.py", "deps": None, "require_success": False},
        {"file": "testcase/test_eiir_model_training.py", "deps": None, "require_success": False},

        # 第二组：有依赖任务
        {"file": "testcase/test_bash_ui.py", "deps": ["testcase/test_bash.py"], "require_success": True},
        {"file": "testcase/test_2D_label.py", "deps": ["testcase/test_bash_ui.py"], "require_success": True},
        {"file": "testcase/test_3D_label.py", "deps": ["testcase/test_standard_push_map.py"], "require_success": True},
        {"file": "testcase/test_model_training_metrics.py", "deps": ["testcase/test_data_training_task.py"],
         "require_success": True}
    ]

    # 添加项目根目录到Python路径
    sys.path.append(BASE_DIR)

    # ========== 初始化报告目录（清空历史数据） ==========
    # 清空JUnit目录
    if os.path.exists(junit_root):
        shutil.rmtree(junit_root)
    os.makedirs(junit_root, exist_ok=True)
    MyLog.info(f"已清理历史JUnit报告数据，目录: {junit_root}")

    # 清空Allure根目录和临时目录
    for dir_path in [ALLURE_RESULTS_ROOT, ALLURE_TEMP_ROOT]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    MyLog.info(f"已清理历史Allure报告数据 → 根目录: {ALLURE_RESULTS_ROOT}, 临时目录: {ALLURE_TEMP_ROOT}")

    # 记录开始时间
    start_time = time.time()
    start_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    MyLog.info(f"开始并行测试 at {start_time_str}")

    try:
        # ==== 使用多进程替代多线程 ====
        with Manager() as manager:
            # 创建共享的事件字典和结果字典
            event_dict = manager.dict()
            result_dict = manager.dict()

            # 收集所有需要管理的文件（包括任务文件和依赖文件）
            all_files = set()
            for task in tasks:
                all_files.add(task["file"])
                if task.get("deps"):
                    for dep in task["deps"]:
                        all_files.add(dep)

            # 初始化事件和结果字典
            for test_file in all_files:
                event_dict[test_file] = manager.Event()
                result_dict[test_file] = None  # 初始化为未执行状态
                MyLog.info(f"初始化事件和结果字典 for: {test_file}")

            # 创建并启动进程
            processes = []
            for task in tasks:
                p = Process(
                    target=process_task,
                    args=(
                        task["file"],
                        task["deps"],
                        task["require_success"],
                        event_dict,
                        result_dict
                    )
                )
                p.start()
                processes.append(p)
                MyLog.info(f"启动进程: {p.pid} 执行 {task['file']}（依赖检查严格模式: {task['require_success']}）")

            # 等待所有进程完成
            for p in processes:
                p.join()
                MyLog.info(f"进程完成: {p.pid}（退出码: {p.exitcode}）")

    except KeyboardInterrupt:
        MyLog.info("用户中断测试执行")
        print("\n用户中断测试执行，正在等待当前进程完成...")
        # 给进程一些时间完成当前任务（避免报告未写完）
        for p in processes:
            if p.is_alive():
                p.join(timeout=10)
        print("正在生成报告...")

    # ========== 统计并输出测试结果 ==========
    end_time = time.time()
    overall_time = end_time - start_time
    formatted_time = format_time(overall_time)

    MyLog.info(f"完成并行测试 at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    MyLog.info(f"一休云接口自动化测试-整体耗时: {formatted_time}")

    # 在控制台显示整体耗时
    print(f"\033[32m一休云接口自动化测试-整体耗时: {formatted_time}\033[0m")

    # ========== 生成Allure报告 ==========
    if os.path.exists(ALLURE_RESULTS_ROOT) and os.listdir(ALLURE_RESULTS_ROOT):
        os.system(f"allure generate {ALLURE_RESULTS_ROOT} -o {allure_report} --clean")

        # 在Allure报告中添加执行时间信息
        report_env_file = os.path.join(allure_report, 'widgets', 'environment.json')
        if os.path.exists(report_env_file):
            try:
                with open(report_env_file, 'r', encoding='utf-8') as f:
                    env_data = json.load(f)
            except:
                env_data = {}
        else:
            env_data = {}

        # 添加执行时间信息
        env_data["执行总耗时"] = formatted_time
        env_data["Allure结果文件数"] = len(os.listdir(ALLURE_RESULTS_ROOT))

        with open(report_env_file, 'w', encoding='utf-8') as f:
            json.dump(env_data, f, ensure_ascii=False, indent=2)

        MyLog.info(f"Allure测试报告生成成功: file://{os.path.abspath(allure_report)}/index.html")
        MyLog.info(f"JUnit报告目录: {junit_root}（共生成 {len(os.listdir(junit_root))} 个文件）")
    else:
        MyLog.info("没有生成Allure测试结果，跳过报告生成")

    MyLog.info("===== 并行测试完成 =====")


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 添加环境变量
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    # 添加 webdriver-manager 相关环境变量
    os.environ['WDM_SSL_VERIFY'] = '0'  # 禁用SSL验证
    os.environ['WDM_LOG_LEVEL'] = '0'  # 禁用 webdriver-manager 日志
    os.environ['WDM_PRINT_FIRST_LINE'] = 'False'  # 禁用首行打印
    # 添加国内镜像源
    os.environ['WDM_CHROMEDRIVER_REPO'] = 'https://cdn.npmmirror.com/binaries/chromedriver'

    print("===== 测试执行程序启动 =====")
    MyLog.info("===== 测试执行程序启动 =====")

    try:
        run_together_tests()  # 并行执行

    finally:
        # 延长延迟，确保子进程的报告写入完成后再终止
        time.sleep(2)
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            try:
                child.terminate()
                MyLog.info(f"终止子进程: {child.pid}")
            except Exception as e:
                MyLog.error(f"终止子进程 {child.pid} 失败: {e}")

    MyLog.info("===== 测试执行程序结束 =====")
    print("===== 测试执行程序结束 =====")
