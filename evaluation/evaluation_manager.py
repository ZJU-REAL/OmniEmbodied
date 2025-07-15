"""
评测管理器 - 统一评测管理和场景级并行执行
"""

import os
import json
import yaml
import logging
import signal
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from config.config_manager import ConfigManager
from .scenario_selector import ScenarioSelector
from .scenario_executor import ScenarioExecutor

logger = logging.getLogger(__name__)


class EvaluationManager:
    """评测管理器 - 统一评测管理和场景级并行执行"""
    
    def __init__(self, config_file: str, agent_type: str, task_type: str, 
                 scenario_selection: Dict[str, Any], custom_suffix: str = None):
        """
        初始化评测管理器
        
        Args:
            config_file: 配置文件名
            agent_type: 智能体类型 ('single', 'centralized', 'decentralized')
            task_type: 任务类型 ('sequential', 'combined', 'independent')
            scenario_selection: 场景选择配置
            custom_suffix: 自定义后缀
        """
        self.config_file = config_file
        self.agent_type = agent_type
        self.task_type = task_type
        self.custom_suffix = custom_suffix or 'demo'
        
        # 加载配置
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config(config_file)
        
        # 选择场景
        self.scenario_list = ScenarioSelector.get_scenario_list(self.config, scenario_selection)
        
        # 生成运行名称和输出目录
        self.run_name = self._generate_run_name()
        self.output_dir = self._create_output_directory()
        
        # 并行配置
        parallel_config = self.config.get('parallel_evaluation', {})
        max_parallel = parallel_config.get('scenario_parallelism', {}).get('max_parallel_scenarios', 2)
        self.parallel_count = min(len(self.scenario_list), max_parallel)
        
        # 任务统计
        self.task_stats = {}

        # 场景结果存储（用于紧急保存）
        self._scenario_results = []

        # 运行开始时间
        self.start_time = datetime.now().isoformat()

        # 运行ID
        self.run_id = self.run_name

        # 注册信号处理器
        self._register_signal_handlers()

        # 保存实验配置
        self._save_experiment_config()

        logger.info(f"🚀 评测管理器初始化完成: {self.run_name}")
        logger.info(f"📊 场景数量: {len(self.scenario_list)}, 并行数: {self.parallel_count}")
    
    def _generate_run_name(self) -> str:
        """生成运行名称"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scenario_range = self._format_scenario_range()
        return f"{timestamp}_{self.agent_type}_{self.task_type}_{scenario_range}_{self.custom_suffix}"
    
    def _format_scenario_range(self) -> str:
        """格式化场景范围字符串"""
        if len(self.scenario_list) == 1:
            return self.scenario_list[0]
        elif len(self.scenario_list) <= 3:
            return "_".join(self.scenario_list)
        else:
            return f"{self.scenario_list[0]}_to_{self.scenario_list[-1]}"
    
    def _create_output_directory(self) -> str:
        """创建输出目录"""
        base_output_dir = self.config.get('evaluation', {}).get('output', {}).get('output_directory', 'output')
        output_dir = os.path.join(base_output_dir, self.run_name)
        
        # 创建必要的子目录
        subdirs = ['trajectories', 'llm_qa', 'logs']
        for subdir in subdirs:
            os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
        
        logger.info(f"📁 输出目录已创建: {output_dir}")
        return output_dir

    def _save_experiment_config(self):
        """保存本次实验的配置信息"""
        try:
            # 获取模型配置信息
            agent_config = self.config.get('agent_config', {})
            model_info = self._extract_model_info(agent_config)

            # 构建实验配置
            experiment_config = {
                'experiment_info': {
                    'run_name': self.run_name,
                    'timestamp': datetime.now().isoformat(),
                    'config_file': self.config_file,
                    'agent_type': self.agent_type,
                    'task_type': self.task_type,
                    'custom_suffix': self.custom_suffix
                },
                'model_config': model_info,
                'scenarios': {
                    'scenario_list': self.scenario_list,
                    'scenario_count': len(self.scenario_list),
                    'selection_mode': self.config.get('evaluation', {}).get('scenario_selection', {}).get('mode', 'unknown')
                },
                'execution_config': {
                    'parallel_count': self.parallel_count,
                    'max_total_steps': self.config.get('execution', {}).get('max_total_steps', 200),
                    'max_steps_per_task': self.config.get('execution', {}).get('max_steps_per_task', 50)
                },
                'evaluation_settings': self.config.get('evaluation', {}),
                'parallel_settings': self.config.get('parallel_evaluation', {})
            }

            # 保存为YAML文件
            config_file = os.path.join(self.output_dir, 'experiment_config.yaml')
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(experiment_config, f, default_flow_style=False, allow_unicode=True, indent=2)

            logger.info(f"📋 实验配置已保存: experiment_config.yaml")

        except Exception as e:
            logger.error(f"保存实验配置失败: {e}")

    def _extract_model_info(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """从智能体配置中提取模型信息"""
        model_info = {
            'agent_class': agent_config.get('agent_class', 'unknown'),
            'max_failures': agent_config.get('max_failures', 3),
            'max_history': agent_config.get('max_history', 50)
        }

        # 尝试从LLM配置中提取模型信息
        try:
            llm_config_manager = ConfigManager()
            llm_config = llm_config_manager.get_config('llm_config')

            if llm_config:
                model_info['llm_mode'] = llm_config.get('mode', 'unknown')

                # 获取API配置
                api_config = llm_config.get('api', {})
                provider = api_config.get('provider', 'unknown')
                model_info['provider'] = provider

                # 根据provider获取具体模型信息
                if provider in api_config:
                    provider_config = api_config[provider]
                    model_info['model_name'] = provider_config.get('model', 'unknown')
                    model_info['temperature'] = provider_config.get('temperature', 0.7)
                    model_info['max_tokens'] = provider_config.get('max_tokens', 1024)

                    # 不保存API密钥等敏感信息
                    if 'endpoint' in provider_config:
                        model_info['api_endpoint'] = provider_config['endpoint']

        except Exception as e:
            logger.warning(f"无法提取LLM配置信息: {e}")

        return model_info

    def run_evaluation(self) -> Dict[str, Any]:
        """运行评测"""
        logger.info(f"🎯 开始评测: {self.run_name}")
        
        start_time = datetime.now()
        
        try:
            if len(self.scenario_list) == 1:
                # 单场景直接执行
                scenario_results = self._execute_single_scenario()
            else:
                # 多场景并行执行
                scenario_results = self._execute_parallel_scenarios()
            
            # 计算总执行时间
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # 生成运行摘要
            run_summary = self._generate_run_summary(
                scenario_results, start_time, end_time, total_duration
            )
            
            # 保存运行摘要
            self._save_run_summary(run_summary)
            
            logger.info(f"✅ 评测完成: {self.run_name}")
            return run_summary
            
        except Exception as e:
            logger.error(f"❌ 评测失败: {e}")
            raise
    
    def _execute_single_scenario(self) -> Dict[str, Any]:
        """执行单个场景"""
        scenario_id = self.scenario_list[0]
        logger.info(f"🔄 执行场景: {scenario_id}")
        
        try:
            scenario_executor = ScenarioExecutor(scenario_id, self.config, self.output_dir)
            result = scenario_executor.execute_scenario(self.agent_type, self.task_type)
            
            # 更新任务统计
            self._update_task_statistics(result)
            
            return {scenario_id: result}
            
        except Exception as e:
            logger.error(f"❌ 场景 {scenario_id} 执行失败: {e}")
            return {scenario_id: {'status': 'failed', 'error': str(e)}}
    
    def _execute_parallel_scenarios(self) -> Dict[str, Any]:
        """并行执行多个场景"""
        logger.info(f"🔄 并行执行 {len(self.scenario_list)} 个场景")
        
        scenario_results = {}
        
        self._executor = ProcessPoolExecutor(max_workers=self.parallel_count)
        try:
            # 提交所有场景任务
            future_to_scenario = {
                self._executor.submit(
                    execute_scenario_standalone,
                    scenario_id, self.config, self.output_dir,
                    self.agent_type, self.task_type
                ): scenario_id
                for scenario_id in self.scenario_list
            }
            
            # 收集结果
            for future in as_completed(future_to_scenario):
                scenario_id = future_to_scenario[future]
                try:
                    result = future.result()
                    scenario_results[scenario_id] = result

                    # 更新场景结果存储（用于紧急保存）
                    self._scenario_results.append({
                        'scenario_id': scenario_id,
                        'result': result,
                        'completed_at': datetime.now().isoformat()
                    })

                    # 更新任务统计
                    self._update_task_statistics(result)

                    logger.info(f"✅ 场景 {scenario_id} 执行完成")

                except Exception as e:
                    logger.error(f"❌ 场景 {scenario_id} 执行失败: {e}")
                    error_result = {'status': 'failed', 'error': str(e)}
                    scenario_results[scenario_id] = error_result

                    # 也要记录失败的场景
                    self._scenario_results.append({
                        'scenario_id': scenario_id,
                        'result': error_result,
                        'completed_at': datetime.now().isoformat()
                    })

        finally:
            # 确保executor被正确关闭
            if hasattr(self, '_executor') and self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None

        return scenario_results
    
    def _update_task_statistics(self, scenario_result: Dict[str, Any]):
        """更新任务统计信息"""
        task_results = scenario_result.get('task_results', [])
        
        for task_result in task_results:
            category = task_result.get('task_category', 'unknown')
            
            if category not in self.task_stats:
                self.task_stats[category] = {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'model_claimed_tasks': 0
                }
            
            self.task_stats[category]['total_tasks'] += 1
            
            if task_result.get('subtask_completed', False):
                self.task_stats[category]['completed_tasks'] += 1
            
            if task_result.get('model_claimed_done', False):
                self.task_stats[category]['model_claimed_tasks'] += 1
    
    def _generate_run_summary(self, scenario_results: Dict[str, Any],
                             start_time: datetime, end_time: datetime,
                             total_duration: float) -> Dict[str, Any]:
        """生成运行摘要"""
        # 计算总体统计
        total_scenarios = len(scenario_results)
        successful_scenarios = sum(1 for result in scenario_results.values() 
                                 if result.get('status') != 'failed')
        
        total_tasks = sum(result.get('total_tasks', 0) for result in scenario_results.values())
        total_completed_tasks = sum(result.get('completed_tasks', 0) for result in scenario_results.values())
        total_model_claimed_tasks = sum(
            len([task for task in result.get('task_results', []) 
                if task.get('model_claimed_done', False)])
            for result in scenario_results.values()
        )
        
        # 计算完成率和准确率
        overall_completion_rate = total_completed_tasks / total_tasks if total_tasks > 0 else 0.0
        overall_completion_accuracy = (
            total_completed_tasks / total_model_claimed_tasks 
            if total_model_claimed_tasks > 0 else 0.0
        )
        
        # 计算任务类型统计
        task_category_statistics = {}
        for category, stats in self.task_stats.items():
            completion_rate = stats['completed_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0.0
            task_category_statistics[category] = {
                'total_tasks': stats['total_tasks'],
                'completed_tasks': stats['completed_tasks'],
                'model_claimed_tasks': stats['model_claimed_tasks'],
                'completion_rate': completion_rate
            }
        
        # 计算并行效率
        parallel_efficiency = self.parallel_count if total_scenarios > 1 else 1.0
        
        return {
            'run_info': {
                'run_name': self.run_name,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration': total_duration,
                'evaluation_mode': self.task_type,
                'agent_type': self.agent_type,
                'parallel_count': self.parallel_count,
                'total_scenarios': total_scenarios,
                'scenario_range': self._format_scenario_range()
            },
            'task_category_statistics': task_category_statistics,
            'overall_summary': {
                'total_scenarios': total_scenarios,
                'successful_scenarios': successful_scenarios,
                'total_tasks': total_tasks,
                'total_completed_tasks': total_completed_tasks,
                'overall_completion_rate': overall_completion_rate,
                'total_model_claimed_tasks': total_model_claimed_tasks,
                'overall_completion_accuracy': overall_completion_accuracy,
                'average_duration_per_scenario': total_duration / total_scenarios if total_scenarios > 0 else 0.0,
                'parallel_efficiency': parallel_efficiency
            },
            'scenario_results': scenario_results
        }
    
    def _save_run_summary(self, run_summary: Dict[str, Any]):
        """保存运行摘要"""
        summary_file = os.path.join(self.output_dir, 'run_summary.json')
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(run_summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📊 运行摘要已保存: {summary_file}")
            
        except Exception as e:
            logger.error(f"保存运行摘要失败: {e}")
    
    def _register_signal_handlers(self):
        """注册信号处理器"""
        def signal_handler(signum, frame):
            logger.info("🛑 接收到中断信号，正在保存数据...")

            # 如果有正在运行的进程池，尝试关闭
            if hasattr(self, '_executor') and self._executor:
                logger.info("🔄 正在关闭进程池...")
                try:
                    self._executor.shutdown(wait=False)
                    logger.info("✅ 进程池已关闭")
                except Exception as e:
                    logger.warning(f"关闭进程池时出错: {e}")

            # 保存当前数据
            try:
                # 生成紧急运行摘要
                emergency_summary = {
                    'run_info': {
                        'run_id': getattr(self, 'run_id', 'unknown'),
                        'start_time': getattr(self, 'start_time', datetime.now().isoformat()),
                        'end_time': datetime.now().isoformat(),
                        'status': 'interrupted',
                        'agent_type': getattr(self, 'agent_type', 'unknown'),
                        'task_type': getattr(self, 'task_type', 'unknown'),
                        'total_scenarios': len(getattr(self, 'scenario_list', [])),
                        'parallel_count': getattr(self, 'parallel_count', 1)
                    },
                    'scenario_results': getattr(self, '_scenario_results', []),
                    'interruption_info': {
                        'signal': signum,
                        'message': 'Evaluation interrupted by user'
                    }
                }
                self._save_run_summary(emergency_summary)
                logger.info("✅ 紧急数据保存完成")
            except Exception as e:
                logger.warning(f"保存数据时出错: {e}")

            logger.info("🚪 程序退出")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def execute_scenario_standalone(scenario_id: str, config: Dict[str, Any], 
                               output_dir: str, agent_type: str, task_type: str) -> Dict[str, Any]:
    """
    独立的场景执行函数，用于并行处理
    避免pickle序列化问题
    """
    try:
        scenario_executor = ScenarioExecutor(scenario_id, config, output_dir)
        return scenario_executor.execute_scenario(agent_type, task_type)
    except Exception as e:
        return {
            'scenario_id': scenario_id,
            'status': 'failed',
            'error': str(e),
            'task_results': []
        }
