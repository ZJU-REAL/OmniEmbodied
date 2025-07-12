from enum import Enum, auto

class ObjectType(Enum):
    """物体类型枚举"""
    STATIC = auto()        # 静态物体，如墙壁、地板
    INTERACTABLE = auto()  # 可交互物体，如门、抽屉、开关
    GRABBABLE = auto()     # 可抓取物体，如杯子、玩具、书本
    FURNITURE = auto()     # 家具，如沙发、床、桌子，有尺寸和重量属性
    ITEM = auto()          # 小型物品，如书、杯子，有易碎性等属性

class ActionType(Enum):
    """动作类型枚举"""
    GOTO = auto()          # 移动到指定位置
    GRAB = auto()          # 抓取物体
    PLACE = auto()         # 放置物体
    LOOK = auto()          # 观察环境
    EXPLORE = auto()       # 探索当前房间，发现家具和物品
    
    # 新添加的操作类型
    CORP_GRAB = auto()     # 合作抓取重物，需要多个智能体协作
    CORP_GOTO = auto()     # 合作移动，需要多个智能体协作
    CORP_PLACE = auto()    # 合作放置重物，需要多个智能体协作
    ATTRIBUTE = auto()     # 基于属性的动作，从CSV文件导入配置

class ActionStatus(Enum):
    """动作执行状态枚举"""
    SUCCESS = auto()       # 动作执行成功
    FAILURE = auto()       # 动作执行失败
    INVALID = auto()       # 动作无效
    PARTIAL = auto()       # 部分成功（如部分探索）
    WAITING = auto()       # 等待其他智能体协作 