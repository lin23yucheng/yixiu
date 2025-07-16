import os
import json
import configparser
import subprocess
import logging
from pathlib import Path
import allure
import pytest
import importlib.util

# 推图命令
fat_command = "main.exe test --grpc=fat-yixiu-brainstorm-grpc.svfactory.com:9181 -m 1"

# 初始化日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# 添加处理器到日志记录器
logger.addHandler(ch)

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def run_renaming_scripts():
    """执行2D和3D图像重命名脚本"""
    try:
        logger.info("开始执行2D和3D图像重命名脚本")

        # 导入并执行2D重命名脚本
        spec_2d = importlib.util.spec_from_file_location(
            "update_2d_name",
            PROJECT_ROOT / "common" / "update_2d_name.py"
        )
        module_2d = importlib.util.module_from_spec(spec_2d)
        spec_2d.loader.exec_module(module_2d)
        module_2d.rename_files_and_modify_json()
        logger.info("2D图像重命名完成")

        # 导入并执行3D重命名脚本
        spec_3d = importlib.util.spec_from_file_location(
            "update_3d_name",
            PROJECT_ROOT / "common" / "update_3d_name.py"
        )
        module_3d = importlib.util.module_from_spec(spec_3d)
        spec_3d.loader.exec_module(module_3d)
        module_3d.rename_files_and_modify_json()
        logger.info("3D图像重命名完成")

        return True

    except Exception as e:
        logger.error(f"执行重命名脚本时出错: {str(e)}")
        return False


