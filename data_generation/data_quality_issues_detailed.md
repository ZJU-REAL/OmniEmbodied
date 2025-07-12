# 🔍 数据质量问题详细分析

基于 R1 验证的 10 个任务样本，我们发现了以下系统性的数据质量问题：

---

## 📊 问题分类统计

| 问题类型 | 数量 | 占比 | 严重程度 |
|---------|------|------|----------|
| 物理约束违反 | 4 | 40% | 🔴 严重 |
| 逻辑死锁/循环依赖 | 3 | 30% | 🔴 严重 |
| 任务分类错误 | 1 | 10% | 🟡 中等 |
| 复杂依赖链问题 | 2 | 20% | 🟡 中等 |

---

## 🔴 严重问题：物理约束违反

### 问题描述
任务要求机器人操作超出其物理能力限制的对象，导致任务在物理上不可能完成。

### 具体案例

#### 案例 1: 重量约束违反
**任务**: "Move the hazardous_waste_barrel_1 to the break_room"
- **对象重量**: 200.0 kg
- **机器人承重**: 50.0 kg (单个) / 100.0 kg (两个协作)
- **问题**: 即使两个机器人协作也无法搬运

#### 案例 2: 尺寸约束违反  
**任务**: "Cooperatively move the heavy live_release_tank_1"
- **对象尺寸**: [0.8, 0.8, 1.2]
- **机器人尺寸限制**: [1.0, 1.0, 1.0]
- **问题**: 对象高度(1.2)超过机器人z轴限制(1.0)

#### 案例 3: 超大型设备操作
**任务**: "Repair the broken baler_machine_1"
- **设备尺寸**: [2.5, 1.8, 2.0]
- **设备重量**: 800 kg
- **问题**: 远超机器人操作能力范围

### 根本原因
1. **生成时缺乏物理约束检查** - 任务生成器没有验证对象属性与机器人能力的匹配性
2. **场景与任务生成分离** - 场景生成器和任务生成器之间缺乏约束同步
3. **协作能力建模不准确** - 对多机器人协作的物理限制理解不足

### 解决方案
```python
def validate_physical_constraints(task, scene_objects, agent_config):
    """验证物理约束"""
    for obj_id in extract_task_objects(task):
        obj = scene_objects[obj_id]
        
        # 检查重量约束
        if obj.weight > sum(agent.max_weight for agent in agents):
            return False, f"Object {obj_id} too heavy"
            
        # 检查尺寸约束
        if any(obj.size[i] > max(agent.max_size[i] for agent in agents) 
               for i in range(3)):
            return False, f"Object {obj_id} too large"
            
    return True, "OK"
```

---

## 🔴 严重问题：逻辑死锁/循环依赖

### 问题描述
任务设计中存在逻辑上的循环依赖，导致任务无法开始或完成。

### 具体案例

#### 案例 1: 房间访问死锁
**任务**: "Find the ashtray with the napkin underneath and place it on folding_table_1"
- **目标位置**: `folding_table_1` 在 `hidden_safe_room`
- **访问机制**: 需要拉取 `communist_manifesto_book_1` 打开 `false_bookshelf_1`
- **问题**: `communist_manifesto_book_1` 位于 `false_bookshelf_1` 内部，而 `false_bookshelf_1` 位于 `hidden_safe_room` 内部
- **循环依赖**: 进入房间 → 需要书 → 书在房间内 → 无法进入房间

#### 案例 2: 工具访问死锁
**任务**: "Repair the broken baler_machine_1"
- **需要工具**: `pallet_jack_handle_1` (修理工具)
- **工具位置**: `backroom_storage`
- **访问要求**: 需要 `pallet_jack_1` 来移动阻挡物
- **问题**: `pallet_jack_1` 已损坏，需要 `pallet_jack_handle_1` 来修理
- **循环依赖**: 修理机器 → 需要工具 → 工具需要搬运车 → 搬运车需要工具修理

