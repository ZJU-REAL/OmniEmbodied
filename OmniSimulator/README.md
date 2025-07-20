# 🤖 Embodied Simulator

一个支持多智能体协作的具身仿真环境，专为复杂任务执行和验证而设计。

## ✨ 主要特性

- 🤖 **多智能体系统** - 支持多个智能体同时工作和协作
- ⚡ **场景驱动的动作注册** - 只注册场景需要的动作，提高性能
- 🔄 **实时能力绑定** - 拿起/放下工具时动作实时注册/取消注册
- 📝 **智能动作描述** - 实时生成英文动作描述和使用指南
- 🎯 **实时任务验证** - 支持多种验证模式的任务完成检测
- 🌐 **可视化界面** - Web界面实时显示仿真状态
- 🔧 **工具系统** - 智能体可以使用工具获得特殊能力
- 🏠 **多房间环境** - 支持复杂的室内环境和物体关系
- 📊 **任务管理系统** - 完整的任务定义、执行和验证框架
- 🔄 **近邻关系管理** - 智能的空间关系维护和验证

## 🚀 快速开始

### 1. 环境要求
- Python 3.7+
- 无外部依赖（仅使用Python标准库和PyYAML）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行交互式任务执行器（推荐）
```bash
# 运行001号场景交互式任务执行器
python tests/task_001_interactive_executor.py
```

### 4. 运行测试
```bash
# 运行001号场景完整测试
python tests/test_scenario_001_tasks.py

# 运行近邻和协作功能测试
python tests/test_proximity_and_cooperation.py
```

### 5. 基本API使用
```python
from embodied_simulator.core import SimulationEngine
from embodied_simulator.utils.data_loader import default_data_loader

# 加载场景数据
scene_data, task_data = default_data_loader.load_complete_scenario("00001")

# 创建引擎并启用可视化
config = {'visualization': {'enabled': True}}
engine = SimulationEngine(config=config, task_abilities=task_data.get("abilities", []))

# 初始化模拟器
success = engine.initialize_with_data({
    'scene': scene_data,
    'task': task_data
})

# 执行动作
agent_id = list(engine.agent_manager.get_all_agents().keys())[0]
status, message, result = engine.action_handler.process_command(
    agent_id, "GOTO main_workbench_area"
)

# 获取智能体支持的动作描述（更新功能）
description = engine.get_agent_supported_actions_description([agent_id])
print(description)  # 显示完整的英文动作描述和使用指南
```

## 📁 项目结构

```
embodied_simulator/
├── 🤖 agent/                           # 智能体系统
│   ├── agent.py                        # 智能体核心类
│   └── agent_manager.py                # 智能体管理器
├── ⚡ action/                          # 动作系统
│   ├── action_handler.py               # 动作处理器（主要API）
│   ├── action_manager.py               # 动作管理器
│   └── actions/                        # 具体动作实现
│       ├── base_action.py              # 动作基类
│       ├── basic_actions.py            # 基础动作（GOTO、GRAB等）
│       ├── attribute_actions.py        # 属性动作（OPEN、CLEAN等）
│       ├── cooperation_actions.py      # 合作动作（CORP_GRAB等）
│       └── attribute_actions.csv       # 属性动作配置
├── 🏗️ core/                            # 核心引擎
│   ├── engine.py                       # 模拟引擎（主要API）
│   ├── state.py                        # 世界状态管理
│   └── enums.py                        # 枚举定义
├── 🌍 environment/                     # 环境管理
│   ├── environment_manager.py          # 环境管理器
│   ├── scene_parser.py                 # 场景解析器
│   ├── scene_validator.py              # 场景验证器
│   ├── room.py                         # 房间类
│   └── object_defs.py                  # 物体定义
├── 🛠️ utils/                           # 工具模块
│   ├── data_loader.py                  # 数据加载器
│   ├── task_verifier.py                # 任务验证器
│   ├── proximity_manager.py            # 近邻关系管理
│   ├── action_validators.py            # 动作验证器
│   ├── feedback.py                     # 反馈系统
│   ├── logger.py                       # 日志系统
│   └── parse_location.py               # 位置解析
├── 🎨 visualization/                   # 可视化系统
│   ├── visualization_manager.py        # 可视化管理器
│   ├── visualization_data.py           # 数据提供器
│   ├── web_server.py                   # Web服务器
│   └── static/                         # 静态资源
├── 📊 data/                            # 数据文件
│   ├── scene/                          # 场景数据
│   ├── task/                           # 任务数据
│   └── simulator_config.yaml           # 全局配置
├── 🧪 tests/                           # 测试文件
│   ├── task_001_interactive_executor.py # 交互式任务执行器
│   ├── test_scenario_001_tasks.py      # 场景任务测试
│   └── test_proximity_and_cooperation.py # 功能测试
└── 📖 docs/                            # 文档
    ├── api.md                          # API文档
    ├── actions.md                      # 动作系统文档
    ├── visualization.md                # 可视化文档
    └── dynamic_action_registration.md  # 动态注册文档
```

