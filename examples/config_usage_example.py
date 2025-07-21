#!/usr/bin/env python3
"""配置系统使用示例"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config_manager import get_config_manager
from config.config_utils import (
    get_llm_config, 
    get_agent_config, 
    list_available_configs,
    create_config_backup,
    print_config_summary
)

def main():
    # 获取配置管理器
    config_manager = get_config_manager()
    
    # 1. 基本配置加载
    print("=== 基本配置加载 ===")
    llm_config = get_llm_config()
    print(f"LLM模式: {llm_config.get('mode')}")
    print(f"当前提供商: {llm_config.get('api', {}).get('provider')}")
    
    # 2. 智能体配置加载
    print("\n=== 智能体配置加载 ===")
    single_agent_config = get_agent_config('single_agent')
    print(f"智能体类: {single_agent_config.get('agent_config', {}).get('agent_class')}")
    print(f"最大失败次数: {single_agent_config.get('agent_config', {}).get('max_failures')}")
    
    # 3. 配置节获取
    print("\n=== 配置节获取 ===")
    model_name = config_manager.get_config_section('llm_config', 'api.custom.model')
    print(f"自定义模型名称: {model_name}")
    
    max_steps = config_manager.get_config_section('single_agent_config', 'execution.max_total_steps')
    print(f"最大执行步数: {max_steps}")
    
    # 4. 环境变量支持
    print("\n=== 环境变量支持 ===")
    api_key = config_manager.get_config_section('llm_config', 'api.custom.api_key')
    print(f"API密钥: {api_key[:10]}..." if api_key else "未设置")
    
    # 5. 列出所有配置
    print("\n=== 可用配置列表 ===")
    configs = list_available_configs()
    for category, config_list in configs.items():
        if config_list:
            print(f"{category}: {', '.join(config_list)}")
    
    # 6. 配置备份
    print("\n=== 配置备份 ===")
    backup_success = create_config_backup('llm_config')
    print(f"LLM配置备份: {'成功' if backup_success else '失败'}")
    
    # 7. 配置更新（仅内存）
    print("\n=== 配置更新 ===")
    config_manager.update_config('llm_config', {
        'api': {
            'custom': {
                'temperature': 0.2
            }
        }
    })
    
    updated_temp = config_manager.get_config_section('llm_config', 'api.custom.temperature')
    print(f"更新后的温度: {updated_temp}")
    
    # 8. 运行时覆盖示例
    print("\n=== 运行时覆盖示例 ===")
    config_manager.set_runtime_override('llm_config', 'api.custom.model', 'deepseek-coder')
    config_manager.set_runtime_override('single_agent_config', 'execution.max_total_steps', 500)
    
    # 显示覆盖后的值
    new_model = config_manager.get_config_section('llm_config', 'api.custom.model')
    new_steps = config_manager.get_config_section('single_agent_config', 'execution.max_total_steps')
    print(f"覆盖后的模型: {new_model}")
    print(f"覆盖后的最大步数: {new_steps}")
    
    # 9. 配置摘要
    print("\n=== 配置摘要 ===")
    print_config_summary('single_agent_config')

if __name__ == "__main__":
    main()