### 根本原因
1. **场景设计缺乏可达性验证** - 没有检查所有对象和位置的可达性
2. **容器嵌套逻辑错误** - 触发机制与容器内容的循环依赖
3. **依赖链分析不足** - 没有分析任务完成所需的完整依赖链

### 解决方案
```python
def validate_accessibility(scene):
    """验证场景可达性"""
    # 构建依赖图
    dependency_graph = build_dependency_graph(scene)
    
    # 检测循环依赖
    cycles = detect_cycles(dependency_graph)
    if cycles:
        return False, f"Circular dependencies: {cycles}"
    
    # 验证所有对象可达
    for obj in scene.objects:
        if not is_reachable(obj, scene):
            return False, f"Object {obj.id} unreachable"
    
    return True, "OK"
```

---

## 🟡 中等问题：任务分类错误

### 问题描述
任务被分配到错误的类别，导致验证逻辑与实际任务需求不匹配。

### 具体案例

#### 案例: 协作分类错误
**任务**: "Have robot_1 and robot_2 cooperate to lock the gear_locker_1"
- **分类**: `explicit_collaboration`
- **实际情况**: 单个机器人就能完成
- **问题**: 不需要真正的协作，分类错误

### 根本原因
1. **分类标准不明确** - 缺乏明确的任务分类标准
2. **协作需求判断错误** - 没有准确评估任务是否真正需要多机器人协作
3. **验证逻辑与分类不匹配** - 分类与实际验证要求不一致

### 解决方案
```python
def validate_task_category(task, scene):
    """验证任务分类"""
    category = task.category
    
    if category in ['explicit_collaboration', 'implicit_collaboration']:
        # 检查是否真正需要协作
        if can_single_agent_complete(task, scene):
            return False, f"Task doesn't require collaboration"
    
    return True, "OK"
```

---

## 🟡 中等问题：复杂依赖链问题

### 问题描述
任务涉及复杂的依赖链，但某些环节缺失或不可行。

### 具体案例

#### 案例: 工具链断裂
**任务**: "Use scissors_1 to unwrap censorship_manual_1"
- **依赖链**: 获取剪刀 → 找到手册 → 解包装 → 放置
- **断裂点**: 手册在无法打开的容器中
- **问题**: 依赖链中的关键环节不可行

### 根本原因
1. **依赖链完整性检查不足** - 没有验证完整的任务执行路径
2. **前置条件验证缺失** - 没有检查所有必要的前置条件
3. **工具可用性验证不足** - 没有确保所需工具真正可用

---

## 🛠️ 系统性解决方案

### 1. 建立多层验证体系

```python
class DataQualityValidator:
    def validate_task(self, task, scene, agents):
        # 第一层：基础格式验证
        if not self.validate_format(task):
            return False, "Format error"
        
        # 第二层：物理约束验证
        if not self.validate_physical_constraints(task, scene, agents):
            return False, "Physical constraint violation"
        
        # 第三层：逻辑一致性验证
        if not self.validate_logical_consistency(task, scene):
            return False, "Logical inconsistency"
        
        # 第四层：依赖链验证
        if not self.validate_dependency_chain(task, scene):
            return False, "Broken dependency chain"
        
        # 第五层：分类验证
        if not self.validate_category(task, scene):
            return False, "Category mismatch"
        
        return True, "Valid"
```

### 2. 改进生成提示

在任务生成提示中明确添加：
- 物理约束说明
- 逻辑一致性要求
- 依赖链完整性要求
- 分类标准说明

### 3. 建立约束数据库

```python
AGENT_CONSTRAINTS = {
    "max_weight": 50.0,
    "max_size": [1.0, 1.0, 1.0],
    "max_grasp_limit": 1.0,
    "abilities": ["move", "grab", "place", "turn_on", "turn_off", ...]
}

COLLABORATION_THRESHOLDS = {
    "weight_requires_collaboration": 75.0,  # 超过此重量需要协作
    "size_requires_collaboration": [1.5, 1.5, 1.5],  # 超过此尺寸需要协作
}
```

### 4. 实施渐进式验证

