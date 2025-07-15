#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embodied Simulator 接口模块

这个模块提供了与模拟器核心组件的接口，允许其他模块导入必要的类和枚举。
"""

# 从模拟器核心导入关键枚举
try:
    # 尝试从simulator模块导入
    from simulator.core.enums import ActionStatus, ActionType, ObjectType
except ImportError:
    # 如果导入失败，定义一个简单的枚举类作为后备
    from enum import Enum, auto
    
    class ActionStatus(Enum):
        """动作执行状态枚举（后备版本）"""
        SUCCESS = auto()       # 动作执行成功
        FAILURE = auto()       # 动作执行失败
        INVALID = auto()       # 动作无效
        PARTIAL = auto()       # 部分成功（如部分探索）
        WAITING = auto()       # 等待其他智能体协作
