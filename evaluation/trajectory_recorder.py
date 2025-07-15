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
    
    def __init__(self, scenario_id: str, output_dir: str):
        """
        初始化轨迹记录器
        
        Args:
            scenario_id: 场景ID
            output_dir: 输出目录
        """
        self.scenario_id = scenario_id
        self.output_dir = output_dir
        self.lock = threading.Lock()
        
        # 文件路径
        self.trajectory_file = os.path.join(output_dir, f"trajectories/{scenario_id}_trajectory.json")
        self.qa_file = os.path.join(output_dir, f"llm_qa/{scenario_id}_llm_qa.json")
        # 按场景组织执行日志：logs/scenario_id/scenario_execution.json
        self.execution_log_file = os.path.join(output_dir, f"logs/{scenario_id}/scenario_execution.json")
        
        # 确保目录存在
        self._create_directories()
        
        logger.debug(f"📝 轨迹记录器初始化: {scenario_id}")
    
    def _create_directories(self):
        """创建必要的子目录"""
        directories = [
            os.path.dirname(self.trajectory_file),
            os.path.dirname(self.qa_file),
            os.path.dirname(self.execution_log_file)
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def record_action_execution(self, task_index: int, step: int,
                               action: str, status: str,
                               message: str, result: Dict[str, Any],
                               agent_id: str = None) -> None:
        """记录动作执行 - 立即写入磁盘"""
        with self.lock:
            action_data = {
                "action_index": step,
                "action_command": action,
                "execution_status": status,
                "result_message": message,
                "agent_id": agent_id or result.get('agent_id', 'unknown')
            }
            
            # 立即追加到轨迹文件
            self._append_to_trajectory(task_index, action_data)
    
    def record_llm_interaction(self, task_index: int, interaction_index: int,
                              prompt: str, response: str,
                              tokens_used: Dict[str, int], response_time_ms: float,
                              extracted_action: str) -> None:
        """记录LLM交互 - 立即写入磁盘，严格按照文档格式"""
        with self.lock:
            qa_data = {
                "interaction_index": interaction_index,
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "response": response,
                "tokens_used": tokens_used,
                "response_time_ms": response_time_ms,
                "extracted_action": extracted_action
            }

            # 立即追加到QA文件
            self._append_to_qa_file(task_index, qa_data)

    def record_llm_qa(self, instruction: str, output: str, system: str = None) -> None:
        """兼容现有LLMAgent的接口 - 已弃用，不再记录以避免重复"""
        # 这个方法已被弃用，因为会导致重复记录
        # 现在由TaskExecutor通过record_llm_interaction统一记录
        pass

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
            completion_data = {
                "subtask_index": task_index,
                "completed_at": step
            }
            
            # 立即更新轨迹文件
            self._update_task_completion(task_index, completion_data)
    
    def save_execution_log(self, execution_data: Dict[str, Any]) -> None:
        """保存场景执行日志JSON文件"""
        with self.lock:
            temp_file = self.execution_log_file + '.tmp'
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(execution_data, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                
                os.rename(temp_file, self.execution_log_file)
                logger.debug(f"💾 执行日志已保存: {self.execution_log_file}")
                
            except Exception as e:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                logger.error(f"保存执行日志失败: {e}")
                raise
    
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