1. **简单任务优先** - 先确保简单任务质量
2. **逐步增加复杂度** - 在简单任务稳定后增加复杂任务
3. **持续监控** - 建立质量监控和反馈机制

---

## 📈 质量改进预期

通过实施上述解决方案，预期能够：

- **物理约束违反率**: 从 40% 降至 0%
- **逻辑死锁率**: 从 30% 降至 5%
- **分类错误率**: 从 10% 降至 2%
- **整体 R1 成功率**: 从 20% 提升至 75%+

这将使数据质量达到可以进行批量生成的标准。

---

## 🔧 具体修复示例

### 修复案例 1: 物理约束违反

**原始任务** (有问题):
```json
{
  "task_description": "Move the hazardous_waste_barrel_1 to the break_room",
  "task_category": "implicit_collaboration",
  "validation_checks": [{"id": "hazardous_waste_barrel_1", "location_id": "in:break_room"}]
}
```

**问题**: 桶重 200kg，超过机器人承重能力

**修复方案 A** - 调整对象重量:
```json
{
  "object_id": "hazardous_waste_barrel_1",
  "weight": 80.0,  // 改为两个机器人可以协作搬运的重量
  "size": [0.6, 0.6, 0.8]  // 确保尺寸在限制内
}
```

**修复方案 B** - 添加辅助工具:
```json
{
  "objects": [
    {
      "id": "heavy_duty_cart_1",
      "provides_abilities": ["transport_heavy_objects"],
      "max_load": 300.0
    }
  ],
  "task_description": "Use the heavy_duty_cart_1 to move hazardous_waste_barrel_1 to break_room"
}
```

### 修复案例 2: 逻辑死锁

**原始场景** (有问题):
```json
{
  "rooms": [
    {"id": "hidden_safe_room", "connected_to": []}
  ],
  "objects": [
    {
      "id": "false_bookshelf_1",
      "location_id": "in:hidden_safe_room",
      "trigger_mechanism": "pull_communist_manifesto_book_1"
    },
    {
      "id": "communist_manifesto_book_1",
      "location_id": "in:false_bookshelf_1"
    }
  ]
}
```

**修复方案** - 打破循环依赖:
```json
{
  "objects": [
    {
      "id": "false_bookshelf_1",
      "location_id": "in:gear_storage_workshop",  // 移到可访问的房间
      "trigger_mechanism": "pull_communist_manifesto_book_1"
    },
    {
      "id": "communist_manifesto_book_1",
      "location_id": "in:false_bookshelf_1"  // 保持在书架中，但书架现在可访问
    }
  ]
}
```

### 修复案例 3: 任务分类错误

**原始任务** (有问题):
```json
{
  "task_description": "Have robot_1 and robot_2 cooperate to lock the gear_locker_1",
  "task_category": "explicit_collaboration"  // 错误分类
}
```

**修复方案 A** - 修正分类:
```json
{
  "task_description": "Lock the gear_locker_1 using the keycard_1",
  "task_category": "direct_command"  // 正确分类
}
```

**修复方案 B** - 修改任务使其真正需要协作:
```json
{
  "task_description": "Have robot_1 hold the gear_locker_1 steady while robot_2 uses the keycard_1 to lock it",
  "task_category": "explicit_collaboration",
  "validation_checks": [
    {"id": "gear_locker_1", "is_locked": true},
    {"coordination_required": true}  // 添加协作验证
  ]
}
```

---

## 📋 实施检查清单

### 立即行动项 ✅
- [ ] 实现物理约束验证器
- [ ] 修复已识别的循环依赖问题
- [ ] 建立任务分类验证逻辑
- [ ] 创建约束数据库

### 验证流程 ✅
- [ ] 对每个新生成的任务运行完整验证
- [ ] 建立自动化测试管道
- [ ] 设置质量阈值和监控

### 持续改进 ✅
- [ ] 收集更多 badcase 样本
- [ ] 优化生成提示
- [ ] 建立质量反馈循环

通过这些具体的修复措施，我们可以系统性地解决数据质量问题，为批量生成做好准备。
