# 开发者指南

本指南为Embodied Simulator的开发者提供详细的开发、测试和贡献指导。

## 目录
- [开发环境设置](#开发环境设置)
- [代码结构](#代码结构)
- [开发工作流](#开发工作流)
- [测试指南](#测试指南)
- [代码规范](#代码规范)
- [贡献指南](#贡献指南)

## 开发环境设置

### 1. 环境要求

- **Python**: 3.7+
- **Git**: 版本控制
- **IDE**: 推荐 VSCode 或 PyCharm
- **浏览器**: 用于测试可视化功能

### 2. 项目设置

```bash
# 克隆项目
git clone <repository-url>
cd embodied_simulator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果存在

# 安装项目为可编辑模式
pip install -e .
```

### 3. IDE配置

**VSCode配置** (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

**PyCharm配置**:
- 设置项目解释器为虚拟环境中的Python
- 启用代码检查和格式化
- 配置测试运行器为pytest

## 代码结构

### 1. 模块组织

```
embodied_simulator/
├── __init__.py              # 包初始化，导出主要API
├── core/                    # 核心模块
│   ├── engine.py           # 主引擎类
│   ├── state.py            # 世界状态管理
│   └── enums.py            # 枚举定义
├── action/                  # 动作系统
│   ├── action_handler.py   # 动作处理器（API层）
│   ├── action_manager.py   # 动作管理器（核心层）
│   └── actions/            # 具体动作实现
├── agent/                   # 智能体系统
├── environment/             # 环境管理
├── utils/                   # 工具模块
└── visualization/           # 可视化系统
```

### 2. 命名约定

- **类名**: PascalCase (如 `SimulationEngine`)
- **函数名**: snake_case (如 `process_command`)
- **常量**: UPPER_SNAKE_CASE (如 `ACTION_STATUS`)
- **私有方法**: 以下划线开头 (如 `_validate_input`)

### 3. 导入规范

```python
# 标准库导入
import os
import sys
from typing import Dict, List, Optional

# 第三方库导入
import yaml

# 本地导入
from ..core import ActionStatus
from .base_action import BaseAction
```

## 开发工作流

### 1. 功能开发流程

1. **创建功能分支**
```bash
git checkout -b feature/new-action-type
```

2. **编写代码**
   - 实现功能逻辑
   - 添加文档字符串
   - 遵循代码规范

3. **编写测试**
   - 单元测试
   - 集成测试
   - 边界情况测试

4. **运行测试**
```bash
pytest tests/ -v
```

5. **提交代码**
```bash
git add .
git commit -m "feat: add new action type"
git push origin feature/new-action-type
```

6. **创建Pull Request**

### 2. 调试技巧

**启用详细日志**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**使用调试器**:
```python
import pdb; pdb.set_trace()  # 设置断点
```

**可视化调试**:
```python
# 启用可视化查看状态变化
config = {'visualization': {'enabled': True}}
engine = SimulationEngine(config=config)
```

## 测试指南

### 1. 测试结构

```
tests/
├── conftest.py                      # pytest配置和fixtures
├── test_scenario_001_tasks.py       # 场景测试
├── test_proximity_and_cooperation.py # 功能测试
└── unit/                           # 单元测试
    ├── test_action_handler.py
    ├── test_simulation_engine.py
    └── test_world_state.py
```

### 2. 编写测试

**单元测试示例**:
```python
import pytest
from embodied_simulator.core import SimulationEngine, ActionStatus

class TestSimulationEngine:
    def test_initialization(self):
        """测试引擎初始化"""
        engine = SimulationEngine()
        assert engine is not None
        assert engine.world_state is not None
    
    def test_action_execution(self):
        """测试动作执行"""
        engine = self.create_test_engine()
        status, message, result = engine.action_handler.process_command(
            "test_agent", "GOTO test_room"
        )
        assert status == ActionStatus.SUCCESS
        assert "成功" in message
    
    def create_test_engine(self):
        """创建测试用引擎"""
        # 实现测试环境创建逻辑
        pass
```

**集成测试示例**:
```python
def test_complete_task_workflow():
    """测试完整任务流程"""
    # 加载测试数据
    scene_data, task_data, verify_data = load_test_data()
    
    # 创建引擎
    engine = SimulationEngine(task_abilities=task_data.get("abilities", []))
    
    # 初始化
    success = engine.initialize_with_data({
        'scene': scene_data,
        'task': task_data,
        'verify': verify_data
    })
    assert success
    
    # 执行任务序列
    commands = ["GOTO room1", "GRAB object1", "PLACE object1 ON table1"]
    for command in commands:
        status, _, _ = engine.action_handler.process_command("agent1", command)
        assert status == ActionStatus.SUCCESS
```

### 3. 测试数据管理

**创建测试数据**:
```python
def create_test_scene():
    """创建测试场景数据"""
    return {
        "description": "测试场景",
        "rooms": [
            {
                "id": "test_room",
                "name": "测试房间",
                "objects": ["test_object"]
            }
        ],
        "objects": [
            {
                "id": "test_object",
                "name": "测试物体",
                "type": "ITEM",
                "location_id": "test_room"
            }
        ]
    }
```

### 4. 性能测试

```python
import time
import pytest

def test_action_performance():
    """测试动作执行性能"""
    engine = create_test_engine()
    
    start_time = time.time()
    for i in range(100):
        status, _, _ = engine.action_handler.process_command(
            "agent1", f"GOTO object_{i % 10}"
        )
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100
    assert avg_time < 0.01  # 平均执行时间应小于10ms
```

## 代码规范

### 1. 文档字符串

```python
def process_command(self, agent_id: str, command_str: str) -> Tuple[ActionStatus, str, Optional[Dict]]:
    """
    处理智能体命令
    
    Args:
        agent_id: 智能体ID
        command_str: 命令字符串，格式如 "GOTO target" 或 "GRAB object"
        
    Returns:
        Tuple包含:
        - ActionStatus: 执行状态 (SUCCESS/FAILURE/INVALID)
        - str: 反馈消息
        - Optional[Dict]: 额外结果数据，可能包含任务验证信息
        
    Raises:
        ValueError: 当agent_id为空时
        
    Example:
        >>> status, msg, result = handler.process_command("robot_1", "GOTO room1")
        >>> assert status == ActionStatus.SUCCESS
    """
```

### 2. 类型注解

```python
from typing import Dict, List, Optional, Tuple, Union

class ActionHandler:
    def __init__(self, 
                 world_state: WorldState,
                 env_manager: EnvironmentManager,
                 agent_manager: AgentManager,
                 config: Optional[Dict[str, Any]] = None) -> None:
        self.world_state = world_state
        self.config = config or {}
```

### 3. 错误处理

```python
def validate_input(self, input_data: Dict) -> bool:
    """验证输入数据"""
    try:
        required_fields = ['id', 'type', 'location']
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"缺少必需字段: {field}")
        return True
    except ValueError as e:
        logger.error(f"输入验证失败: {e}")
        raise
    except Exception as e:
        logger.error(f"未知验证错误: {e}")
        return False
```

### 4. 配置管理

```python
class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        'visualization': {'enabled': False},
        'task_verification': {'mode': 'disabled'}
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                self._merge_config(self.config, user_config)
        except FileNotFoundError:
            logger.warning(f"配置文件未找到: {config_path}")
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {e}")
```

## 贡献指南

### 1. 贡献类型

- **Bug修复**: 修复已知问题
- **功能增强**: 添加新功能
- **文档改进**: 完善文档
- **性能优化**: 提升系统性能
- **测试补充**: 增加测试覆盖率

### 2. 提交规范

**提交消息格式**:
```
<type>(<scope>): <description>

<body>

<footer>
```

**类型说明**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**:
```
feat(action): add custom action support

- Add BaseAction class for custom actions
- Implement action registration mechanism
- Add validation for custom action parameters

Closes #123
```

### 3. Pull Request流程

1. **Fork项目** 到个人账户
2. **创建功能分支** 从main分支
3. **实现功能** 并添加测试
4. **确保测试通过** 运行完整测试套件
5. **更新文档** 如果需要
6. **提交PR** 并填写详细描述
7. **响应Review** 根据反馈修改代码
8. **合并代码** 通过审核后合并

### 4. 代码审查清单

- [ ] 代码符合项目规范
- [ ] 添加了适当的测试
- [ ] 测试全部通过
- [ ] 文档已更新
- [ ] 没有引入新的依赖（或已说明必要性）
- [ ] 性能没有明显下降
- [ ] 向后兼容性保持

### 5. 发布流程

1. **版本号管理**: 遵循语义化版本控制
2. **变更日志**: 更新CHANGELOG.md
3. **标签创建**: 创建版本标签
4. **文档更新**: 更新版本相关文档
5. **发布说明**: 编写发布说明

## 常见问题

### Q: 如何调试可视化问题？

A: 
1. 检查浏览器控制台错误
2. 验证Web服务器是否正常启动
3. 检查数据API返回是否正确
4. 使用浏览器开发者工具检查网络请求

### Q: 如何添加新的测试场景？

A:
1. 在`data/scene/`创建场景JSON文件
2. 在`data/task/`创建任务JSON文件
3. 在`tests/`添加对应的测试脚本
4. 确保测试覆盖主要功能路径

### Q: 如何优化性能？

A:
1. 使用性能分析工具识别瓶颈
2. 优化频繁调用的函数
3. 添加适当的缓存机制
4. 考虑异步处理长时间操作
