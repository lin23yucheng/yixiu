import grpc
import bash.push.bash_pb2 as grpc_api
import bash.push.bash_pb2_grpc as grpc_control
from google.protobuf.json_format import MessageToDict
from threading import Thread
from bash.push.log import *
import json
import re
import random
import os
import time


class BashGrpcMock(Thread):
    def __init__(self, channel, loops):
        Thread.__init__(self)
        self.counter_task = 2100
        self.counter_photo = 1

        # 获取当前脚本所在的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 构建证书文件的绝对路径
        key_path = os.path.join(current_dir, '..', 'crt', 'client.key')
        crt_path = os.path.join(current_dir, '..', 'crt', 'client.crt')
        ca_path = os.path.join(current_dir, '..', 'crt', 'ca.crt')

        with open(key_path, 'rb') as f:
            private_key = f.read()
        with open(crt_path, 'rb') as f:
            certificate_chain = f.read()
        with open(ca_path, 'rb') as f:
            root_certificates = f.read()

        creds = grpc.ssl_channel_credentials(
            root_certificates=root_certificates,
            private_key=private_key,
            certificate_chain=certificate_chain
        )

        self.stub = grpc_control.BashServiceStub(grpc.secure_channel(
            channel, creds,
            options=(('grpc.ssl_target_name_override', "svfactory.com.cn",),)
        ))

        # 构建配置文件的绝对路径
        params_path = os.path.join(current_dir, '..', 'json', 'params_data.json')
        with open(params_path, encoding='utf-8') as a:
            self.result = json.load(a)

        self.img_bytes = []
        # 构建图片目录的绝对路径
        img_path = os.path.join(current_dir, '..', 'images')
        for root, dirs, files in os.walk(img_path):
            for file in files:
                if re.findall(r'(.+?)\.jpg', file):  # 修正正则表达式
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as f:
                        self.img_bytes.append(f.read())

        # 添加空图片列表保护
        if self.img_bytes:
            self.i_r_images = len(self.img_bytes) - 1
        else:
            self.i_r_images = 0
            log("警告: 图片目录中没有找到任何.jpg文件", LogType.WARNING)

        self.loops = loops
        self.fixed_values = [1, 2, 3, 4, 5]
        self.index = 0
        self.last_index = len(self.fixed_values) - 1

    def run(self):
        if self.loops > 0:
            # 根据循环数循环
            for i in range(self.loops):
                nowTime = time.time() * 1000
                now = time.strftime("%Y%m%d%H%M%S", time.localtime(nowTime / 1000)) + "%03d" % (nowTime % 1000)
                # counter_photo = self.counter_photo
                counter_task = self.counter_task
                fixed_value = self.fixed_values[self.index]
                a = random.randint(6, 10)
                image_header = "{0}-{1}-{2}{3}{4}.jpg".format(1166, 9317, 1,
                                                              self.result["image_header"], now)
                # 更新索引以指向下一个值
                self.index = (self.index + 1) % len(self.fixed_values)
                # next_index = (self.index + 1) % len(self.fixed_values)
                if self.index == 0:
                    self.counter_task += 1
                # self.counter_photo += 1
                # if self.counter_photo > 4:
                #     self.counter_photo = 1
                #     self.counter_task += 1
                #     if self.counter_task > 5000:
                #         self.counter_task = 1000
                self.grpc_request(image_header)

        else:
            # 小于等于1时候做死循环
            while 1:
                nowTime = time.time() * 1000
                now = time.strftime("%Y%m%d%H%M%S", time.localtime(nowTime / 1000)) + "%03d" % (nowTime % 1000)
                image_header = "{0}-{1}-{2}{3}{4}.jpg".format(random.randint(1000, 9999), random.randint(10, 99),
                                                              random.randint(1, 13), self.result["image_header"], now)
                self.grpc_request(image_header)

    def grpc_request(self, image_header: str):
        # 开始时间打点
        t = time.perf_counter()
        try:
            response = self.stub.ImageRecheck(
                grpc_api.ImageRecheckRequest(
                    access_token=self.result["access_token"],  # 认证token
                    device_no=self.result["device_no"], product_name=self.result["product_name"],  # 产品名
                    optical_side_id=self.result["optical_side_id"],  # 光学面
                    width=self.result["width"], height=self.result["height"],
                    encoded_image=self.img_bytes[random.randint(0, self.i_r_images)],  # 图片文件流
                    image_header=image_header,  # 图片名
                    result=self.result["DetectionResult"],
                    model_version=self.result["model_version"],  # 模型版本
                    request_type=self.result["request_type"],
                    # 纯测通讯网速的test、测存图，不走前端的 save、不存图，走前端的 simple、和正常，存图+走前端的 normal
                    is_crop=2,  # 是否切图 2 不切 1 切图
                    detection_area_type=2,  # 检测区域类型 1 检测区域内部 2 检测区域外部
                    detection_area=[{"points": [{"x": 2, "y": 3}, {"x": 6, "y": 7},
                                                {"x": 7, "y": 1}, {"x": 4, "y": 9}]}],  # 检测区域
                    detection_comment="检测逻辑说明",  # 检测逻辑说明
                    proto_version="",  # proto 协议版本号
                    system_type=1,  # 系统类型 1 质检 2 EW
                    expand_feature="{}",  # 小版本迭代 json 字符串
                    model_result=json.dumps({
                        "version": "1.0",
                        "jsonVersion": "1.0",
                        "flags": {},
                        "imageWidth": 1400,
                        "imageHeight": 1400,
                        "imageDepth": 1,
                        "imagePath": image_header,
                        "finalRes": "",
                        "deepRes": "NG",
                        "cvRes": "NG",
                        "bashRes": "NG",
                        "dataRes": "NG",
                        "bashUserId": "",
                        "dataModelVersion": "10.7.7",
                        "tryDataRes": "",
                        "tryDataModelVersion": "4.3.2",
                        "shapes": [{"if_model": True,
                                    "model_id": "M1",
                                    "label_type": "1",
                                    "pre_label": "qipao",
                                    "class_id": "",
                                    "class_type": "NG",  # //uncertain（不确定）unconfirmed（疑似不良），ng,ok;
                                    "label": "qipao",
                                    "score": 0.4303,
                                    "shape_type": "rectangle",
                                    "id": "1714032656556765",
                                    "points": [
                                        [
                                            727.0714,
                                            103.0
                                        ],
                                        [
                                            1065.0714,
                                            439.0
                                        ]
                                    ],
                                    "point_arr": [
                                        [
                                            227.07,
                                            284.54
                                        ],
                                        [
                                            225.07,
                                            283.34
                                        ],
                                        [
                                            223.07,
                                            283.34
                                        ],
                                        [
                                            222.07,
                                            285.14
                                        ]
                                    ],
                                    "data_type": 1,  # 深度模型1，cv模型2
                                    "data_result": "NG",  # 数据模型当前版本判定结果{OK、NG}
                                    "try_data_result": "OK",  # 数据模型试跑版本判定结果{OK、NG}
                                    "data_rule_type": 2,  # 规则类型：0 屏蔽 1 过滤，2 转换 ... 7检出
                                    "data_filter_rule_id": 232,  # 如果有转换,转换或过滤规则id
                                    "data_detection_rule_id": 123,  # 对应检出规则ID
                                    "data_rule_kindof": 1,  # 0 保底规则，1 普通规则
                                    "depth_defect_code": "baidian",  # 原始深度检测缺陷码,如果没有转换初始化缺陷码
                                    "upload_cloud": 1,  # 规则检出的缺陷是否上云 1上云（默认），2 不上云
                                    "upload_cloud_rule_type": 1,  # 不上云规则类型 1 数据算法A1 2 脱云算法A2
                                    "upload_cloud_rule_id": 2323,
                                    # 不上云规则id，如果数据规则引发不上云，该id为 0 否则 脱云规则引发不上云，id为脱云规则id
                                    "defect_feature":
                                        {
                                            "max_length": 252.976,
                                            "smoothness": 0.0212465,
                                            "angle": 0,
                                            "curvature": 0.25,
                                            "straight_line": 0,
                                            "length_width_ratio": 0.239837,
                                            "avg_height": 0,
                                            "max_height": 0,
                                            # ......后期会进行扩展
                                        }
                                    },
                                   {"if_model": True,
                                    "model_id": "M1",
                                    "label_type": "1",
                                    "pre_label": "yise",
                                    "class_id": "",
                                    "class_type": "unconfirmed",  # //uncertain（不确定）unconfirmed（疑似不良），ng,ok;
                                    "label": "yise",
                                    "score": 0.4303,
                                    "shape_type": "rectangle",
                                    "id": "1714032656556765",
                                    "points": [
                                        [
                                            332.088888888888,
                                            709.0
                                        ],
                                        [
                                            490.0,
                                            859.0
                                        ]
                                    ],
                                    "point_arr": [
                                        [
                                            227.07,
                                            284.54
                                        ],
                                        [
                                            225.07,
                                            283.34
                                        ],
                                        [
                                            223.07,
                                            283.34
                                        ],
                                        [
                                            222.07,
                                            285.14
                                        ]
                                    ],
                                    "data_type": 1,  # 深度模型1，cv模型2
                                    "data_result": "unconfirmed",  # 数据模型当前版本判定结果{OK、NG}
                                    "try_data_result": "OK",  # 数据模型试跑版本判定结果{OK、NG}
                                    "data_rule_type": 2,  # 规则类型：0 屏蔽 1 过滤，2 转换 ... 7检出
                                    "data_filter_rule_id": 232,  # 如果有转换,转换或过滤规则id
                                    "data_detection_rule_id": 123,  # 对应检出规则ID
                                    "data_rule_kindof": 1,  # 0 保底规则，1 普通规则
                                    "depth_defect_code": "baidian",  # 原始深度检测缺陷码,如果没有转换初始化缺陷码
                                    "upload_cloud": 1,  # 规则检出的缺陷是否上云 1上云（默认），2 不上云
                                    "upload_cloud_rule_type": 1,  # 不上云规则类型 1 数据算法A1 2 脱云算法A2
                                    "upload_cloud_rule_id": 2323,
                                    # 不上云规则id，如果数据规则引发不上云，该id为 0 否则 脱云规则引发不上云，id为脱云规则id
                                    "defect_feature":
                                        {
                                            "max_length": 252.976,
                                            "smoothness": 0.0212465,
                                            "angle": 0,
                                            "curvature": 0.25,
                                            "straight_line": 0,
                                            "length_width_ratio": 0.239837,
                                            "avg_height": 0,
                                            "max_height": 0,
                                            # ......后期会进行扩展
                                        }
                                    },
                                   {"if_model": True,
                                    "model_id": "M1",
                                    "label_type": "1",
                                    "pre_label": "aotudian",
                                    "class_id": "",
                                    "class_type": "NG",  # //uncertain（不确定）unconfirmed（疑似不良），ng,ok;
                                    "label": "aotudian",
                                    "score": 0.4303,
                                    "shape_type": "polygon",
                                    "id": "1714032656556765",
                                    "points": [
                                        [
                                            1046.83,
                                            1119.07
                                        ],
                                        [
                                            1108.83,
                                            1199.07
                                        ],
                                        [
                                            1180.83,
                                            1195.07
                                        ],
                                        [
                                            1248.83,
                                            1081.07
                                        ],
                                        [
                                            1226.83,
                                            1027.07
                                        ],
                                        [
                                            1142.83,
                                            993.07
                                        ],
                                        [
                                            1102.83,
                                            971.07
                                        ],
                                        [
                                            1000.83,
                                            963.07
                                        ],
                                        [
                                            952.83,
                                            1001.07
                                        ],
                                        [
                                            934.83,
                                            1047.07
                                        ],
                                        [
                                            952.83,
                                            1069.07
                                        ],
                                        [
                                            990.83,
                                            1103.07
                                        ]
                                    ],
                                    "point_arr": [
                                        [
                                            227.07,
                                            284.54
                                        ],
                                        [
                                            225.07,
                                            283.34
                                        ],
                                        [
                                            223.07,
                                            283.34
                                        ],
                                        [
                                            222.07,
                                            285.14
                                        ]
                                    ],
                                    "data_type": 1,  # 深度模型1，cv模型2
                                    "data_result": "OK",  # 数据模型当前版本判定结果{OK、NG}
                                    "try_data_result": "OK",  # 数据模型试跑版本判定结果{OK、NG}
                                    "data_rule_type": 2,  # 规则类型：0 屏蔽 1 过滤，2 转换 ... 7检出
                                    "data_filter_rule_id": 232,  # 如果有转换,转换或过滤规则id
                                    "data_detection_rule_id": 123,  # 对应检出规则ID
                                    "data_rule_kindof": 1,  # 0 保底规则，1 普通规则
                                    "depth_defect_code": "baidian",  # 原始深度检测缺陷码,如果没有转换初始化缺陷码
                                    "upload_cloud": 1,  # 规则检出的缺陷是否上云 1上云（默认），2 不上云
                                    "upload_cloud_rule_type": 1,  # 不上云规则类型 1 数据算法A1 2 脱云算法A2
                                    "upload_cloud_rule_id": 2323,
                                    # 不上云规则id，如果数据规则引发不上云，该id为 0 否则 脱云规则引发不上云，id为脱云规则id
                                    "defect_feature":
                                        {
                                            "max_length": 252.976,
                                            "smoothness": 0.0212465,
                                            "angle": 0,
                                            "curvature": 0.25,
                                            "straight_line": 0,
                                            "length_width_ratio": 0.239837,
                                            "avg_height": 0,
                                            "max_height": 0,
                                            # ......后期会进行扩展
                                        }
                                    }

                                   ]
                        # "finalRes": "OK",#最终判定
                        # "deepRes": "ok", #深度判定(模型判定)
                        # "dataRes": "NG", #数据判定（数据算法判定）
                        # "cvResult": "NG"#CV判定 Other,OK,NG
                        # "model_result_list":{}
                    }),
                )
            )
            # 结束时间打点
            cost = f"{time.perf_counter() - t:.8f}"
            # 转换响应格式
            res = json.dumps(MessageToDict(response), ensure_ascii=False)
        except Exception as e:
            # 结束时间打点
            cost = f"{time.perf_counter() - t:.8f}"
            # 处理grpc异常
            res = {"imageRecheckResult": "Exception", "imageHeader": f"{repr(e)}"}
        log(
            f'func {self.grpc_request.__name__}  cost time(s):【{cost}】,【{image_header}】的响应是【{res}】',
            LogType.LOGIC, is_split=False)


