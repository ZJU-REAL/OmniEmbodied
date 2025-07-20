"""
评测管理器 - 统一评测管理和场景级并行执行
"""

import os
import json
import yaml
import csv
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
            agent_type: 智能体类型 ('single', 'multi')
            task_type: 任务类型 ('sequential', 'combined', 'independent')
            scenario_selection: 场景选择配置
            custom_suffix: 自定义后缀
        """
        self.config_file = config_file
        self.agent_type = agent_type
        self.task_type = task_type
        self.custom_suffix = custom_suffix or 'demo'

        # 映射agent_type到实际的智能体模式
        self.actual_agent_type = self._map_agent_type(agent_type, config_file)
        
        # 加载配置
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config(config_file)
        
        # 选择场景和任务
        scenario_result = ScenarioSelector.get_scenario_list(self.config, scenario_selection)
        self.scenario_list = scenario_result['scenarios']
        self.task_indices = scenario_result['task_indices']
        
        # 生成运行名称和输出目录
        self.run_name = self._generate_run_name()
        self.output_dir = self._create_output_directory()
        
        # 并行配置
        parallel_config = self.config.get('parallel_evaluation', {})
        max_parallel = parallel_config.get('scenario_parallelism', {}).get('max_parallel_scenarios', 2)
        self.parallel_count = min(len(self.scenario_list), max_parallel)

        # 运行开始时间
        self.start_time = datetime.now().isoformat()

        # 运行ID
        self.run_id = self.run_name

        # 提取并保存模型名称
        agent_config = self.config.get('agent_config', {})
        model_info = self._extract_model_info(agent_config)

        # 保存模型名称为实例变量
        provider = model_info.get('provider', 'unknown')
        model_name = model_info.get('model_name', 'unknown')
        self.model_name = f"{provider}:{model_name}" if provider != 'unknown' and model_name != 'unknown' else 'unknown'

        # 注册信号处理器
        self._register_signal_handlers()

        # 保存实验配置
        self._save_experiment_config()

        logger.info(f"🚀 评测管理器初始化完成: {self.run_name}")
        logger.info(f"📊 场景数量: {len(self.scenario_list)}, 并行数: {self.parallel_count}")

    def _map_agent_type(self, agent_type: str, config_file: str) -> str:
        """
        将评测接口的agent_type映射到实际的智能体模式

        Args:
            agent_type: 评测接口传入的类型 ('single', 'multi')
            config_file: 配置文件名

        Returns:
            str: 实际的智能体模式 ('single', 'centralized', 'decentralized')
        """
        if agent_type == 'single':
            return 'single'
        elif agent_type == 'multi':
            # 根据配置文件名判断多智能体模式
            if 'centralized' in config_file:
                return 'centralized'
            elif 'decentralized' in config_file:
                return 'decentralized'
            else:
                # 默认为中心化模式
                return 'centralized'
        else:
            # 直接返回，支持直接传入具体模式
            return agent_type
    
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
        subdirs = ['trajectories', 'llm_qa']
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
            # 执行场景
            self._execute_scenarios()

            # 计算总执行时间
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()

            # 【修改】使用混合数据源生成摘要
            run_summary = self._generate_run_summary(
                start_time, end_time, total_duration,
                status="completed"
            )

            # 保存运行摘要
            self._save_run_summary(run_summary)

            logger.info(f"✅ 评测完成: {self.run_name}")
            return run_summary

        except Exception as e:
            logger.error(f"❌ 评测失败: {e}")
            raise
    

    
    def _execute_scenarios(self):
        """执行场景（简化版，不返回结果）"""
        scenario_count = len(self.scenario_list)

        if scenario_count == 1:
            logger.info(f"🔄 执行场景: {self.scenario_list[0]}")
        else:
            logger.info(f"🔄 执行 {scenario_count} 个场景")

        self._executor = ProcessPoolExecutor(max_workers=self.parallel_count)
        try:
            # 提交所有场景任务
            future_to_scenario = {
                self._executor.submit(
                    execute_scenario_standalone,
                    scenario_id, self.config, self.output_dir,
                    self.actual_agent_type, self.task_type,
                    self.task_indices.get(scenario_id, [])
                ): scenario_id
                for scenario_id in self.scenario_list
            }

            # 等待所有任务完成（不收集结果）
            for future in as_completed(future_to_scenario):
                scenario_id = future_to_scenario[future]
                try:
                    future.result()  # 只是等待完成，不保存结果
                    logger.info(f"✅ 场景 {scenario_id} 执行完成")
                except Exception as e:
                    logger.error(f"❌ 场景 {scenario_id} 执行失败: {e}")

        finally:
            if hasattr(self, '_executor') and self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None
    
    def _calculate_overall_summary_from_csv(self) -> Dict[str, Any]:
        """
        从CSV文件计算overall_summary

        Returns:
            Dict: overall_summary数据
        """
        csv_file = os.path.join(self.output_dir, "subtask_execution_log.csv")

        # 默认值
        summary = {
            "total_tasks": 0,
            "actually_completed": 0,
            "model_claimed_completed": 0,
            "total_llm_interactions": 0,
            "completion_rate": 0.0,
            "avg_llm_interactions": 0.0
        }

        if not os.path.exists(csv_file):
            logger.warning(f"CSV文件不存在: {csv_file}")
            return summary

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                total_tasks = 0
                actually_completed = 0
                model_claimed_completed = 0
                total_llm_interactions = 0

                for row in reader:
                    total_tasks += 1

                    # 统计实际完成
                    if row.get('subtask_completed', '').lower() == 'true':
                        actually_completed += 1

                    # 统计模型声称完成
                    if row.get('model_claimed_done', '').lower() == 'true':
                        model_claimed_completed += 1

                    # 累计LLM交互次数
                    try:
                        llm_interactions = int(row.get('llm_interactions', 0) or 0)
                        total_llm_interactions += llm_interactions
                    except (ValueError, TypeError):
                        pass

                # 计算比率
                completion_rate = actually_completed / total_tasks if total_tasks > 0 else 0.0
                avg_llm_interactions = total_llm_interactions / total_tasks if total_tasks > 0 else 0.0

                summary.update({
                    "total_tasks": total_tasks,
                    "actually_completed": actually_completed,
                    "model_claimed_completed": model_claimed_completed,
                    "total_llm_interactions": total_llm_interactions,
                    "completion_rate": round(completion_rate, 4),
                    "avg_llm_interactions": round(avg_llm_interactions, 2)
                })

                logger.info(f"📊 从CSV计算统计: {total_tasks}个任务, {actually_completed}个完成")

        except Exception as e:
            logger.error(f"解析CSV文件失败: {e}")

        return summary

    def _calculate_task_category_statistics_from_csv(self) -> Dict[str, Any]:
        """
        从CSV文件计算任务分类统计

        Returns:
            Dict: 按任务类别分组的统计数据
        """
        csv_file = os.path.join(self.output_dir, "subtask_execution_log.csv")

        if not os.path.exists(csv_file):
            return {}

        category_stats = {}

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    category = row.get('task_category', 'unknown')

                    if category not in category_stats:
                        category_stats[category] = {
                            "total": 0,
                            "completed": 0,
                            "model_claimed": 0,
                            "completion_rate": 0.0
                        }

                    category_stats[category]["total"] += 1

                    if row.get('subtask_completed', '').lower() == 'true':
                        category_stats[category]["completed"] += 1

                    if row.get('model_claimed_done', '').lower() == 'true':
                        category_stats[category]["model_claimed"] += 1

                # 计算完成率
                for category, stats in category_stats.items():
                    if stats["total"] > 0:
                        stats["completion_rate"] = round(stats["completed"] / stats["total"], 4)

        except Exception as e:
            logger.error(f"计算任务分类统计失败: {e}")

        return category_stats
    
    def _generate_run_summary(self, start_time: datetime, end_time: datetime,
                             total_duration: float, status: str = "completed",
                             note: str = None) -> Dict[str, Any]:
        """
        生成运行摘要（混合数据源版本）

        Args:
            start_time: 开始时间
            end_time: 结束时间
            total_duration: 总持续时间
            status: 运行状态
            note: 备注信息

        Returns:
            Dict: 运行摘要
        """

        # 1. 运行时信息（不依赖CSV）
        runinfo = {
            "run_id": self.run_id,
            "model_name": self.model_name,
            "agent_type": self.agent_type,
            "task_mode": self.task_type,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_scenarios": len(self.scenario_list),
            "config_file": self.config_file,
            "status": status,
            "duration_seconds": round(total_duration, 2)
        }

        if note:
            runinfo["note"] = note

        # 2. 从CSV计算统计数据
        overall_summary = self._calculate_overall_summary_from_csv()
        task_category_statistics = self._calculate_task_category_statistics_from_csv()

        return {
            "runinfo": runinfo,
            "overall_summary": overall_summary,
            "task_category_statistics": task_category_statistics
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

            # 关闭进程池
            if hasattr(self, '_executor') and self._executor:
                logger.info("🔄 正在关闭进程池...")
                self._executor.shutdown(wait=False)
                self._executor = None
                logger.info("✅ 进程池已关闭")

            # 保存当前数据
            self._save_emergency_summary()
            logger.info("✅ 紧急数据保存完成")

            logger.info("🚪 程序退出")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _save_emergency_summary(self):
        """异常情况下的紧急摘要保存"""
        try:
            end_time = datetime.now()
            start_time_dt = datetime.fromisoformat(self.start_time)
            total_duration = (end_time - start_time_dt).total_seconds()

            # 检查是否有CSV数据
            csv_file = os.path.join(self.output_dir, "subtask_execution_log.csv")
            has_csv_data = os.path.exists(csv_file) and os.path.getsize(csv_file) > 100  # 大于头部

            if has_csv_data:
                # 有CSV数据，生成完整摘要
                emergency_summary = self._generate_run_summary(
                    start_time_dt, end_time, total_duration,
                    status="emergency_exit",
                    note="Program terminated unexpectedly"
                )
            else:
                # 没有CSV数据，生成基本摘要
                emergency_summary = self._generate_run_summary(
                    start_time_dt, end_time, total_duration,
                    status="emergency_exit_no_data",
                    note="Program terminated before any task completion"
                )

            # 保存摘要
            summary_path = os.path.join(self.output_dir, 'run_summary.json')
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(emergency_summary, f, indent=2, ensure_ascii=False)

            logger.info(f"📊 紧急运行摘要已保存: {summary_path}")

        except Exception as e:
            logger.error(f"保存紧急摘要失败: {e}")


def execute_scenario_standalone(scenario_id: str, config: Dict[str, Any],
                               output_dir: str, agent_type: str, task_type: str,
                               task_indices: List[int] = None) -> Dict[str, Any]:
    """
    独立的场景执行函数，用于并行处理
    避免pickle序列化问题

    Args:
        scenario_id: 场景ID
        config: 配置信息
        output_dir: 输出目录
        agent_type: 智能体类型
        task_type: 任务类型
        task_indices: 要执行的任务索引列表，None表示执行所有任务
    """
    try:
        scenario_executor = ScenarioExecutor(scenario_id, config, output_dir, task_indices)
        return scenario_executor.execute_scenario(agent_type, task_type)
    except Exception as e:
        return {
            'scenario_id': scenario_id,
            'status': 'failed',
            'error': str(e),
            'task_results': []
        }
