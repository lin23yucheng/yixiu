# -*- coding: UTF-8 -*-
import os
import logging
import time

#

"""[输出控制]
class LogLevel:
    DEBUG = 0
    LOW = 1
    MIDDLE = 2
    HIGH = 3
    HIGHER = 4
    TOP = 5
"""


class LogLevel:
    DEBUG = 0
    LOW = 1
    MIDDLE = 2
    HIGH = 3
    HIGHER = 4
    TOP = 5


# 日志文件输出等级
logFileLv = LogLevel.LOW
# 日志面板输出等级
logPrintLv = LogLevel.DEBUG

# 初始化Log控件信息
logger = logging.getLogger('Logging')
logger.setLevel(level=logging.DEBUG)
formatter = logging.Formatter('%(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)
logger.addHandler(console)


def get_now(time_format="%Y-%m-%d %H:%M:%S"):
    """获得当前时间的字符串
    精确到毫秒
    """
    nowTime = time.time() * 1000
    now = time.strftime(time_format, time.localtime(
        nowTime / 1000)) + "," + "%03d" % (nowTime % 1000)
    return now


class LogType:
    """终端带颜色的输出
    @todo: 将组合写成类，便于快速组合

    @param:[log类型，优先级，颜色代码，可以用类，也可以自己写，规则见注释]
    @note:
    格式：\033[显示方式;文字色;背景色m
    说明:

    文字色            背景色            颜色
    ---------------------------------------
      30                40              黑色
      31                41              红色
      32                42              绿色
      33                43              黃色
      34                44              蓝色
      35                45              紫红色
      36                46              青蓝色
      37                47              白色

    显示方式           意义
    -------------------------
       0           终端默认设置
       1             高亮显示
       4            使用下划线
       5              闪烁
       7             反白显示
       8              不可见

    例子：
    \033[1;31;40m    <!--1-高亮显示 31-文字色红色  40-背景色黑色-->
    \033[0m          <!--采用终端默认设置，即取消颜色设置-->]]]
    """
    DEBUG = ["debug", LogLevel.DEBUG, "\033[37m"]  # 调试
    NORMAL = ["info", LogLevel.LOW, "\033[37m"]  # 默认
    HIGHLIGHT = ["info", LogLevel.MIDDLE, "\033[1;37m"]  # 高亮
    LOGIC = ["info", LogLevel.HIGH, "\033[32m"]  # 逻辑用，绿色
    WARNING = ["warning", LogLevel.HIGHER, "\033[33m"]  # 警告
    ERROR = ["error", LogLevel.TOP, "\033[31m"]  # 错误


def logFileHandler(obj, filename, is_split):
    # 项目路径
    prj_path = os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))  # 当前文件的上一级的上一级目录（增加一级）
    if is_split:
        date, s_time = get_now().split(" ")
        hour = s_time.split(":")[0]
        if filename is None:
            filename = hour
        log_path = prj_path + "/log/{0}".format(date)
    else:
        if filename is None:
            filename = "log"
        log_path = prj_path + "/log/"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log_name = log_path + "/{filename}.log".format(filename=filename)
    with open(log_name, 'a+') as f:
        f.write(obj + "\n")


def printl(obj, color_code):
    # 字体样式拼装
    colorstr = "{0}{1}{2}".format(color_code[2], obj, "\033[0m")
    string = "%s" % colorstr
    getattr(logger, color_code[0])(string)


def log(obj, prefix=LogType.DEBUG, log_name=None, is_split=True):
    """
    日志输出主方法
    :param is_split: 是否日志分离
    :param log_name: 日志名称
    :param obj: 输出内容
    :param prefix: 类型颜色区分
    :return:
    """
    if log_name:
        log_name = "{0}_{1}".format(get_now().split(" ")[0], "_log")
    # 格式拼装
    obj = "{0} - {1} - {2}".format(get_now(), prefix[0].upper(), obj)
    # 输出到控制台
    if not prefix[1] < logPrintLv:
        printl(obj, prefix)

    if not prefix[1] < logFileLv:
        logFileHandler(obj, log_name, is_split)


class Log(object):
    pass


if __name__ == "__main__":
    print("请确认现在在调试")
    log(1111, LogType.WARNING)
