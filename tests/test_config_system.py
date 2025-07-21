#!/usr/bin/env python3
"""配置系统测试"""

import sys
import os
import tempfile
import unittest
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config_manager import ConfigManager, get_config_manager, reset_config_manager
from config.config_validator import ConfigValidator
from config.config_utils import load_and_validate_config

class TestConfigSystem(unittest.TestCase):
    """配置系统测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 重置全局配置管理器
        reset_config_manager()
    
    def tearDown(self):
        """测试后清理"""
        reset_config_manager()
    
    def test_config_manager_singleton(self):
        """测试配置管理器单例模式"""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        self.assertIs(manager1, manager2)
    
    def test_config_loading(self):
        """测试配置加载"""
        config_manager = get_config_manager()
        
        # 测试加载LLM配置
        llm_config = config_manager.get_config('llm_config')
        self.assertIsInstance(llm_config, dict)
        self.assertIn('mode', llm_config)
        self.assertIn('api', llm_config)
    
    def test_config_inheritance(self):
        """测试配置继承"""
        config_manager = get_config_manager()
        
        # 测试单智能体配置继承基础配置
        single_config = config_manager.get_config('single_agent_config')
        self.assertIsInstance(single_config, dict)
        
        # 应该包含基础配置的内容
        self.assertIn('system', single_config)
        self.assertIn('data_dir', single_config)
        self.assertIn('execution', single_config)
        
        # 应该包含智能体特定配置
        self.assertIn('agent_config', single_config)
    
    def test_environment_variable_resolution(self):
        """测试环境变量解析"""
        config_manager = get_config_manager()

        # 设置测试环境变量
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            # 创建临时配置
            test_config = {
                'test_key': '${TEST_VAR}',
                'nested': {
                    'test_key2': '${TEST_VAR}'
                }
            }

            resolved = config_manager._resolve_environment_variables(test_config)
            self.assertEqual(resolved['test_key'], 'test_value')
            self.assertEqual(resolved['nested']['test_key2'], 'test_value')

        # 测试环境变量不存在时应该抛出异常
        test_config_missing = {'test_key': '${MISSING_VAR}'}
        with self.assertRaises(KeyError):
            config_manager._resolve_environment_variables(test_config_missing)
    
    def test_runtime_overrides(self):
        """测试运行时覆盖"""
        config_manager = get_config_manager()
        
        # 设置运行时覆盖
        config_manager.set_runtime_override('test_config', 'key1', 'value1')
        config_manager.set_runtime_override('test_config', 'nested.key2', 'value2')
        
        # 验证覆盖是否生效
        self.assertIn('test_config', config_manager.runtime_overrides)
        overrides = config_manager.runtime_overrides['test_config']
        self.assertEqual(overrides['key1'], 'value1')
        self.assertEqual(overrides['nested']['key2'], 'value2')
    
    def test_config_section_access(self):
        """测试配置节访问"""
        config_manager = get_config_manager()

        # 测试嵌套路径访问
        llm_config = config_manager.get_config('llm_config')
        provider = config_manager.get_config_section('llm_config', 'api.provider')
        self.assertIsNotNone(provider)

        # 测试不存在的配置项应该抛出异常
        with self.assertRaises(KeyError):
            config_manager.get_config_section('llm_config', 'non.existent.key')
    
    def test_value_type_conversion(self):
        """测试值类型转换"""
        config_manager = get_config_manager()
        
        # 测试布尔值转换
        self.assertTrue(config_manager._convert_value_type('true'))
        self.assertFalse(config_manager._convert_value_type('false'))
        
        # 测试数字转换
        self.assertEqual(config_manager._convert_value_type('123'), 123)
        self.assertEqual(config_manager._convert_value_type('123.45'), 123.45)
        
        # 测试列表转换
        self.assertEqual(config_manager._convert_value_type('a,b,c'), ['a', 'b', 'c'])
        
        # 测试字符串
        self.assertEqual(config_manager._convert_value_type('hello'), 'hello')
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试基础配置验证
        valid_config = {'data_dir': '/path/to/data'}
        errors = ConfigValidator.validate_config(valid_config, 'base')
        self.assertEqual(len(errors), 0)
        
        # 测试无效配置
        invalid_config = {}
        errors = ConfigValidator.validate_config(invalid_config, 'base')
        self.assertGreater(len(errors), 0)
    
    def test_config_merge(self):
        """测试配置合并"""
        config_manager = get_config_manager()
        
        base_config = {
            'key1': 'value1',
            'nested': {
                'key2': 'value2',
                'key3': 'value3'
            }
        }
        
        override_config = {
            'key1': 'new_value1',
            'nested': {
                'key2': 'new_value2',
                'key4': 'value4'
            },
            'key5': 'value5'
        }
        
        merged = config_manager._merge_configs(base_config, override_config)
        
        # 验证合并结果
        self.assertEqual(merged['key1'], 'new_value1')  # 覆盖
        self.assertEqual(merged['nested']['key2'], 'new_value2')  # 嵌套覆盖
        self.assertEqual(merged['nested']['key3'], 'value3')  # 保留原值
        self.assertEqual(merged['nested']['key4'], 'value4')  # 新增
        self.assertEqual(merged['key5'], 'value5')  # 新增

if __name__ == '__main__':
    unittest.main()
