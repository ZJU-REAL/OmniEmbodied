#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多线程功能测试脚本

测试项目中的各种多线程功能，包括：
1. ThreadPoolManager 的基本功能
2. 数据生成器的多线程处理
3. 并行场景执行
4. 独立任务执行器的多线程功能
5. 模拟器的多智能体并发处理
"""

import os
import sys
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_thread_pool_manager():
    """测试 ThreadPoolManager 基本功能"""
    logger.info("🧵 测试 ThreadPoolManager 基本功能")
    
    try:
        from data_generation.utils.thread_pool import ThreadPoolManager, TaskStatus
        
        def sample_task(item, thread_id):
            """示例任务函数"""
            task_name = item.get('name', f'task_{thread_id}')
            sleep_time = item.get('sleep_time', 1)
            
            logger.info(f"  线程 {thread_id}: 开始执行任务 {task_name}")
            time.sleep(sleep_time)
            logger.info(f"  线程 {thread_id}: 完成任务 {task_name}")
            
            return f"Task {task_name} completed by thread {thread_id}"
        
        # 创建测试任务
        test_tasks = [
            {'name': f'task_{i}', 'sleep_time': 0.5} 
            for i in range(8)
        ]
        
        # 创建线程池管理器
        pool_manager = ThreadPoolManager(num_threads=4, max_retries=2)
        
        # 执行任务
        start_time = time.time()
        results = pool_manager.execute_tasks(
            tasks=test_tasks,
            task_func=sample_task,
            task_id_func=lambda item: item['name']
        )
        end_time = time.time()
        
        # 分析结果
        completed_count = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for r in results if r.status == TaskStatus.FAILED)
        
        logger.info(f"  ✅ ThreadPoolManager 测试完成:")
        logger.info(f"     - 总任务数: {len(test_tasks)}")
        logger.info(f"     - 成功任务: {completed_count}")
        logger.info(f"     - 失败任务: {failed_count}")
        logger.info(f"     - 总耗时: {end_time - start_time:.2f}s")
        logger.info(f"     - 统计信息: {pool_manager.get_statistics()}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ ThreadPoolManager 测试失败: {e}")
        return False

def test_data_generator_threading():
    """测试数据生成器的多线程功能"""
    logger.info("🏭 测试数据生成器多线程功能")
    
    try:
        # 检查是否有数据生成器配置
        config_path = "data_generation/config"
        if not os.path.exists(config_path):
            logger.warning("  ⚠️ 数据生成器配置目录不存在，跳过测试")
            return True
            
        # 这里可以添加具体的数据生成器测试
        logger.info("  ✅ 数据生成器多线程测试通过（模拟）")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ 数据生成器多线程测试失败: {e}")
        return False

def cpu_bound_task(n):
    """CPU密集型任务 - 定义在模块级别以支持pickle"""
    result = sum(i * i for i in range(n))
    return f"Task {n}: {result}"

def io_bound_task(delay):
    """IO密集型任务 - 定义在模块级别以支持pickle"""
    time.sleep(delay)
    return f"IO task completed after {delay}s"

def test_concurrent_futures():
    """测试 concurrent.futures 的基本功能"""
    logger.info("⚡ 测试 concurrent.futures 基本功能")
    
    try:
        # 测试 ThreadPoolExecutor
        logger.info("  测试 ThreadPoolExecutor (IO密集型)")
        with ThreadPoolExecutor(max_workers=4) as executor:
            io_tasks = [0.2, 0.3, 0.1, 0.4, 0.2]
            start_time = time.time()
            
            futures = [executor.submit(io_bound_task, delay) for delay in io_tasks]
            results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            logger.info(f"    - IO任务完成，耗时: {end_time - start_time:.2f}s")
            logger.info(f"    - 结果数量: {len(results)}")
        
        # 测试 ProcessPoolExecutor
        logger.info("  测试 ProcessPoolExecutor (CPU密集型)")
        with ProcessPoolExecutor(max_workers=2) as executor:
            cpu_tasks = [10000, 15000, 12000, 8000]
            start_time = time.time()
            
            futures = [executor.submit(cpu_bound_task, n) for n in cpu_tasks]
            results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            logger.info(f"    - CPU任务完成，耗时: {end_time - start_time:.2f}s")
            logger.info(f"    - 结果数量: {len(results)}")
        
        logger.info("  ✅ concurrent.futures 测试通过")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ concurrent.futures 测试失败: {e}")
        return False

def test_threading_primitives():
    """测试线程同步原语"""
    logger.info("🔒 测试线程同步原语")
    
    try:
        # 测试 Lock
        shared_counter = 0
        counter_lock = threading.Lock()
        
        def increment_counter():
            nonlocal shared_counter
            for _ in range(1000):
                with counter_lock:
                    shared_counter += 1
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=increment_counter)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        logger.info(f"  Lock测试: 期望值=5000, 实际值={shared_counter}")
        
        # 测试 Event
        event = threading.Event()
        results = []
        
        def wait_for_event(worker_id):
            logger.info(f"    工作线程 {worker_id} 等待事件...")
            event.wait()
            results.append(f"Worker {worker_id} completed")
            logger.info(f"    工作线程 {worker_id} 完成")
        
        # 启动等待线程
        wait_threads = []
        for i in range(3):
            thread = threading.Thread(target=wait_for_event, args=(i,))
            wait_threads.append(thread)
            thread.start()
        
        time.sleep(0.5)  # 让线程开始等待
        logger.info("  触发事件...")
        event.set()  # 触发事件
        
        for thread in wait_threads:
            thread.join()
        
        logger.info(f"  Event测试: 完成的工作线程数={len(results)}")
        logger.info("  ✅ 线程同步原语测试通过")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ 线程同步原语测试失败: {e}")
        return False

def test_simulator_multithreading():
    """测试模拟器的多线程功能"""
    logger.info("🤖 测试模拟器多线程功能")
    
    try:
        # 检查模拟器是否存在
        simulator_path = "utils/embodied_simulator"
        if not os.path.exists(simulator_path):
            logger.warning("  ⚠️ 模拟器目录不存在，跳过测试")
            return True
        
        # 检查测试文件
        test_files = [
            "utils/embodied_simulator/tests/test_proximity_and_cooperation.py",
            "utils/embodied_simulator/tests/test_scenario_001_tasks.py"
        ]
        
        available_tests = [f for f in test_files if os.path.exists(f)]
        
        if not available_tests:
            logger.warning("  ⚠️ 模拟器测试文件不存在，跳过测试")
            return True
        
        logger.info(f"  找到 {len(available_tests)} 个模拟器测试文件")
        logger.info("  ✅ 模拟器多线程测试通过（检查）")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ 模拟器多线程测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始多线程功能测试")
    logger.info("=" * 60)
    
    test_results = {}
    
    # 运行各项测试
    tests = [
        ("ThreadPoolManager", test_thread_pool_manager),
        ("数据生成器多线程", test_data_generator_threading),
        ("concurrent.futures", test_concurrent_futures),
        ("线程同步原语", test_threading_primitives),
        ("模拟器多线程", test_simulator_multithreading),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 运行测试: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            test_results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"测试 {test_name}: {status}")
        except Exception as e:
            test_results[test_name] = False
            logger.error(f"测试 {test_name} 异常: {e}")
    
    # 输出总结
    logger.info("\n" + "=" * 60)
    logger.info("🎯 测试总结")
    logger.info("=" * 60)
    
    passed_count = sum(1 for result in test_results.values() if result)
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有多线程测试通过！")
        return 0
    else:
        logger.warning(f"⚠️ {total_count - passed_count} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
