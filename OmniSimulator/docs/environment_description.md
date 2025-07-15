# 环境描述配置详解

本文档详细说明环境描述配置如何影响提示词中的房间信息完整性，以及如何根据不同任务需求进行配置。

## 概述

环境描述是LLM智能体获取环境信息的主要途径，直接影响智能体的决策质量。框架提供了灵活的配置选项来控制环境描述的详细程度和内容范围。

## 配置参数详解

### detail_level - 详细程度控制

控制提示词中包含的房间信息范围：

#### `detail_level: "full"` - 完整环境描述
- **包含内容**：所有房间的完整信息
- **输出格式**：
  ```
  ================ 环境概述 ================
  共有 4 个房间, 54 个物体, 2 个智能体

  ================ 房间详情 ================
  ▶ 房间：Filter Simulation Station (ID: filter_simulation_station)
    • 房间属性: type: simulation
    • 智能体: robot_1, robot_2
    • 物体: [详细物体列表]
  
  ▶ 房间：Main Workbench Area (ID: main_workbench_area)
    • 房间属性: type: workbench
    • 物体: [详细物体列表]
  
  [其他房间...]
  
  ================ 智能体详情 ================
  [所有智能体的详细状态]
  ```
- **适用场景**：
  - 全局规划任务
  - 多房间协调任务
  - 需要了解完整环境布局的任务

#### `detail_level: "room"` - 当前房间描述（默认）
- **包含内容**：只有智能体当前所在房间的信息
- **输出格式**：
  ```
  ▶ 房间：Filter Simulation Station (ID: filter_simulation_station)
    • 房间属性: type: simulation
    • 连接房间: Main Workbench Area, Storage Shelves
    • 智能体: robot_1, robot_2
    • 物体: [当前房间物体列表]
  ```
- **适用场景**：
  - 局部操作任务
  - 减少提示词长度的场景
  - 专注于当前环境的任务

#### `detail_level: "brief"` - 简要描述
- **包含内容**：只有智能体自身状态
- **输出格式**：
  ```
  ▶ 智能体：robot_1 (ID: agent_1)
    • 位置：Filter Simulation Station
    • 物理属性：负载 0.0/10.0kg, 抓取容量 0/1个
    • 持有物品：无
  ```
- **适用场景**：
  - 简单任务
  - 最小化提示词长度
  - 主要依赖历史信息的任务

### show_object_properties - 物体属性显示

控制是否显示物体的详细属性信息：

#### `show_object_properties: true`
- **显示内容**：
  ```
  ◆ Triple-Monitor Setup (ID: triple_monitor_setup_1, 类型: FURNITURE)
    • 位置: 在Filter Simulation Station里面
    • 状态: is_on: True, is_open: False
    • 属性:
      - 尺寸: 长1.5m × 宽0.4m × 高0.8m
      - 重量: 25.0kg
      - 品牌: Dell
      - 条件: one screen flickering
  ```

#### `show_object_properties: false`
- **显示内容**：
  ```
  ◆ Triple-Monitor Setup (ID: triple_monitor_setup_1, 类型: FURNITURE)
    • 位置: 在Filter Simulation Station里面
    • 状态: is_on: True, is_open: False
  ```

### only_show_discovered - 发现状态过滤

控制是否只显示已发现的物体：

#### `only_show_discovered: true` - 现实探索模式
- 只显示智能体已经探索发现的物体
- 符合现实世界的认知限制
- 鼓励智能体主动探索环境

#### `only_show_discovered: false` - 全知模式
- 显示所有物体，包括未探索的
- 适用于测试和调试
- 适用于不需要探索机制的任务

## 配置示例

### 全局规划任务配置
```yaml
env_description:
  detail_level: "full"           # 查看所有房间
  show_object_properties: true   # 需要详细物体信息进行规划
  only_show_discovered: false    # 全知视角便于规划
```

### 探索任务配置
```yaml
env_description:
  detail_level: "room"           # 专注当前房间
  show_object_properties: true   # 需要物体详情进行交互
  only_show_discovered: true     # 符合探索的现实性
```

### 简单操作任务配置
```yaml
env_description:
  detail_level: "room"           # 当前房间足够
  show_object_properties: false  # 不需要详细属性
  only_show_discovered: true     # 已知物体即可
```

### 轻量级任务配置
```yaml
env_description:
  detail_level: "brief"          # 最小环境信息
  show_object_properties: false  # 无需物体属性
  only_show_discovered: true     # 减少信息量
```

## 性能考虑

### 提示词长度影响
- **`detail_level: "full"`**：可能产生很长的提示词，影响LLM处理速度
- **`detail_level: "room"`**：平衡信息量和性能
- **`detail_level: "brief"`**：最短提示词，最快处理速度

### 建议
1. **开发阶段**：使用 `detail_level: "full"` 和 `only_show_discovered: false` 便于调试
2. **生产环境**：根据任务复杂度选择合适的 `detail_level`
3. **性能敏感场景**：使用 `detail_level: "brief"` 或 `"room"`

## 配置文件位置

- **单智能体**：`config/defaults/single_agent_config.yaml`
- **中心化多智能体**：`config/defaults/centralized_config.yaml`
- **去中心化多智能体**：`config/defaults/decentralized_config.yaml`

## 动态配置

也可以在代码中动态设置环境描述配置：

```python
from embodied_framework.utils import create_env_description_config

# 创建环境描述配置
env_config = create_env_description_config(
    detail_level='full',
    show_properties=True,
    only_discovered=False
)

# 在智能体配置中使用
agent_config = {
    'env_description': env_config,
    # 其他配置...
}
```

## 总结

环境描述配置直接影响LLM智能体对环境的认知能力：
- 选择合适的 `detail_level` 确保智能体获得足够的环境信息
- 根据任务需求调整 `show_object_properties` 和 `only_show_discovered`
- 在信息完整性和性能之间找到平衡点
