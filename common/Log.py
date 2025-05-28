import logging
import os
import time

LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

logger = logging.getLogger()
level = 'info'  # 默认日志级别设为info


def create_file(filename):
    """创建日志文件及目录"""
    try:
        path = filename[0:filename.rfind('/')]
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
        if not os.path.isfile(filename):
            with open(filename, mode='w', encoding='utf-8') as f:
                pass
    except Exception as e:
        print(f"Error creating log file: {e}")


def set_log_level(log_level):
    """设置日志级别"""
    global level
    level = log_level
    logger.setLevel(LEVELS.get(level, logging.INFO))


class MyLog:
    """日志封装类"""
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = path + '/Log/log.log'
    err_file = path + '/Log/err.log'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 创建文件
    create_file(log_file)
    create_file(err_file)

    # 配置处理器
    handler = logging.FileHandler(log_file, encoding='utf-8')
    err_handler = logging.FileHandler(err_file, encoding='utf-8')

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt=date_format
    )
    handler.setFormatter(formatter)
    err_handler.setFormatter(formatter)

    # 添加处理器（仅一次）
    logger.addHandler(handler)
    logger.addHandler(err_handler)

    # 设置日志级别
    logger.setLevel(LEVELS.get(level, logging.INFO))

    @staticmethod
    def debug(log_msg):
        logger.debug(log_msg)

    @staticmethod
    def info(log_msg):
        logger.info(log_msg)

    @staticmethod
    def warning(log_msg):
        logger.warning(log_msg)

    @staticmethod
    def error(log_msg):
        logger.error(log_msg)

    @staticmethod
    def critical(log_msg):
        logger.critical(log_msg)


if __name__ == "__main__":
    # 测试日志功能
    MyLog.debug("This is a debug message")
    MyLog.info("This is an info message")
    MyLog.warning("This is a warning message")
    MyLog.error("This is an error message")
    MyLog.critical("This is a critical message")