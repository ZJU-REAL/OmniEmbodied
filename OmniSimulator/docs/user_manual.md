# Embodied Simulator 使用手册

本手册提供了Embodied Simulator的详细使用指南，包括安装、配置、基本使用和高级功能。

## 目录
- [快速开始](#快速开始)
- [安装和配置](#安装和配置)
- [基本概念](#基本概念)
- [使用场景](#使用场景)
- [高级功能](#高级功能)
- [故障排除](#故障排除)

## 快速开始

### 5分钟体验

1. **克隆项目**
```bash
git clone <repository-url>
cd embodied_simulator
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行交互式演示**
```bash
python tests/task_001_interactive_executor.py
```

4. **查看可视化界面**
   - 程序会自动打开浏览器显示可视化界面
   - 或手动访问 http://localhost:8080

5. **逐步执行任务**
   - 按回车键执行下一步
   - 观察智能体的行为和任务进度

## 安装和配置

### 系统要求

- **Python**: 3.7 或更高版本
- **操作系统**: Windows、macOS、Linux
- **内存**: 建议 512MB 以上
- **网络**: 可视化功能需要本地端口 8080

### 安装步骤

1. **创建虚拟环境（推荐）**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

2. **安装依赖包**
```bash
pip install -r requirements.txt
```

3. **验证安装**
```bash
python -c "from embodied_simulator.core import SimulationEngine; print('安装成功')"
```

### 配置文件

主配置文件位于 `data/simulator_config.yaml`：

```yaml
# 探索模式
explore_mode: thorough   # normal/thorough

# 任务验证配置
task_verification:
  enabled: true          # 是否启用任务验证
  mode: "step_by_step"   # 验证模式
  return_subtask_status: true

# 可视化配置
visualization:
  enabled: true          # 是否启用可视化
  web_server:
    host: "localhost"
    port: 8080
    auto_open_browser: true
  request_interval: 2000  # 更新间隔(毫秒)
```

## 基本概念

### 核心组件

1. **SimulationEngine**: 模拟引擎，系统的核心入口
2. **ActionHandler**: 动作处理器，执行智能体命令
3. **AgentManager**: 智能体管理器，管理多个智能体
4. **EnvironmentManager**: 环境管理器，管理场景和物体
5. **VisualizationManager**: 可视化管理器，提供Web界面

### 数据结构

1. **场景数据** (`*_scene.json`): 定义房间、家具、物体
2. **任务数据** (`*_task.json`): 定义智能体配置和任务
3. **验证数据** (`*_verify.json`): 定义任务验证规则

### 动作类型

1. **基础动作**: GOTO、GRAB、PLACE、EXPLORE
2. **属性动作**: OPEN、CLOSE、TURN_ON、CLEAN等
3. **合作动作**: CORP_GRAB、CORP_GOTO、CORP_PLACE

## 使用场景

### 场景1: 单智能体任务执行

```python
from embodied_simulator.core import SimulationEngine
from embodied_simulator.utils.data_loader import default_data_loader

# 加载场景
scene_data, task_data, verify_data = default_data_loader.load_complete_scenario("00001")

# 创建引擎
engine = SimulationEngine(task_abilities=task_data.get("abilities", []))

# 初始化
success = engine.initialize_with_data({
    'scene': scene_data,
    'task': task_data,
    'verify': verify_data
})

# 获取智能体
agent_id = list(engine.agent_manager.get_all_agents().keys())[0]

# 执行任务
commands = ["GOTO main_workbench_area", "GRAB oscilloscope_1"]
for command in commands:
    status, message, result = engine.action_handler.process_command(agent_id, command)
    print(f"{command}: {status.name} - {message}")
```

### 场景2: 多智能体协作

```python
# 创建多智能体环境
engine = SimulationEngine(task_abilities=["corp_grab", "corp_goto"])

# 初始化环境
success = engine.initialize_with_data(data)

# 执行合作任务
status, message, result = engine.action_handler.process_command(
    "robot_1", "CORP_GRAB robot_1,robot_2 heavy_box_1"
)
```

### 场景3: 带可视化的交互式执行

```python
# 启用可视化
config = {'visualization': {'enabled': True}}
engine = SimulationEngine(config=config)

# 初始化并获取可视化URL
success = engine.initialize_with_data(data)
url = engine.get_visualization_url()
print(f"可视化界面: {url}")

# 执行任务并观察可视化效果
for command in commands:
    input("按回车执行下一步...")
    status, message, result = engine.action_handler.process_command(agent_id, command)
```

## 高级功能

### 自定义动作

1. **创建动作类**
```python
from embodied_simulator.action.actions.base_action import BaseAction

class CustomAction(BaseAction):
    def execute(self, agent, target_id=None, **kwargs):
        # 实现自定义逻辑
        return ActionStatus.SUCCESS, "执行成功", {}
```

2. **注册动作**
```python
engine.action_handler.register_action_class("custom", CustomAction)
```

### 任务验证自定义

1. **创建验证规则**
```json
{
  "tasks": [
    {
      "id": "task_1",
      "description": "将物体放到指定位置",
      "verification": {
        "type": "location",
        "object_id": "object_1",
        "location_id": "target_location"
      }
    }
  ]
}
```

2. **使用验证器**
```python
from embodied_simulator.utils.task_verifier import TaskVerifier

verifier = TaskVerifier(verify_data, engine.world_state)
results = verifier.verify_all_tasks()
```

### 可视化扩展

1. **自定义数据提供器**
```python
def custom_data_provider(world_state):
    return {
        'custom_info': 'your_data_here'
    }
```

2. **添加REST API端点**
```python
# 在web_server.py中添加新的路由
@app.route('/api/custom')
def get_custom_data():
    return jsonify(custom_data_provider(world_state))
```

## 故障排除

### 常见问题

1. **模拟器初始化失败**
   - 检查数据文件格式是否正确
   - 确认所有必需的字段都存在
   - 查看控制台错误信息

2. **可视化无法访问**
   - 确认端口8080未被占用
   - 检查防火墙设置
   - 尝试使用127.0.0.1而不是localhost

3. **动作执行失败**
   - 检查智能体是否在正确位置
   - 确认目标物体存在且可访问
   - 验证动作的前置条件

4. **任务验证不工作**
   - 检查验证数据格式
   - 确认验证模式配置正确
   - 查看任务验证器的初始化状态

### 调试技巧

1. **启用详细日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **检查世界状态**
```python
print(engine.world_state.get_all_objects())
print(engine.world_state.get_all_agents())
```

3. **验证数据完整性**
```python
from embodied_simulator.environment.scene_validator import SceneValidator
validator = SceneValidator()
is_valid, errors = validator.validate_scene(scene_data)
```

### 性能优化

1. **禁用可视化**（生产环境）
```yaml
visualization:
  enabled: false
```

2. **调整验证频率**
```yaml
task_verification:
  mode: "global"  # 仅在done命令时验证
```

3. **优化探索模式**
```yaml
explore_mode: normal  # 使用普通探索模式
```

## 更多资源

- [API文档](api.md) - 完整的API参考
- [动作系统文档](actions.md) - 动作类型和配置
- [可视化文档](visualization.md) - 可视化系统详解
- [动态注册文档](dynamic_action_registration.md) - 动作注册机制

## 社区和支持

- **问题反馈**: 通过GitHub Issues报告问题
- **功能请求**: 提交Feature Request
- **贡献代码**: 查看贡献指南
