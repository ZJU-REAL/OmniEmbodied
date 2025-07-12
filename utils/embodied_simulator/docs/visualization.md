# 模拟器可视化系统

## 概述

模拟器可视化系统提供了一个实时的Web界面，用于观察和监控模拟器的状态。该系统采用地图形式展示房间、物体、智能体及其关系，方便用户直观地了解模拟环境的当前状态。

## 功能特性

### 🎯 核心功能
- **实时状态监控**: 动态显示模拟器的当前状态
- **交互式地图**: 使用Canvas绘制的可缩放、可拖拽的环境地图
- **任务进度监控**: TODO列表形式显示任务完成情况和进度
- **多层信息展示**: 房间、物体、智能体的详细信息
- **包含关系可视化**: 准确展示物体的 in/on 包含和所属关系
- **层级结构展示**: 清晰显示容器与内容物的层级关系

### 🎨 界面特性
- **响应式设计**: 适配不同屏幕尺寸
- **实时更新**: 10Hz频率自动刷新数据
- **交互控制**: 支持鼠标拖拽、滚轮缩放
- **信息面板**: 侧边栏显示详细信息
- **任务面板**: 显示TODO列表和任务完成进度
- **机器人图标**: 网页使用🤖图标，提升用户体验

### ⚡ 性能特性
- **按需启动**: 只在配置启用时才启动，不影响核心性能
- **缓存机制**: 智能缓存减少数据处理开销
- **轻量级服务器**: 基于Python内置HTTP服务器

## 配置说明

### 启用/禁用可视化

在 `data/simulator_config.yaml` 中配置：

```yaml
visualization:
  enabled: true  # 设置为 false 可完全禁用可视化系统
```

### 详细配置选项

```yaml
visualization:
  enabled: true                    # 是否启用可视化系统
  web_server:
    host: "localhost"             # Web服务器主机地址
    port: 8080                    # Web服务器端口
    auto_open_browser: true       # 是否自动打开浏览器
  update:
    frequency: 10                 # 状态更新频率 (Hz)
    batch_size: 100              # 批量更新大小
  display:
    show_object_properties: true  # 是否显示物体属性
    show_agent_status: true       # 是否显示智能体状态
    show_relationships: true      # 是否显示物体关系
    animation_enabled: true       # 是否启用动画效果
    grid_size: 20                # 网格大小(像素)
  performance:
    max_objects_per_room: 50     # 每个房间最大显示物体数
    enable_caching: true         # 是否启用缓存
    cache_ttl: 1000             # 缓存生存时间(毫秒)
```

## 使用方法

### 1. 基本使用

```python
from embodied_simulator.core import SimulationEngine
from embodied_simulator.utils.data_loader import default_data_loader

# 加载场景数据
scene_data, task_data, verify_data = default_data_loader.load_complete_scenario("00001")

# 创建模拟引擎并启用可视化
config = {
    'visualization': {
        'enabled': True,
        'web_server': {
            'port': 8080,
            'auto_open_browser': True
        }
    }
}
engine = SimulationEngine(config=config, task_abilities=task_data.get("abilities", []))

# 初始化模拟器
success = engine.initialize_with_data({'scene': scene_data, 'task': task_data})

if success:
    # 获取可视化URL
    viz_url = engine.get_visualization_url()
    print(f"可视化界面: {viz_url}")
    
    # 执行一些动作
    agent_id = list(engine.agent_manager.get_all_agents().keys())[0]
    engine.action_handler.process_command(agent_id, "goto main_workbench_area")
    
    # 停止可视化系统
    engine.stop_visualization()
```

### 2. 程序化控制

```python
# 检查可视化状态
status = engine.get_visualization_status()
print(f"可视化状态: {status}")

# 重启可视化系统
engine.restart_visualization()

# 停止可视化系统
engine.stop_visualization()
```

## 界面说明

### 主界面布局

1. **左侧边栏**:
   - **任务信息**: TODO列表显示所有任务和完成状态
   - **环境信息**: 房间列表和智能体状态
   - **选中物体详情**: 显示点击选中的物体详细信息

