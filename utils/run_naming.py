#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行命名工具 - 为每次评测运行生成唯一的名称
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional


class RunNamingManager:
    """
    运行命名管理器 - 生成基于时间和配置的唯一运行名称
    """
    
    @staticmethod
    def generate_run_name(agent_type: str, task_type: str, scenario_id: str,
                         config_name: str = None, custom_suffix: str = None) -> str:
        """
        Generate run name

        Args:
            agent_type: Agent type ('single' or 'multi')
            task_type: Task type ('sequential' or 'combined')
            scenario_id: Scenario ID
            config_name: Configuration file name (optional)
            custom_suffix: Custom suffix (optional)

        Returns:
            str: Formatted run name
        """
        # Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Basic name components
        components = [
            timestamp,
            f"{agent_type}_{task_type}",
            f"scenario_{scenario_id}"
        ]

        # Add configuration name (if not default configuration)
        if config_name and not config_name.endswith('_config'):
            config_name = config_name.replace('_config', '')
            if config_name not in ['single_agent', 'centralized', 'decentralized']:
                components.append(f"config_{config_name}")
        
        # Add custom suffix
        if custom_suffix:
            # Clean custom suffix, keep only alphanumeric characters and underscores
            clean_suffix = re.sub(r'[^a-zA-Z0-9_]', '_', custom_suffix)
            components.append(clean_suffix)
        
        return "_".join(components)
    
    @staticmethod
    def generate_output_directory(base_output_dir: str, run_name: str) -> str:
        """
        Generate output directory path

        Args:
            base_output_dir: Base output directory
            run_name: Run name

        Returns:
            str: Complete output directory path
        """
        return f"{base_output_dir}/{run_name}"
    
    @staticmethod
    def parse_run_name(run_name: str) -> Dict[str, str]:
        """
        解析运行名称，提取其中的信息
        
        Args:
            run_name: 运行名称
            
        Returns:
            Dict: 解析出的信息
        """
        parts = run_name.split('_')
        
        result = {
            'timestamp': None,
            'agent_type': None,
            'task_type': None,
            'scenario_id': None,
            'config_name': None,
            'custom_suffix': None
        }
        
        if len(parts) >= 1:
            # 尝试解析时间戳
            if len(parts[0]) == 8 and parts[0].isdigit():
                if len(parts) >= 2 and len(parts[1]) == 6 and parts[1].isdigit():
                    result['timestamp'] = f"{parts[0]}_{parts[1]}"
                    parts = parts[2:]
                else:
                    result['timestamp'] = parts[0]
                    parts = parts[1:]
        
        # 解析智能体类型和任务类型
        if len(parts) >= 1:
            agent_task = parts[0]
            if '_' in agent_task:
                agent_type, task_type = agent_task.split('_', 1)
                if agent_type in ['single', 'multi'] and task_type in ['sequential', 'combined']:
                    result['agent_type'] = agent_type
                    result['task_type'] = task_type
                    parts = parts[1:]
        
        # 解析场景ID
        if len(parts) >= 1 and parts[0].startswith('scenario_'):
            result['scenario_id'] = parts[0].replace('scenario_', '')
            parts = parts[1:]
        
        # 解析配置名称
        if len(parts) >= 1 and parts[0].startswith('config_'):
            result['config_name'] = parts[0].replace('config_', '')
            parts = parts[1:]
        
        # 剩余部分作为自定义后缀
        if parts:
            result['custom_suffix'] = '_'.join(parts)
        
        return result
    
    @staticmethod
    def get_run_description(run_name: str) -> str:
        """
        获取运行的可读描述
        
        Args:
            run_name: 运行名称
            
        Returns:
            str: 可读的运行描述
        """
        info = RunNamingManager.parse_run_name(run_name)
        
        description_parts = []
        
        # 时间信息
        if info['timestamp']:
            try:
                if '_' in info['timestamp']:
                    date_part, time_part = info['timestamp'].split('_')
                    formatted_time = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                else:
                    date_part = info['timestamp']
                    formatted_time = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                description_parts.append(f"时间: {formatted_time}")
            except:
                description_parts.append(f"时间: {info['timestamp']}")
        
        # 模式信息
        if info['agent_type'] and info['task_type']:
            mode_desc = {
                'single_sequential': '单智能体逐个评测',
                'single_combined': '单智能体混合评测',
                'single_independent': '单智能体独立评测',
                'multi_sequential': '多智能体逐个评测',
                'multi_combined': '多智能体混合评测',
                'multi_independent': '多智能体独立评测'
            }.get(f"{info['agent_type']}_{info['task_type']}", f"{info['agent_type']}_{info['task_type']}")
            description_parts.append(f"模式: {mode_desc}")
        
        # 场景信息
        if info['scenario_id']:
            description_parts.append(f"场景: {info['scenario_id']}")
        
        # 配置信息
        if info['config_name']:
            description_parts.append(f"配置: {info['config_name']}")
        
        # 自定义后缀
        if info['custom_suffix']:
            description_parts.append(f"标签: {info['custom_suffix']}")
        
        return " | ".join(description_parts) if description_parts else run_name
    
    @staticmethod
    def validate_run_name(run_name: str) -> bool:
        """
        验证运行名称的有效性
        
        Args:
            run_name: 运行名称
            
        Returns:
            bool: 是否有效
        """
        # 检查基本格式
        if not run_name or not isinstance(run_name, str):
            return False
        
        # 检查字符（只允许字母、数字、下划线、连字符）
        if not re.match(r'^[a-zA-Z0-9_-]+$', run_name):
            return False
        
        # 检查长度
        if len(run_name) > 200:
            return False
        
        return True
    
    @staticmethod
    def suggest_run_name_from_config(config: Dict[str, Any], scenario_id: str = None) -> str:
        """
        根据配置建议运行名称
        
        Args:
            config: 配置字典
            scenario_id: 场景ID
            
        Returns:
            str: 建议的运行名称
        """
        # 从配置中提取信息
        evaluation_config = config.get('evaluation', {})
        
        # 确定智能体类型
        agent_type = 'single'  # 默认单智能体
        if 'coordinator' in config or 'worker_agents' in config:
            agent_type = 'multi'
        elif 'autonomous_agent' in config or 'communication' in config:
            agent_type = 'multi'
        
        # 确定任务类型
        task_type = evaluation_config.get('task_type', 'sequential')
        
        # 使用默认场景ID如果未提供
        if not scenario_id:
            scenario_id = '00001'
        
        return RunNamingManager.generate_run_name(
            agent_type=agent_type,
            task_type=task_type,
            scenario_id=scenario_id
        )
