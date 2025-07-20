"""
轨迹记录器 - 严格按照文档要求记录步骤级信息
"""

import os
import json
import csv
import threading
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TrajectoryRecorder:
    """轨迹记录器 - 每次操作都立即写入磁盘"""
    
    def __init__(self, scenario_id: str, output_dir: str, agent_type: str = "multi"):
        """
        初始化轨迹记录器

        Args:
            scenario_id: 场景ID
            output_dir: 输出目录
            agent_type: 智能体类型 ("single" 或 "multi")
        """
        self.scenario_id = scenario_id
        self.output_dir = output_dir
        self.agent_type = agent_type
        self.lock = threading.Lock()

        # 计数器
        self._action_step_counter = 0  # 动作步骤计数器
        self._qa_interaction_counter = 0  # QA交互计数器

        # 关闭状态标记
        self._closed = False

        # 文件路径
        self.trajectory_file = os.path.join(output_dir, f"trajectories/{scenario_id}_trajectory.json")
        self.qa_file = os.path.join(output_dir, f"llm_qa/{scenario_id}_llm_qa.json")

        # 确保目录存在
        self._create_directories()

        logger.debug(f"📝 轨迹记录器初始化: {scenario_id}")
    
    def _create_directories(self):
        """创建必要的子目录"""
        directories = [
            os.path.dirname(self.trajectory_file),
            os.path.dirname(self.qa_file)
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def record_action_execution(self, task_index: int, step: int,
                               action: str, status: str,
                               message: str, result: Dict[str, Any],
                               agent_id: str = None) -> None:
        """记录动作执行 - 立即写入磁盘，支持单智能体和多智能体格式"""
        with self.lock:
            # 在锁内检查关闭状态，避免竞态条件
            if self._closed:
                logger.warning(f"⚠️ 尝试在已关闭的轨迹记录器上记录: {self.scenario_id}")
                return
            # 递增动作步骤计数器
            self._action_step_counter += 1
            actual_step = self._action_step_counter

            # 确保status是字符串格式，处理ActionStatus枚举
            if hasattr(status, 'name'):
                status_str = status.name
            elif hasattr(status, 'value'):
                status_str = str(status.value)
            else:
                status_str = str(status)

            # 基于智能体架构类型构建相应的轨迹格式
            if self.agent_type == "multi":
                # 多智能体模式：为每个智能体生成独立记录
                action_data_list = self._build_multi_agent_action_data(
                    actual_step, action, status_str, message, result, agent_id
                )
                logger.debug(f"📝 记录多智能体轨迹: {len(action_data_list)} 个智能体记录")

                # 为每个智能体记录分别追加到轨迹文件
                for action_data in action_data_list:
                    self._append_to_trajectory(task_index, action_data)
            else:
                # 单智能体模式：标准格式
                action_data = self._build_single_agent_action_data(
                    actual_step, action, status_str, message, result, agent_id
                )
                logger.debug(f"📝 记录单智能体轨迹: {action_data['agent_id']}")

                # 立即追加到轨迹文件
                self._append_to_trajectory(task_index, action_data)

    def _build_single_agent_action_data(self, step: int, action: str, status_str: str,
                                       message: str, result: Dict[str, Any],
                                       agent_id: str = None) -> Dict[str, Any]:
        """构建单智能体轨迹数据格式"""
        return {
            "action_index": step,
            "action_command": action,
            "execution_status": status_str,
            "result_message": message,
            "agent_id": agent_id or result.get('agent_id', 'unknown')
        }

    def _build_multi_agent_action_data(self, step: int, action: str, status_str: str,
                                      message: str, result: Dict[str, Any],
                                      agent_id: str = None) -> List[Dict[str, Any]]:
        """构建多智能体（中心化）轨迹数据格式 - 返回两个智能体的独立记录"""
        action_data_list = []

        # 安全检查：确保result不为None且包含coordination_details
        if not isinstance(result, dict) or 'coordination_details' not in result:
            logger.warning(f"result缺少coordination_details: {result}")
            # 回退到原始格式
            action_data_list.append(self._build_single_agent_action_data(
                step, action, status_str, message, result or {}, agent_id
            ))
            return action_data_list

        coordination_details = result['coordination_details']
        if not isinstance(coordination_details, dict):
            logger.warning(f"coordination_details不是字典类型: {type(coordination_details)}")
            action_data_list.append(self._build_single_agent_action_data(
                step, action, status_str, message, result, agent_id
            ))
            return action_data_list

        # 为每个智能体创建独立的轨迹记录
        for current_agent_id, agent_result in coordination_details.items():
            # 安全检查：确保agent_result不为None
            if not isinstance(agent_result, dict):
                logger.warning(f"智能体 {current_agent_id} 的结果不是字典类型: {type(agent_result)}")
                continue

            # 提取智能体的具体动作
            agent_action = self._extract_agent_action_from_result(agent_result, action)

            # 确保status是字符串格式
            agent_status = agent_result.get('status', status_str)
            if hasattr(agent_status, 'name'):
                agent_status_str = agent_status.name
            elif hasattr(agent_status, 'value'):
                agent_status_str = str(agent_status.value)
            else:
                agent_status_str = str(agent_status) if agent_status is not None else status_str

            # 构建单智能体格式的记录
            agent_action_data = {
                "action_index": step,
                "action_command": agent_action,
                "execution_status": agent_status_str,
                "result_message": agent_result.get('message', message) or message,
                "agent_id": current_agent_id
            }

            action_data_list.append(agent_action_data)

        return action_data_list

    def _extract_agent_action_from_result(self, agent_result: Dict[str, Any],
                                         original_action: str) -> str:
        """从智能体结果中提取具体的动作命令"""
        # 安全检查：确保agent_result不为None且为字典
        if not isinstance(agent_result, dict):
            logger.warning(f"agent_result不是字典类型: {type(agent_result)}")
            return self._get_default_action(original_action)

        # 尝试从result中提取动作信息
        if 'result' in agent_result and isinstance(agent_result['result'], dict):
            result = agent_result['result']

            # 检查是否有location相关的动作
            if 'new_location_id' in result:
                return f"GOTO {result['new_location_id']}"

            # 检查是否有物品相关的动作
            if 'grabbed_object_id' in result:
                return f"GRAB {result['grabbed_object_id']}"

            if 'placed_object_id' in result and 'target_id' in result:
                return f"PLACE {result['placed_object_id']} on {result['target_id']}"

        return self._get_default_action(original_action)

    def _get_default_action(self, original_action: str) -> str:
        """获取默认动作"""
        # 如果无法提取具体动作，尝试从原始动作中推断
        if original_action == "COORDINATE":
            # 对于COORDINATE动作，返回通用的EXPLORE作为默认值
            return "EXPLORE"

        return original_action or "EXPLORE"

    def _serialize_coordination_details(self, coordination_details: Dict[str, Any]) -> Dict[str, Any]:
        """序列化coordination_details，确保ActionStatus枚举被转换为字符串"""
        serialized = {}
        for agent_id, details in coordination_details.items():
            if isinstance(details, dict):
                serialized_details = details.copy()
                # 转换status字段
                if 'status' in serialized_details:
                    status = serialized_details['status']
                    if hasattr(status, 'name'):
                        serialized_details['status'] = status.name
                    elif hasattr(status, 'value'):
                        serialized_details['status'] = str(status.value)
                    else:
                        serialized_details['status'] = str(status)
                serialized[agent_id] = serialized_details
            else:
                serialized[agent_id] = details
        return serialized

    def record_llm_interaction(self, task_index: int, interaction_index: int,
                              prompt: str, response: str,
                              tokens_used: Dict[str, int], response_time_ms: float,
                              extracted_action: str) -> None:
        """记录LLM交互 - 立即写入磁盘，根据智能体类型使用不同格式"""
        with self.lock:
            # 在锁内检查关闭状态，避免竞态条件
            if self._closed:
                logger.warning(f"⚠️ 尝试在已关闭的轨迹记录器上记录LLM交互: {self.scenario_id}")
                return
            if self.agent_type == "single":
                # 单智能体：使用传入的interaction_index，保持原有行为
                actual_interaction_index = interaction_index if interaction_index > 0 else (self._qa_interaction_counter + 1)
                self._qa_interaction_counter = max(self._qa_interaction_counter, actual_interaction_index)
            else:
                # 多智能体：内部管理交互索引
                self._qa_interaction_counter += 1
                actual_interaction_index = self._qa_interaction_counter

            qa_data = {
                "interaction_index": actual_interaction_index,
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "response": response,
                "tokens_used": tokens_used,
                "response_time_ms": response_time_ms
            }

            logger.debug(f"📝 记录LLM交互 ({self.agent_type}): interaction_index={actual_interaction_index}, tokens={tokens_used}")

            # 立即追加到QA文件
            self._append_to_qa_file(task_index, qa_data)

    def record_llm_qa(self, instruction: str, output: str, system: str = None) -> None:
        """废弃的接口 - 请使用record_llm_interaction"""
        logger.warning("record_llm_qa接口已废弃，请使用record_llm_interaction接口")

        # 为了向后兼容，仍然提供基本功能，但不推荐使用
        # 注意：索引将由record_llm_interaction内部管理
        self.record_llm_interaction(
            task_index=1,  # 默认任务索引
            interaction_index=0,  # 将被内部管理的索引覆盖
            prompt=instruction,
            response=output,
            tokens_used={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},  # 默认token统计
            response_time_ms=0.0,  # 默认响应时间
            extracted_action=""  # 空字符串，不再使用
        )

    def _extract_action_from_response(self, response: str) -> str:
        """从LLM响应中提取动作命令"""
        try:
            # 查找 "Action: " 后面的内容
            if "Action:" in response:
                action_line = response.split("Action:")[1].split("\n")[0].strip()
                return action_line
            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"
    
    def record_task_completion(self, task_index: int, step: int) -> None:
        """记录任务完成状态 - 立即写入磁盘"""
        with self.lock:
            # 在锁内检查关闭状态，避免竞态条件
            if self._closed:
                logger.warning(f"⚠️ 尝试在已关闭的轨迹记录器上记录任务完成: {self.scenario_id}")
                return
            completion_data = {
                "subtask_index": task_index,
                "completed_at": step
            }
            
            # 立即更新轨迹文件
            self._update_task_completion(task_index, completion_data)
    


    def close(self):
        """关闭记录器：强制保存数据并清理内存"""
        if self._closed:
            return  # 避免重复关闭

        with self.lock:
            try:
                # 标记为已关闭（在保存之前，避免新的记录请求）
                self._closed = True

                # 1. 强制保存轨迹数据（即使没有新数据，也确保文件存在）
                trajectory_data = self._load_trajectory_data()
                if trajectory_data:
                    self._save_trajectory_immediately(trajectory_data)
                    logger.debug(f"💾 轨迹数据已强制保存: {self.scenario_id}")
                else:
                    logger.debug(f"📝 轨迹记录器关闭时无数据需要保存: {self.scenario_id}")

                # 2. 强制保存QA数据
                qa_data = self._load_qa_data()
                if qa_data:
                    self._save_qa_immediately(qa_data)
                    logger.debug(f"💾 QA数据已强制保存: {self.scenario_id}")

                logger.debug(f"📝 轨迹记录器已关闭: {self.scenario_id}")

            except Exception as e:
                logger.error(f"❌ 关闭轨迹记录器失败: {e}")
                # 即使保存失败，也要标记为已关闭
                self._closed = True
                raise

    def __del__(self):
        """析构函数 - 确保数据不丢失"""
        if not self._closed:
            logger.warning(f"⚠️ 轨迹记录器未正确关闭，执行紧急保存: {self.scenario_id}")
            try:
                self.close()
            except Exception as e:
                logger.error(f"❌ 析构时保存失败: {e}")

    def _append_to_trajectory(self, task_index: int, action_data: Dict[str, Any]):
        """追加动作到轨迹文件"""
        # 读取现有轨迹数据
        trajectory_data = self._load_trajectory_data()
        
        # 确保有足够的任务条目
        while len(trajectory_data) < task_index:
            trajectory_data.append({
                "action_sequence": [],
                "subtask_completions": []
            })
        
        # 追加新动作到指定任务
        trajectory_data[task_index - 1]["action_sequence"].append(action_data)
        
        # 立即写入磁盘
        self._save_trajectory_immediately(trajectory_data)
    
    def _append_to_qa_file(self, task_index: int, qa_data: Dict[str, Any]):
        """追加QA交互到QA文件"""
        # 读取现有QA数据
        qa_data_list = self._load_qa_data()
        
        # 确保有足够的任务条目
        while len(qa_data_list) < task_index:
            qa_data_list.append({"qa_interactions": []})
        
        # 追加新交互到指定任务
        qa_data_list[task_index - 1]["qa_interactions"].append(qa_data)
        
        # 立即写入磁盘
        self._save_qa_immediately(qa_data_list)
    
    def _update_task_completion(self, task_index: int, completion_data: Dict[str, Any]):
        """更新任务完成状态"""
        trajectory_data = self._load_trajectory_data()
        
        # 确保有足够的任务条目
        while len(trajectory_data) < task_index:
            trajectory_data.append({
                "action_sequence": [],
                "subtask_completions": []
            })
        
        # 更新指定任务的完成状态
        trajectory_data[task_index - 1]["subtask_completions"].append(completion_data)
        
        # 立即写入磁盘
        self._save_trajectory_immediately(trajectory_data)
    
    def _save_trajectory_immediately(self, trajectory_data: List[Dict]):
        """立即保存轨迹数据到磁盘"""
        temp_file = self.trajectory_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 强制写入磁盘
            
            # 原子性重命名
            os.rename(temp_file, self.trajectory_file)
            logger.debug(f"💾 轨迹已保存: {self.trajectory_file}")
            
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            logger.error(f"保存轨迹失败: {e}")
            raise
    
    def _save_qa_immediately(self, qa_data: List[Dict]):
        """立即保存QA数据到磁盘"""
        temp_file = self.qa_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(qa_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 强制写入磁盘
            
            # 原子性重命名
            os.rename(temp_file, self.qa_file)
            logger.debug(f"💾 QA记录已保存: {self.qa_file}")
            
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            logger.error(f"保存QA记录失败: {e}")
            raise
    
    def _load_trajectory_data(self) -> List[Dict]:
        """加载现有轨迹数据"""
        if os.path.exists(self.trajectory_file):
            try:
                with open(self.trajectory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"加载轨迹数据失败: {e}")
        return []
    
    def _load_qa_data(self) -> List[Dict]:
        """加载现有QA数据"""
        if os.path.exists(self.qa_file):
            try:
                with open(self.qa_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"加载QA数据失败: {e}")
        return []


class CSVRecorder:
    """CSV记录器 - 实时写入CSV数据"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.lock = threading.Lock()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        
        # 初始化CSV文件头
        self._initialize_csv_header()
    
    def _initialize_csv_header(self):
        """初始化CSV文件头"""
        if not os.path.exists(self.csv_file):
            header = [
                'timestamp', 'scenario_id', 'task_index', 'task_description',
                'task_category', 'agent_type', 'status', 'task_executed',
                'subtask_completed', 'model_claimed_done', 'actual_completion_step',
                'done_command_step', 'total_steps', 'successful_steps', 'failed_steps',
                'command_success_rate', 'true_positive', 'false_positive', 'true_negative',
                'false_negative', 'start_time', 'end_time', 'duration_seconds',
                'llm_interactions'
            ]
            self.write_header(header)
    
    def write_header(self, header: List[str]):
        """写入CSV头部"""
        with self.lock:
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                f.flush()
                os.fsync(f.fileno())
    
    def append_row(self, row_data: List[Any]):
        """立即写入CSV数据到磁盘"""
        with self.lock:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
                f.flush()  # 立即刷新到磁盘
                os.fsync(f.fileno())  # 强制写入磁盘