2. **主视图区域**:
   - **环境地图**: Canvas绘制的交互式地图，房间居中显示
   - **控制按钮**: 重置视图按钮（适应内容功能）
   - **图例**: 左下角显示不同类型物体的颜色含义

3. **任务监控**:
   - **总体进度**: 蓝色进度条显示整体完成情况
   - **任务列表**: 每个任务显示描述、类别和完成状态
   - **实时更新**: 任务完成状态实时同步

### 交互操作

- **鼠标拖拽**: 平移地图视图
- **滚轮缩放**: 放大/缩小地图
- **点击房间**: 选中房间并显示详细信息
- **点击侧边栏**: 快速定位到对应房间或智能体

### 颜色编码

- 🟤 **棕色**: 家具 (FURNITURE)
- 🔵 **蓝色**: 物品 (ITEM)
- 🟢 **绿色**: 智能体 (AGENT)
- 🟢 **绿框**: 容器物体 (可包含其他物体)
- 🟠 **橙色虚线**: 包含关系连线 (in/on)
- 🔢 **蓝色数字**: 容器包含的物体数量

## 包含关系可视化

### 关系类型

1. **in 关系**: 物体在容器内部
   - 例如：螺丝刀在工具架内
   - 可视化：橙色虚线连接，标注 "in"

2. **on 关系**: 物体在容器表面
   - 例如：杯子在桌子上
   - 可视化：橙色虚线连接，标注 "on"

### 层级显示

- **容器物体**: 显示绿色边框，表示可以包含其他物体
- **包含数量**: 容器上方显示 `[数字]` 表示包含的物体数量
- **层级结构**: 侧边栏以树形结构显示完整的包含层级
- **位置计算**: 被包含的物体会显示在容器附近

### 交互功能

- **点击房间**: 查看该房间内的完整物体层级结构
- **层级展示**: 自动展开多层嵌套的包含关系
- **动态更新**: 当物体被移动时，包含关系实时更新

## API接口

可视化系统提供以下REST API接口：

- `GET /`: 主页面
- `GET /api/data`: 获取完整可视化数据
- `GET /api/rooms`: 获取房间列表
- `GET /api/room/{room_id}`: 获取特定房间数据
- `GET /api/agents`: 获取智能体数据
- `GET /api/objects`: 获取物体数据
- `GET /api/config`: 获取配置信息

## 性能考虑

### 高效设计

1. **按需启动**: 只有在配置启用时才会启动可视化系统
2. **缓存机制**: 智能缓存减少重复计算
3. **批量更新**: 减少频繁的数据传输
4. **轻量级服务器**: 使用Python内置HTTP服务器，无额外依赖

### 性能影响

根据测试结果：
- 初始化时间影响: < 10%
- 运行时性能影响: 几乎为0（当可视化禁用时）
- 内存占用: 约增加5-10MB

## 故障排除

### 常见问题

1. **可视化系统无法启动**
   - 检查配置文件中 `visualization.enabled` 是否为 `true`
   - 确认端口8080未被占用
   - 查看控制台错误信息

2. **浏览器无法访问**
   - 确认防火墙设置
   - 尝试使用 `http://127.0.0.1:8080` 而不是 `localhost`
   - 检查端口配置是否正确

3. **数据不更新**
   - 检查网络连接
   - 刷新浏览器页面
   - 查看控制台网络请求状态

### 调试模式

启用调试输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展开发

### 添加自定义可视化元素

可以通过修改 `visualization_data.py` 中的数据提供器来添加自定义信息：

```python
def _get_custom_data(self):
    """添加自定义可视化数据"""
    return {
        'custom_info': 'your_data_here'
    }
```

### 自定义前端样式

修改 `web_server.py` 中的HTML模板或添加CSS样式来自定义界面外观。

## 更新日志

- **v1.0.0**: 初始版本，支持基本的实时可视化功能
- 支持房间、物体、智能体的可视化展示
- 提供交互式地图界面
- 实现配置化的启用/禁用机制