## 🧪 测试系统

### 主要测试文件
- **task_001_interactive_executor.py**: 交互式任务执行器，支持逐步执行和可视化
- **test_scenario_001_tasks.py**: 001号场景完整任务测试
- **test_proximity_and_cooperation.py**: 近邻关系和协作功能测试

### 测试结果
- ✅ **基础功能**: 95% 测试通过
- ✅ **任务执行**: 多个任务成功完成（交互式执行器验证）
- ✅ **工具系统**: 动态能力获取和工具使用正常
- ✅ **可视化系统**: Web界面实时显示状态
- ✅ **任务验证**: 支持多种验证模式
- ⚠️ **协作功能**: 部分功能需要优化

## 📖 文档

### 📚 完整文档
- **[文档中心](docs/README.md)** - 所有文档的导航和索引

### 🚀 快速开始文档
- **[用户手册](docs/user_manual.md)** - 详细的安装、配置和使用指南
- **[API文档](docs/api.md)** - 完整的API接口说明和使用示例

### 🔧 开发文档
- **[开发者指南](docs/developer_guide.md)** - 开发环境设置和贡献指南
- **[系统架构](docs/architecture.md)** - 系统架构和设计原则详解

### 📋 功能文档
- **[动作系统](docs/actions.md)** - 动作类型、配置和扩展指南
- **[可视化系统](docs/visualization.md)** - Web界面使用和配置说明
- **[动态注册机制](docs/dynamic_action_registration.md)** - 动作注册系统详解
- **[环境描述配置](docs/environment_description.md)** - 环境描述配置详解和最佳实践

## 🎯 核心功能

### ✅ 已完成功能 (98% 完成)
- **场景管理**: 完整的场景加载、解析和验证
- **智能体系统**: 多智能体管理、移动、探索和交互
- **动作系统**: 基础动作、属性动作、合作动作
- **场景驱动注册**: 只注册场景需要的动作，提高性能
- **实时能力绑定**: 拿起/放下工具时动作实时注册/取消注册
- **智能动作描述**: 实时生成英文动作描述和使用指南
- **工具系统**: 动态能力获取和工具使用
- **近邻关系**: 智能的空间关系维护和验证
- **任务验证**: 多种验证模式（逐步验证、全局验证）
- **可视化系统**: 实时Web界面显示状态
- **数据管理**: 完整的数据加载和配置系统

### ⚠️ 需要优化的功能
- **协作动作**: 多智能体协作命令的语法和执行
- **性能优化**: 大规模场景的性能优化
- **错误处理**: 更完善的错误处理和恢复机制

## 📋 系统要求

### 环境要求
- **Python**: 3.7+
- **操作系统**: Windows、macOS、Linux
- **内存**: 建议512MB以上
- **存储**: 约50MB

### 依赖包
```bash
# 核心依赖
pyyaml>=5.4.0    # 配置文件解析

# 测试依赖
pytest>=6.0.0    # 单元测试框架
```

### 可选依赖
- **Web浏览器**: 用于查看可视化界面
- **端口8080**: 可视化Web服务器默认端口

## 🔧 开发指南

### 添加新场景
1. **创建场景文件**: 在 `data/scene/` 创建 `*_scene.json` 文件
2. **创建任务文件**: 在 `data/task/` 创建 `*_task.json` 文件
3. **创建验证文件**: 在 `data/task/` 创建 `*_verify.json` 文件（可选）
4. **添加测试**: 在 `tests/` 添加对应的测试脚本

### 添加新动作
1. **实现动作类**: 在 `action/actions/` 继承 `BaseAction` 实现新动作
2. **注册动作**: 在相应的管理器中注册动作
3. **配置动作**: 如果是属性动作，在 `attribute_actions.csv` 中配置
4. **更新文档**: 在 `docs/actions.md` 中添加动作说明

### 扩展可视化
1. **修改数据提供器**: 在 `visualization_data.py` 中添加新的数据类型
2. **更新前端**: 修改 `web_server.py` 中的HTML模板
3. **添加API**: 在Web服务器中添加新的REST API端点

## 🤝 贡献指南

1. **Fork项目** 并创建功能分支
2. **编写测试** 确保新功能正确工作
3. **更新文档** 包括API文档和使用说明
4. **提交PR** 并描述变更内容

## 📄 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。