def test_logic_manual(config_data=None):
    """手动输入模式"""
    print("测试开始 (手动模式)")
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if config_data is None:
        config_path = os.path.join(current_dir, '..', 'json', 'config.json')
        with open(config_path, encoding='utf-8') as a:
            config = json.load(a)
    else:
        config = config_data

    print("性能Bash工具 - 手动模式")
    i = 1
    for url in config['channel']:
        print(f"{i}.{url}")
        i += 1

    address_no = int(input("请输入GRPC请求编号："))
    i_threads = int(input("请输入线程数："))
    i_loops = int(input("请输入循环数："))

    run_test(config, address_no, i_threads, i_loops)


def test_logic_auto(config_data=None):
    """自动执行模式 - 无输入操作"""
    print("测试开始 (自动模式 - 无输入)")
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if config_data is None:
        config_path = os.path.join(current_dir, '..', 'json', 'config.json')
        with open(config_path, encoding='utf-8') as a:
            config = json.load(a)
    else:
        config = config_data

    # 固定参数 - 无任何输入操作
    address_no = 1  # GRPC请求编号固定为1
    i_threads = 2  # 线程数固定为2
    i_loops = 1  # 循环数固定为1

    print(f"自动模式参数: GRPC请求编号={address_no}, 线程数={i_threads}, 循环数={i_loops}")

    run_test(config, address_no, i_threads, i_loops)

def run_test(config, address_no, i_threads, i_loops):
    """执行测试的通用方法"""
    log("开始测试", LogType.LOGIC)
    l_threads = []
    for i in range(i_threads):
        l_threads.append(BashGrpcMock(config['channel'][address_no - 1], i_loops))
    for thread in l_threads:
        thread.setDaemon(True)
        thread.start()
    for thread in l_threads:
        thread.join()
    log("结束测试", LogType.LOGIC)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # test_logic_manual()
    test_logic_auto()
