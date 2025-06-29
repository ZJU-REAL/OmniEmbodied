from .logger import setup_logger
from .data_loader import DataLoader, load_scene, load_task, get_task_scene, load_complete_scenario
from .simulator_bridge import SimulatorBridge
from .prompt_manager import PromptManager

def create_env_description_config(detail_level='room', show_properties=False, only_discovered=True):
    """
    创建环境描述配置

    Args:
        detail_level: 详细程度，可选 'full'、'room'、'brief'
        show_properties: 是否显示物体属性
        only_discovered: 是否只显示已发现的内容

    Returns:
        dict: 环境描述配置字典
    """
    return {
        'detail_level': detail_level,
        'show_object_properties': show_properties,
        'only_show_discovered': only_discovered
    }

__all__ = [
    'setup_logger',
    'DataLoader',
    'load_scene',
    'load_task',
    'get_task_scene',
    'load_complete_scenario',
    'SimulatorBridge',
    'PromptManager',
    'create_env_description_config'
]