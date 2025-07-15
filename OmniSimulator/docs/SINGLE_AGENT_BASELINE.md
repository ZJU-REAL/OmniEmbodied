# 单智能体Baseline实现

## 概述

本文档介绍了在 `examples/single_agent_example.py` 中实现的单智能体baseline，该实现展示了如何使用大模型进行决策并与模拟器进行交互。

## 核心特性

### ✅ 完整的LLM集成
- **多API支持**: OpenAI和自定义API（如DeepSeek）
- **统一openai库**: 使用openai库统一处理所有API调用
- **智能JSON解析**: 自动处理```json代码块格式
- **错误重试机制**: 自动重试失败的API调用
- **配置驱动**: 通过YAML配置文件管理

### ✅ 动态提示词生成
- **实时动作描述**: 使用 `get_agent_supported_actions_description()` API
- **状态感知**: 包含当前位置、库存和历史信息
- **任务导向**: 集成任务背景和目标
- **结构化设计**: 清晰的提示词结构

### ✅ 智能决策执行
- **JSON格式响应**: 包含思考、动作和原因
- **历史记录**: 跟踪执行历史和统计信息
- **任务完成检测**: 自动检查任务完成状态
- **详细日志**: 完整的执行过程记录

## 实现架构

### 核心类

#### 1. LLMClient
```python
class LLMClient:
    """统一的LLM客户端，支持多种API提供商，使用openai库"""

    def __init__(self, config: Dict[str, Any])
    def simple_completion(self, prompt: str) -> str
    def get_model_info(self) -> Dict[str, Any]
    def _init_openai_client(self)  # OpenAI官方API
    def _init_custom_client(self)  # 自定义API（使用openai库）
```

#### 2. LLMAgent
```python
class LLMAgent:
    """基于大模型的智能体"""
    
    def __init__(self, bridge: SimulatorBridge, agent_id: str, config: Dict[str, Any])
    def step(self) -> tuple  # 执行一步决策
    def _generate_prompt(self) -> str  # 生成动态提示词
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, str]]
```

### 数据流

```
智能体状态 → 动态提示词生成 → LLM调用 → JSON响应解析 → 动作执行 → 结果记录
```

## 测试结果

### 性能指标
- ✅ **成功率**: 40.0% (6/15 动作成功)
- ✅ **运行时间**: 145.6秒
- ✅ **LLM调用**: 15次
- ✅ **环境探索**: 发现29个新物体
- ✅ **真实API**: 成功调用DeepSeek API（使用openai库）

### 执行示例
```
步骤 1: EXPLORE filter_simulation_station → SUCCESS (发现11个新物体)
步骤 6: GOTO main_workbench_area → SUCCESS 
步骤 7: EXPLORE main_workbench_area → SUCCESS (发现18个新物体)
```

## 配置说明

### LLM配置 (`config/defaults/llm_config.yaml`)
```yaml
mode: "api"
api:
  provider: "custom"  # 或 "openai"
  custom:
    model: "deepseek-chat"
    temperature: 0.1
    max_tokens: 4096
    api_key: "your-api-key"
    endpoint: "https://api.deepseek.com"
```

## 使用方法

### 基础运行
```bash
cd /path/to/embodied_framework
python examples/single_agent_example.py
```

### 自定义配置
1. 修改 `config/defaults/llm_config.yaml` 中的API配置
2. 设置环境变量 `CUSTOM_LLM_API_KEY` 或 `OPENAI_API_KEY`
3. 运行示例

## 提示词结构

### 完整提示词包含
1. **系统角色**: 智能机器人助手身份
2. **核心能力**: 移动、操作、设备控制等
3. **行为准则**: 任务导向、先探索后操作等
4. **响应格式**: 严格的JSON格式要求
5. **可执行动作**: 完整的动作描述（3564字符）
6. **当前任务**: 任务背景和目标
7. **当前状态**: 位置、库存、历史信息

### JSON响应格式
```json
{
    "thought": "思考过程和推理逻辑",
    "action": "具体动作命令",
    "reason": "选择这个动作的原因"
}
```

## 关键特性

### 统一的openai库集成
- **统一接口**: 使用openai库处理所有API调用
- **OpenAI官方API**: 直接支持GPT-3.5/GPT-4等模型
- **自定义API**: 通过base_url参数支持DeepSeek等第三方API
- **一致性**: 所有API调用使用相同的接口和错误处理

### 智能JSON解析
- 自动处理 ```json 代码块格式
- 支持多种JSON提取模式
- 健壮的错误处理机制

### 动态提示词
- 实时获取智能体支持的动作
- 包含当前状态和历史信息
- 任务导向的内容生成

### 执行统计
- 成功率、运行时间统计
- 详细的执行历史记录
- LLM调用次数和模型信息

## 扩展指南

### 添加新的LLM提供商
```python
def _init_new_provider(self):
    """初始化新的API提供商（使用openai库）"""
    # 使用openai库创建客户端，只需指定base_url
    self.new_client = openai.OpenAI(
        api_key=self.api_key,
        base_url="https://api.new-provider.com"  # 新提供商的API端点
    )

def _new_provider_completion(self, prompt: str) -> str:
    """新提供商的API调用"""
    response = self.new_client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=self.temperature,
        max_tokens=self.max_tokens
    )
    return response.choices[0].message.content
```

### 自定义提示词
```python
def _generate_custom_prompt(self) -> str:
    """生成自定义提示词"""
    # 添加自定义的提示词内容
    pass
```

### 增强决策逻辑
```python
def _enhanced_decision_making(self, response: Dict[str, str]) -> str:
    """增强的决策逻辑"""
    # 添加额外的决策验证和优化
    pass
```

## 故障排除

### 常见问题

1. **LLM API调用失败**
   - 检查API密钥配置
   - 验证网络连接
   - 确认API额度

2. **JSON解析失败**
   - 检查LLM响应格式
   - 调整temperature参数
   - 优化提示词清晰度

3. **动作执行失败**
   - 验证动作命令格式
   - 检查物体ID有效性
   - 确认环境状态

### 调试技巧
```python
# 启用详细日志
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 检查提示词内容
prompt = agent._generate_prompt()
print(f"提示词长度: {len(prompt)}")

# 监控执行统计
stats = agent.get_statistics()
print(f"成功率: {stats['success_rate']*100:.1f}%")
```

## 最佳实践

### 1. 提示词优化
- 使用清晰的结构化格式
- 包含必要的上下文信息
- 避免过长的提示词
- 使用emoji增强可读性

### 2. 错误处理
- 实现健壮的JSON解析
- 提供有意义的错误信息
- 记录和分析失败模式
- 避免无限重试循环

### 3. 性能监控
- 跟踪成功率和执行时间
- 监控LLM调用频率
- 分析动作执行模式
- 优化提示词长度

## 总结

单智能体baseline提供了一个完整的、可工作的LLM与模拟器交互实现：

- 🚀 **真实LLM集成**: 支持多种API提供商
- 🧠 **智能决策**: 基于动态提示词的决策生成
- 📊 **详细统计**: 完整的性能监控和历史记录
- 🛡️ **健壮性**: 完善的错误处理和重试机制
- 🔧 **可扩展**: 易于添加新功能和提供商

这个baseline为更复杂的智能体实现提供了坚实的基础。
