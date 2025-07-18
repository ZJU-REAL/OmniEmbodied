import logging
from typing import Dict, List, Any, Optional, Union
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class PromptManager:
    """
    提示词管理器，负责加载和格式化提示词模板
    """
    
    def __init__(self, config_name: str = "prompts_config"):
        """
        初始化提示词管理器
        
        Args:
            config_name: 提示词配置名称
        """
        # 加载提示词配置
        config_manager = ConfigManager()
        self.prompts_config = config_manager.get_config(config_name)
        
        # 确保配置加载成功
        if not self.prompts_config:
            logger.warning(f"Unable to load prompt config: {config_name}, using default prompts")
            self.prompts_config = {}
    
    def get_prompt_template(self, mode: str, template_key: str, default_value: str = "") -> str:
        """
        获取指定模式和键的提示词模板
        
        Args:
            mode: 模式名称 (single_agent, centralized, decentralized)
            template_key: 模板键名
            default_value: 默认值，如果找不到模板则返回此值
            
        Returns:
            str: 提示词模板
        """
        mode_config = self.prompts_config.get(mode, {})
        return mode_config.get(template_key, default_value)
    
    def format_template(self, template: str, **kwargs) -> str:
        """
        格式化提示词模板
        
        Args:
            template: 提示词模板
            **kwargs: 格式化参数
            
        Returns:
            str: 格式化后的提示词
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"格式化提示词模板时缺少参数: {e}")
            return template
        except Exception as e:
            logger.exception(f"格式化提示词模板时出错: {e}")
            return template
    
    def get_formatted_prompt(self, mode: str, template_key: str, default_value: str = "", **kwargs) -> str:
        """
        获取并格式化提示词模板
        
        Args:
            mode: 模式名称
            template_key: 模板键名
            default_value: 默认值
            **kwargs: 格式化参数
            
        Returns:
            str: 格式化后的提示词
        """
        template = self.get_prompt_template(mode, template_key, default_value)
        return self.format_template(template, **kwargs)
    
    def format_history(self, mode: str, history: List[Dict[str, Any]], max_entries: int = 20, config: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化历史记录

        Args:
            mode: 模式名称
            history: 历史记录列表
            max_entries: 最大条目数
            config: 历史记录格式配置，可选
                - include_thought: 是否在历史记录中包含Thought内容 (默认: True)
                - show_execution_status: 是否显示执行状态 (默认: True，centralized模式除外)

        Returns:
            str: 格式化后的历史记录
        """
        if not history:
            return ""

        # 获取配置，设置默认值
        if config is None:
            config = {}
        include_thought = config.get('include_thought', True)
        show_execution_status = config.get('show_execution_status', mode != "centralized")
        
        # 获取历史记录模板
        history_template = self.get_prompt_template(mode, "history_template", "Recent Action History:\n{history_entries}")

        # 根据配置决定是否显示execution_status
        if show_execution_status:
            # 显示execution_status
            entry_template = self.get_prompt_template(mode, "history_entry_template", "{index}. Action: {action}, Result: {status}, Message: {message}")
        else:
            # 不显示execution_status
            entry_template = self.get_prompt_template(mode, "history_entry_template", "{index}. Action: {action}, Result: {message}")
        
        # 格式化历史条目
        entries = []
        for i, entry in enumerate(history[-max_entries:]):
            action = entry.get('action', '')
            llm_response = entry.get('llm_response', '')  # 获取完整的LLM回复

            # 支持两种格式：新格式（直接包含status和message）和旧格式（嵌套在result中）
            if 'result' in entry:
                # 旧格式
                result = entry.get('result', {})
                status = result.get('status', '')
                message = result.get('message', '')
            else:
                # 新格式
                status = entry.get('status', '')
                message = entry.get('message', '')

            # 如果有LLM回复，根据配置决定是否显示
            if llm_response and include_thought:
                # 根据配置决定是否显示execution_status
                if show_execution_status:
                    # 显示execution_status
                    formatted_entry = f"{i+1}. {llm_response}\n   Execution Result: {status} - {message}"
                else:
                    # 不显示execution_status
                    formatted_entry = f"{i+1}. {llm_response}\n   Execution Result: {message}"
            else:
                # 不显示LLM回复（Thought），回退到原有格式
                if show_execution_status:
                    # 显示status
                    formatted_entry = self.format_template(entry_template,
                                                          index=i+1,
                                                          action=action,
                                                          status=status,
                                                          message=message)
                else:
                    # 不显示status
                    formatted_entry = self.format_template(entry_template,
                                                          index=i+1,
                                                          action=action,
                                                          message=message)
            entries.append(formatted_entry)
        
        # 组合所有条目
        history_entries = "\n".join(entries)
        
        # 返回完整历史记录
        return self.format_template(history_template, history_entries=history_entries)
    
    def format_messages(self, mode: str, messages: List[Dict[str, Any]], max_entries: int = 20) -> str:
        """
        格式化消息记录
        
        Args:
            mode: 模式名称
            messages: 消息记录列表
            max_entries: 最大条目数
            
        Returns:
            str: 格式化后的消息记录
        """
        if not messages:
            return "No new messages"

        # 获取消息历史模板
        history_template = self.get_prompt_template(mode, "message_history_template", "Received Messages:\n{message_entries}")
        entry_template = self.get_prompt_template(mode, "message_entry_template", "- From {sender_id}: {content}")
        
        # 格式化消息条目
        entries = []
        for msg in messages[-max_entries:]:
            sender_id = msg.get('sender_id', 'unknown')
            content = msg.get('content', '')
            
            formatted_entry = self.format_template(entry_template,
                                                  sender_id=sender_id,
                                                  content=content)
            entries.append(formatted_entry)
        
        # 组合所有条目
        message_entries = "\n".join(entries)
        
        # 返回完整消息历史
        return self.format_template(history_template, message_entries=message_entries)
    
    def add_environment_description(self, prompt: str, agent_id: str, bridge, config: Optional[Dict[str, Any]] = None) -> str:
        """
        为提示词添加环境描述部分
        
        Args:
            prompt: 原始提示词
            agent_id: 智能体ID
            bridge: 模拟器桥接实例
            config: 环境描述配置，可选
                - show_object_properties: 是否显示物体属性
                - only_show_discovered: 是否只显示已发现的内容
                - detail_level: 详细程度 'full'/'room'/'brief'
                
        Returns:
            str: 添加了环境描述的提示词
        """
        if bridge is None:
            return prompt
        
        config = config or {}
        detail_level = config.get('detail_level', 'room')
        
        description = ""
        
        try:
            # 获取智能体当前所在房间
            agent_info = bridge.get_agent_info(agent_id)
            if agent_info and 'location_id' in agent_info:
                room_id = agent_info.get('location_id')
                
                # 根据详细程度选择不同的描述
                if detail_level == 'full':
                    # 完整环境描述
                    description = bridge.describe_environment_natural_language(
                        sim_config={
                            'nlp_show_object_properties': config.get('show_object_properties', False),
                            'nlp_only_show_discovered': config.get('only_show_discovered', True)
                        }
                    )
                elif detail_level == 'room':
                    # 当前房间描述
                    description = bridge.describe_room_natural_language(room_id)
                else:
                    # 简要描述
                    description = bridge.describe_agent_natural_language(agent_id)
        except Exception as e:
            logger.warning(f"获取环境描述时出错: {e}")
            return prompt
        
        # 将环境描述直接作为插值参数传递，而不是尝试找插入点
        if description:
            return self.format_template(prompt, environment_description=description)

        return prompt

    def get_system_prompt_with_actions(self, mode: str, agent_id: str, bridge, default_value: str = "") -> str:
        """
        获取包含动态动作描述的系统提示词

        Args:
            mode: 模式名称 (single_agent, centralized, decentralized)
            agent_id: 智能体ID
            bridge: 模拟器桥接实例
            default_value: 默认值，如果找不到模板则返回此值

        Returns:
            str: 包含动态动作描述的系统提示词
        """
        # 获取系统提示词模板
        system_template = self.get_prompt_template(mode, "system", default_value)

        # 获取通用配置
        common_config = self.prompts_config.get('common', {})
        proximity_rules = common_config.get('proximity_rules', '')
        interaction_rules = common_config.get('interaction_rules', '')
        general_notes = common_config.get('general_notes', '')

        # 获取动态动作描述
        dynamic_actions = self._get_dynamic_actions_description(agent_id, bridge)

        # 格式化模板，插入所有必要的配置
        try:
            return self.format_template(system_template,
                                      dynamic_actions_description=dynamic_actions,
                                      proximity_rules=proximity_rules,
                                      interaction_rules=interaction_rules,
                                      general_notes=general_notes)
        except KeyError as e:
            logger.warning(f"格式化系统提示词时缺少参数: {e}")
            return system_template
        except Exception as e:
            logger.exception(f"格式化系统提示词时出错: {e}")
            return system_template

    def _get_dynamic_actions_description(self, agent_id: str, bridge) -> str:
        """
        获取智能体的动态动作描述

        Args:
            agent_id: 智能体ID
            bridge: 模拟器桥接实例

        Returns:
            str: 动作描述字符串
        """
        if bridge is None:
            return "【可用动作】\n动作信息暂时不可用。"

        try:
            # 使用模拟器桥接获取动作描述（传入单个智能体ID）
            actions_description = bridge.get_agent_supported_actions_description(agent_id)
            if actions_description:
                return f"【可用动作】\n{actions_description}"
            else:
                return "【可用动作】\n动作信息暂时不可用。"
        except Exception as e:
            logger.warning(f"获取动态动作描述时出错: {e}")
            return "【可用动作】\n动作信息暂时不可用。"