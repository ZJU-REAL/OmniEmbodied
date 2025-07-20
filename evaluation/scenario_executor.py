"""
场景执行器 - 管理单个场景的完整执行
"""

import os
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from OmniSimulator import SimulationEngine
from .trajectory_recorder import TrajectoryRecorder, CSVRecorder
from .agent_adapter import AgentAdapter
from .task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class ScenarioExecutor:
    """场景执行器 - 管理单个场景的完整执行"""
    
    def __init__(self, scenario_id: str, config: Dict[str, Any], output_dir: str, task_indices: List[int] = None):
        """
        初始化场景执行器

        Args:
            scenario_id: 场景ID
            config: 配置字典
            output_dir: 输出目录
            task_indices: 要执行的任务索引列表，None表示执行所有任务
        """
        self.scenario_id = scenario_id
        self.config = config
        self.output_dir = output_dir
        self.task_indices = task_indices or []  # 空列表表示执行所有任务

        # 从配置中获取数据目录（严格验证）
        self.data_dir = self._get_data_dir_from_config()
        self.scene_dir = os.path.join(self.data_dir, 'scene')
        self.task_dir = os.path.join(self.data_dir, 'task')

        # 加载场景和任务数据
        self.scene_data = self._load_scene_data()
        self.task_data = self._load_task_data()
        
        # 初始化模拟器
        self.simulator = self._initialize_simulator()
        
        # 创建轨迹记录器，根据智能体架构正确设置类型
        agent_class = self.config.get('agent_config', {}).get('agent_class', '')
        # 根据智能体架构正确设置类型
        if 'centralized' in agent_class.lower():
            agent_type = "multi"  # centralized是多智能体架构
        elif 'single' in agent_class.lower():
            agent_type = "single"  # single是单智能体架构
        else:
            agent_type = "single"  # 默认单智能体
        self.trajectory_recorder = TrajectoryRecorder(scenario_id, output_dir, agent_type)
        
        # 创建CSV记录器
        csv_file = os.path.join(output_dir, "subtask_execution_log.csv")
        self.csv_recorder = CSVRecorder(csv_file)
        
        logger.info(f"🏠 场景执行器初始化完成: {scenario_id}")

    def _get_data_dir_from_config(self) -> str:
        """
        从配置中获取数据目录

        Returns:
            str: 数据目录绝对路径

        Raises:
            KeyError: 配置中缺少data_dir
            FileNotFoundError: 数据目录不存在
        """
        if 'data_dir' not in self.config:
            raise KeyError("配置中缺少必需的 'data_dir' 设置")

        data_dir = self.config['data_dir']

        # 转换为绝对路径
        if not os.path.isabs(data_dir):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)  # evaluation -> OmniEmbodied
            data_dir = os.path.join(project_root, data_dir)

        # 严格验证
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"配置的数据目录不存在: {data_dir}")

        return data_dir

    def _load_scene_data(self) -> Dict[str, Any]:
        """
        加载场景数据

        Raises:
            FileNotFoundError: 场景文件不存在
        """
        scene_file = os.path.join(self.scene_dir, f"{self.scenario_id}_scene.json")

        if not os.path.exists(scene_file):
            raise FileNotFoundError(f"场景文件不存在: {scene_file}")

        try:
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            logger.debug(f"📄 场景数据已加载: {scene_file}")
            return scene_data
        except json.JSONDecodeError as e:
            raise ValueError(f"场景文件格式错误: {scene_file}, 错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载场景文件失败: {scene_file}, 错误: {e}")
    
    def _load_task_data(self) -> Dict[str, Any]:
        """
        加载任务数据

        Raises:
            FileNotFoundError: 任务文件不存在
        """
        task_file = os.path.join(self.task_dir, f"{self.scenario_id}_task.json")

        if not os.path.exists(task_file):
            raise FileNotFoundError(f"任务文件不存在: {task_file}")

        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)

            tasks = task_data.get('tasks', [])
            logger.info(f"📋 任务数据已加载: {len(tasks)} 个任务")
            return task_data
        except json.JSONDecodeError as e:
            raise ValueError(f"任务文件格式错误: {task_file}, 错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载任务文件失败: {task_file}, 错误: {e}")
    
    def _initialize_simulator(self) -> SimulationEngine:
        """初始化模拟器"""
        try:
            # 根据配置确定智能体数量
            agent_config = self.config.get('agent_config', {})
            agent_class = agent_config.get('agent_class', '')

            # 判断是否为中心化多智能体模式
            if 'centralized' in agent_class:
                agent_count = 2  # 中心化模式需要2个智能体
            else:
                agent_count = 1  # 单智能体模式创建1个智能体

            # 创建模拟器配置，确保创建正确数量的智能体
            simulator_config = {
                'agent_count': agent_count,
                'agent_init_mode': 'default',  # 使用默认初始化模式
                'visualization': {'enabled': False},
                'task_verification': {'enabled': True}
            }

            simulator = SimulationEngine(config=simulator_config)

            # 使用initialize方法加载场景
            scene_file = os.path.join(self.scene_dir, f"{self.scenario_id}_scene.json")
            success = simulator.initialize(scene_file)

            if not success:
                raise RuntimeError(f"模拟器初始化失败: {scene_file}")

            # 设置任务数据和验证器
            if hasattr(simulator, 'set_task_data') and self.task_data:
                simulator.set_task_data(self.task_data)
                logger.debug("✅ 已设置任务数据和验证器")

            logger.info(f"🎮 模拟器初始化完成，场景已加载: {self.scenario_id}")
            return simulator

        except Exception as e:
            logger.error(f"❌ 模拟器初始化失败: {e}")
            raise
    
    def execute_scenario(self, agent_type: str, task_type: str) -> Dict[str, Any]:
        """
        执行完整场景
        
        Args:
            agent_type: 智能体类型 ('single', 'centralized', 'decentralized')
            task_type: 任务类型 ('sequential', 'combined', 'independent')
            
        Returns:
            Dict: 场景执行结果
        """
        logger.info(f"🚀 开始执行场景 {self.scenario_id} - {agent_type}_{task_type}")
        
        start_time = datetime.now()
        
        try:
            # 创建智能体适配器
            agent_adapter = AgentAdapter(agent_type, self.config, self.simulator, self.trajectory_recorder)
            
            # 根据task_type选择执行策略
            if task_type == 'sequential':
                result = self._execute_sequential_tasks(agent_adapter)
            elif task_type == 'combined':
                result = self._execute_combined_tasks(agent_adapter)
            elif task_type == 'independent':
                result = self._execute_independent_tasks(agent_adapter)
            else:
                raise ValueError(f"不支持的任务类型: {task_type}")
            
            # 计算总执行时间
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # 生成场景级汇总
            scenario_result = self._generate_scenario_result(
                result, agent_type, task_type, start_time, end_time, total_duration
            )
            

            
            logger.info(f"✅ 场景 {self.scenario_id} 执行完成")
            return scenario_result
            
        except Exception as e:
            logger.error(f"❌ 场景 {self.scenario_id} 执行失败: {e}")

            # 即使出现异常，也尝试保存已有的执行日志
            try:
                end_time = datetime.now()
                total_duration = (end_time - start_time).total_seconds()

                # 异常情况下的任务结果已通过CSV记录保存
                partial_task_results = getattr(self, '_partial_task_results', [])
                logger.debug(f"📝 异常情况下已完成 {len(partial_task_results)} 个任务的CSV记录")

                # 生成部分结果用于保存场景级日志
                partial_result = {
                    'task_results': partial_task_results,
                    'mode': task_type,
                    'execution_time': total_duration,
                    'summary': {'error': str(e), 'interrupted': True}
                }

                logger.info("📝 异常情况下的CSV记录已保存")
            except Exception as save_error:
                logger.error(f"保存异常情况下的执行日志失败: {save_error}")

            raise
    
    def _execute_sequential_tasks(self, agent_adapter: AgentAdapter) -> Dict[str, Any]:
        """Sequential模式：逐个执行任务，任务间清空历史"""
        logger.info("📋 执行Sequential模式任务")

        all_tasks = self.task_data.get('tasks', [])

        # 根据任务筛选确定要执行的任务
        if self.task_indices:
            # 有具体的任务索引，只执行这些任务
            tasks_to_execute = [(i, all_tasks[i]) for i in self.task_indices if i < len(all_tasks)]
            logger.info(f"📋 任务筛选：执行 {len(tasks_to_execute)}/{len(all_tasks)} 个任务")
        else:
            # 没有筛选，执行所有任务
            tasks_to_execute = [(i, task) for i, task in enumerate(all_tasks)]
            logger.info(f"📋 执行所有 {len(tasks_to_execute)} 个任务")

        task_results = []
        
        # 创建任务执行器
        task_executor = TaskExecutor(self.simulator, agent_adapter, self.trajectory_recorder)

        # 获取每个任务的最大步数配置
        max_steps_per_task = self.config.get('execution', {}).get('max_steps_per_task', 50)

        for exec_index, (original_index, task) in enumerate(tasks_to_execute):
            task_index = original_index + 1  # 使用原始任务索引（从1开始）

            logger.info(f"🎯 执行任务 {task_index} (筛选后第{exec_index + 1}个): {task.get('task_description', 'Unknown')[:50]}...")

            # 执行任务
            task_result = task_executor.execute_task(task, task_index, max_steps_per_task)
            task_results.append(task_result)

            # 记录到CSV
            try:
                self._record_task_to_csv(task_result)
                logger.debug(f"📊 任务 {task_index} 已记录到CSV")
            except Exception as csv_error:
                logger.error(f"❌ 记录任务 {task_index} 到CSV失败: {csv_error}")
                # 尝试重新初始化CSV记录器
                try:
                    csv_file = os.path.join(self.output_dir, "subtask_execution_log.csv")
                    self.csv_recorder = CSVRecorder(csv_file)
                    self._record_task_to_csv(task_result)
                    logger.info(f"✅ CSV记录器重新初始化成功，任务 {task_index} 已记录")
                except Exception as retry_error:
                    logger.error(f"❌ CSV记录器重新初始化也失败: {retry_error}")



            # Sequential模式：只有模型输出DONE才继续下一个任务
            if not task_result.get('model_claimed_done', False):
                logger.warning(f"⚠️ 任务 {task_index} 模型未输出DONE，Sequential模式停止执行后续任务")
                break

            # 任务间重置智能体状态（清空历史）
            if exec_index < len(tasks_to_execute) - 1:  # 不是最后一个任务
                agent_adapter.reset()
                logger.debug(f"🔄 任务 {task_index} 完成后重置智能体状态")
        
        return {
            'mode': 'sequential',
            'task_results': task_results,
            'total_tasks': len(all_tasks),
            'executed_tasks': len(tasks_to_execute),
            'filtered_task_indices': self.task_indices
        }
    
    def _execute_combined_tasks(self, agent_adapter: AgentAdapter) -> Dict[str, Any]:
        """Combined模式：所有任务拼接执行，保持历史"""
        logger.info("📋 执行Combined模式任务")
        
        all_tasks = self.task_data.get('tasks', [])

        # 根据任务筛选确定要执行的任务
        if self.task_indices:
            # 有具体的任务索引，只执行这些任务
            tasks_to_execute = [all_tasks[i] for i in self.task_indices if i < len(all_tasks)]
            logger.info(f"📋 任务筛选：执行 {len(tasks_to_execute)}/{len(all_tasks)} 个任务")
        else:
            # 没有筛选，执行所有任务
            tasks_to_execute = all_tasks
            logger.info(f"📋 执行所有 {len(tasks_to_execute)} 个任务")

        # 将筛选后的任务描述拼接成一个长任务
        combined_description = "Please complete the following tasks: \n"
        for i, task in enumerate(tasks_to_execute):
            combined_description += f"{i+1}. {task.get('task_description', '')}\n"
        
        # 创建合并任务
        combined_task = {
            'task_description': combined_description,
            'task_category': 'combined',
            'subtasks': tasks_to_execute
        }
        
        # 创建任务执行器
        task_executor = TaskExecutor(self.simulator, agent_adapter, self.trajectory_recorder)
        
        # 执行合并任务（使用更多步数）
        max_steps = self.config.get('execution', {}).get('max_total_steps', 200)
        combined_result = task_executor.execute_task(combined_task, 1, max_steps)

        # 记录到CSV
        try:
            self._record_task_to_csv(combined_result)
            logger.debug(f"📊 Combined任务已记录到CSV")
        except Exception as csv_error:
            logger.error(f"❌ 记录Combined任务到CSV失败: {csv_error}")


        
        return {
            'mode': 'combined',
            'task_results': [combined_result],
            'total_tasks': len(all_tasks),
            'executed_tasks': len(tasks_to_execute),
            'filtered_task_indices': self.task_indices,
            'combined_task': True
        }
    
    def _execute_independent_tasks(self, agent_adapter: AgentAdapter) -> Dict[str, Any]:
        """Independent模式：每个任务在全新环境中执行"""
        logger.info("📋 执行Independent模式任务")

        all_tasks = self.task_data.get('tasks', [])

        # 根据任务筛选确定要执行的任务
        if self.task_indices:
            # 有具体的任务索引，只执行这些任务
            tasks_to_execute = [(i, all_tasks[i]) for i in self.task_indices if i < len(all_tasks)]
            logger.info(f"📋 任务筛选：执行 {len(tasks_to_execute)}/{len(all_tasks)} 个任务")
        else:
            # 没有筛选，执行所有任务
            tasks_to_execute = [(i, task) for i, task in enumerate(all_tasks)]
            logger.info(f"📋 执行所有 {len(tasks_to_execute)} 个任务")

        task_results = []

        # 初始化部分结果记录，用于异常情况下的日志保存
        self._partial_task_results = task_results

        for exec_index, (original_index, task) in enumerate(tasks_to_execute):
            task_index = original_index + 1  # 使用原始任务索引（从1开始）
            task_trajectory_recorder = None

            logger.info(f"🔄 Independent任务 {task_index} (筛选后第{exec_index + 1}/{len(tasks_to_execute)}个): {task.get('task_description', 'Unknown')[:50]}...")

            try:
                # 重新初始化模拟器（全新环境）
                self.simulator = self._initialize_simulator()

                # 为每个独立任务创建独立的轨迹记录器，使用任务特定的scenario_id
                from .trajectory_recorder import TrajectoryRecorder
                task_scenario_id = f"{self.scenario_id}_task_{task_index:05d}"
                task_trajectory_recorder = TrajectoryRecorder(
                    scenario_id=task_scenario_id,
                    output_dir=self.output_dir,
                    agent_type=agent_adapter.agent_type
                )

                # 重新创建智能体适配器（全新状态，使用独立的轨迹记录器）
                fresh_agent_adapter = AgentAdapter(
                    agent_adapter.agent_type, self.config, self.simulator, task_trajectory_recorder
                )

                # 创建任务执行器（使用独立的轨迹记录器）
                task_executor = TaskExecutor(self.simulator, fresh_agent_adapter, task_trajectory_recorder)

                # 获取每个任务的最大步数配置
                max_steps_per_task = self.config.get('execution', {}).get('max_steps_per_task', 50)

                # 执行任务
                task_result = task_executor.execute_task(task, task_index, max_steps_per_task)
                task_results.append(task_result)

                # 记录到CSV
                try:
                    self._record_task_to_csv(task_result)
                    logger.debug(f"📊 Independent任务 {task_index} 已记录到CSV")
                except Exception as csv_error:
                    logger.error(f"❌ 记录Independent任务 {task_index} 到CSV失败: {csv_error}")



                # Independent模式：只有模型输出DONE才继续下一个任务
                if not task_result.get('model_claimed_done', False):
                    logger.warning(f"⚠️ 任务 {task_index} 模型未输出DONE，Independent模式停止执行后续任务")
                    break

            except Exception as task_error:
                logger.error(f"❌ 任务 {task_index} 执行失败: {task_error}")
                raise
            finally:
                # 关键：无论成功还是失败，都要关闭轨迹记录器
                if task_trajectory_recorder is not None:
                    try:
                        task_trajectory_recorder.close()
                        logger.debug(f"✅ 任务 {task_index} 轨迹记录器已关闭")
                    except Exception as close_error:
                        logger.error(f"❌ 关闭任务 {task_index} 轨迹记录器失败: {close_error}")

                    # 清理引用
                    del task_trajectory_recorder

        return {
            'mode': 'independent',
            'task_results': task_results,
            'total_tasks': len(all_tasks),
            'executed_tasks': len(tasks_to_execute),
            'filtered_task_indices': self.task_indices
        }
    
    def _record_task_to_csv(self, task_result: Dict[str, Any]):
        """记录任务结果到CSV"""
        try:
            # 获取评估结果
            eval_result = task_result.get('evaluation_result', {})

            # 检测智能体类型
            agent_type = 'single'  # 默认值
            agent_config = self.config.get('agent_config', {})
            agent_class = agent_config.get('agent_class', '')
            if 'centralized' in agent_class:
                agent_type = 'centralized'
            elif 'decentralized' in agent_class:
                agent_type = 'decentralized'

            csv_row = [
                datetime.now().isoformat(),  # timestamp
                self.scenario_id,  # scenario_id
                task_result.get('task_index'),  # task_index
                task_result.get('task_description'),  # task_description
                task_result.get('task_category'),  # task_category
                agent_type,  # agent_type (动态检测)
                task_result.get('status'),  # status
                task_result.get('task_executed'),  # task_executed
                task_result.get('subtask_completed'),  # subtask_completed
                task_result.get('model_claimed_done'),  # model_claimed_done
                task_result.get('actual_completion_step'),  # actual_completion_step
                task_result.get('done_command_step'),  # done_command_step
                task_result.get('total_steps'),  # total_steps
                task_result.get('successful_steps'),  # successful_steps
                task_result.get('failed_steps'),  # failed_steps
                task_result.get('command_success_rate'),  # command_success_rate
                # 添加四种评估情况
                eval_result.get('true_positive', False),  # true_positive
                eval_result.get('false_positive', False),  # false_positive
                eval_result.get('true_negative', False),  # true_negative
                eval_result.get('false_negative', False),  # false_negative
                task_result.get('start_time'),  # start_time
                task_result.get('end_time'),  # end_time
                task_result.get('duration_seconds'),  # duration_seconds
                task_result.get('llm_interactions')  # llm_interactions
            ]
            
            self.csv_recorder.append_row(csv_row)
            
        except Exception as e:
            logger.error(f"记录CSV失败: {e}")
    
    def _generate_scenario_result(self, execution_result: Dict[str, Any], 
                                 agent_type: str, task_type: str,
                                 start_time: datetime, end_time: datetime,
                                 total_duration: float) -> Dict[str, Any]:
        """生成场景级汇总结果"""
        task_results = execution_result.get('task_results', [])
        total_tasks = len(task_results)
        
        # 统计完成情况
        completed_tasks = sum(1 for result in task_results if result.get('subtask_completed', False))
        failed_tasks = total_tasks - completed_tasks
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # 统计步数和交互
        total_steps = sum(result.get('total_steps', 0) for result in task_results)
        total_llm_interactions = sum(result.get('llm_interactions', 0) for result in task_results)
        
        return {
            'scenario_id': self.scenario_id,
            'agent_type': agent_type,
            'task_type': task_type,
            'status': 'completed' if failed_tasks == 0 else 'partial',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration': total_duration,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'completion_rate': completion_rate,
            'total_steps': total_steps,
            'total_llm_interactions': total_llm_interactions,
            'task_results': task_results,
            'execution_log': {
                'scenario_id': self.scenario_id,
                'evaluation_mode': task_type,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_seconds': total_duration,
                'tasks': [self._format_task_for_log(result) for result in task_results]
            }
        }
    
    def _format_task_for_log(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化任务结果用于执行日志"""
        return {
            'task_index': task_result.get('task_index'),
            'task_description': task_result.get('task_description'),
            'task_category': task_result.get('task_category'),
            'status': task_result.get('status'),
            'total_steps': task_result.get('total_steps'),
            'llm_interactions': task_result.get('llm_interactions'),
            'duration_seconds': task_result.get('duration_seconds'),
            'completion_analysis': {
                'model_claimed_completion': task_result.get('model_claimed_done'),
                'actually_completed': task_result.get('subtask_completed'),
                'completion_accuracy': 'correct' if task_result.get('subtask_completed') else 'failed',
                'done_step': task_result.get('done_command_step', -1),
                'actual_completion_step': task_result.get('actual_completion_step', -1)
            }
        }
    