def update_data_json():
    """更新data.json文件内容"""
    try:
        # 1. 读取accessToken.txt
        token_path = PROJECT_ROOT / "testdata" / "accessToken.txt"
        access_token = ""
        if token_path.exists():
            with open(token_path, 'r') as f:
                access_token = f.read().strip()
            logger.info(f"成功读取Token文件: {token_path}")
        else:
            logger.warning(f"Token文件不存在: {token_path}")
            return False

        # 2. 读取配置文件获取miai-product-code
        config_path = PROJECT_ROOT / "config" / "env_config.ini"
        miai_product_code = ""
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)
            if 'global' in config:
                try:
                    miai_product_code = config.get('global', 'miai-product-code')
                    logger.info(f"成功读取miai-product-code: {miai_product_code}")
                except configparser.NoOptionError:
                    logger.warning("配置文件中缺少miai-product-code字段")
                    return False
            else:
                logger.warning("配置文件中缺少global节")
                return False
        else:
            logger.warning(f"配置文件不存在: {config_path}")
            return False

        # 3. 修改data.json
        data_json_path = PROJECT_ROOT / "testdata" / "brainstormGRpcClient" / "2.0" / "testdata" / "1" / "data.json"
        if data_json_path.exists():
            with open(data_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新字段
            data["access_token"] = access_token
            data["device_no"] = miai_product_code
            data["product_name"] = miai_product_code

            # 写回文件
            with open(data_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            logger.info(f"成功更新data.json: {data_json_path}")

            # 记录更新后的内容到Allure报告
            updated_content = json.dumps(data, indent=4, ensure_ascii=False)
            allure.attach(
                updated_content,
                name="更新后的data.json内容",
                attachment_type=allure.attachment_type.JSON
            )

            return True
        else:
            logger.error(f"data.json文件不存在: {data_json_path}")
            return False

    except Exception as e:
        logger.error(f"更新data.json时出错: {str(e)}")
        return False


def execute_grpc_command():
    """执行GRPC命令"""
    try:
        # 目标目录
        target_dir = PROJECT_ROOT / "testdata" / "brainstormGRpcClient" / "2.0"

        # 切换到目标目录
        os.chdir(target_dir)
        logger.info(f"切换到目录: {target_dir}")

        # 记录当前目录内容到报告
        dir_contents = "\n".join(os.listdir(target_dir))
        allure.attach(
            dir_contents,
            name="目标目录内容",
            attachment_type=allure.attachment_type.TEXT
        )

        # 执行命令
        logger.info(f"执行命令: {fat_command}")
        result = subprocess.run(
            fat_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将 stderr 重定向到 stdout
            text=True,
            encoding='utf-8'
        )

        # 记录输出
        if result.stdout:
            logger.info(f"命令标准输出:\n{result.stdout}")

        if result.stderr:
            # 检查内容是否包含错误关键字
            if "ERROR" in result.stderr or "WARNING" in result.stderr:
                logger.warning(f"命令错误输出:\n{result.stderr}")
            else:
                logger.info(f"命令日志输出:\n{result.stderr}")  # 作为普通日志记录

        # 将输出附加到Allure报告
        allure.attach(
            result.stdout if result.stdout else "无输出",
            name="命令标准输出",
            attachment_type=allure.attachment_type.TEXT
        )

        if result.stderr:
            # 根据内容决定附件名称
            attachment_name = "命令错误输出" if ("ERROR" in result.stderr) else "命令日志输出"
            allure.attach(
                result.stderr,
                name=attachment_name,
                attachment_type=allure.attachment_type.TEXT
            )

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e}")
        logger.error(f"错误输出:\n{e.stderr}")

        # 附加错误信息到报告
        allure.attach(
            f"命令执行失败: {str(e)}\n错误输出:\n{e.stderr}",
            name="命令执行错误",
            attachment_type=allure.attachment_type.TEXT
        )

        return False
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")

        # 附加错误信息到报告
        allure.attach(
            f"执行命令时出错: {str(e)}",
            name="命令执行错误",
            attachment_type=allure.attachment_type.TEXT
        )

        return False


@allure.feature("GRPC命令执行")
class TestStandardPushMap:
    @allure.story("更新配置并执行GRPC命令")
    def test_execute_grpc_command(self):
        """测试更新配置并执行GRPC命令"""
        # 步骤0: 执行2D和3D图像重命名
        with allure.step("执行2D和3D图像重命名"):
            renaming_success = run_renaming_scripts()
            assert renaming_success, "2D/3D图像重命名失败"

            # 在Allure报告中记录结果
            allure.attach(
                f"重命名结果: {'成功' if renaming_success else '失败'}",
                name="图像重命名状态",
                attachment_type=allure.attachment_type.TEXT
            )

        # 如果重命名失败，直接终止测试
        if not renaming_success:
            pytest.fail("2D/3D图像重命名失败，终止测试")

        # 步骤1: 更新data.json
        with allure.step("更新data.json配置"):
            update_success = update_data_json()

            # 使用标准的Python断言替代自定义断言
            assert update_success, "更新data.json失败"

            # 在Allure报告中记录更新结果
            allure.attach(
                f"更新结果: {'成功' if update_success else '失败'}",
                name="data.json更新状态",
                attachment_type=allure.attachment_type.TEXT
            )

        # 步骤2: 执行GRPC命令
        with allure.step("执行GRPC命令"):
            command_success = execute_grpc_command()

            # 使用标准的Python断言替代自定义断言
            assert command_success, "执行GRPC命令失败"

            # 在Allure报告中记录执行结果
            allure.attach(
                f"命令执行结果: {'成功' if command_success else '失败'}",
                name="GRPC命令执行状态",
                attachment_type=allure.attachment_type.TEXT
            )


if __name__ == "__main__":
    # 直接运行时的测试逻辑
    print("===== 开始执行GRPC命令测试 =====")

    # 执行2D和3D图像重命名
    print("--- 执行2D和3D图像重命名 ---")
    if run_renaming_scripts():
        print("2D/3D图像重命名成功")

        # 更新data.json
        if update_data_json():
            print("data.json更新成功")

            # 执行命令
            if execute_grpc_command():
                print("GRPC命令执行成功")
            else:
                print("GRPC命令执行失败")
        else:
            print("data.json更新失败，终止执行")
    else:
        print("2D/3D图像重命名失败，终止执行")

    print("===== 测试结束 =====")
