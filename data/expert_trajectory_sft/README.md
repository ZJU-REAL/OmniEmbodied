---
license: mit
task_categories:
- text-generation
- robotics
- reinforcement-learning
language:
- en
size_categories:
- 1K<n<10K
tags:
- embodied-ai
- agent-reasoning
- supervised-fine-tuning
- expert-trajectories
- physical-interaction
- tool-usage
- collaboration
pretty_name: "OmniEAR Expert Trajectory Dataset"
---

# OmniEAR Expert Trajectory Dataset

## Dataset Summary

The OmniEAR Expert Trajectory SFT Dataset is a comprehensive collection of high-quality expert demonstration trajectories specifically designed for supervised fine-tuning (SFT) of embodied reasoning models. This dataset contains **1,982 instruction-following examples** across single-agent and multi-agent scenarios, focusing on physical interactions, tool usage, and collaborative reasoning in embodied environments.

## Dataset Structure

### File Organization
```
expert_trajectory_sft/
├── single_agent/              # Single-agent reasoning tasks (1,262 samples)
│   ├── attribute_reasoning_*.json    # Attribute comparison and inference (350 samples)
│   ├── compound_reasoning_*.json     # Multi-step complex reasoning (269 samples)
│   ├── direct_command_*.json         # Basic instruction following (313 samples)
│   └── tool_use_*.json              # Dynamic capability acquisition (330 samples)
└── centralized_agent/         # Multi-agent coordination tasks (720 samples)
    └── compound_collaboration_*.json # Complex collaborative scenarios (720 samples)
```

### Data Format
Each JSON file contains an array of structured training examples:
```json
[
  {
    "instruction": "Detailed task instruction with environment context and agent capabilities",
    "output": "Expected agent response following standardized action format",
    "system": "System prompt defining operational framework and behavioral guidelines"
  }
]
```

## Task Categories

### Single-Agent Tasks (1,262 samples)
- **Direct Command** (313 samples): Basic instruction following requiring spatial understanding and object manipulation
- **Attribute Reasoning** (350 samples): Comparison and inference over continuous physical properties like weight, temperature, and material composition
- **Tool Use** (330 samples): Dynamic capability acquisition through tool manipulation and environmental interaction
- **Compound Reasoning** (269 samples): Multi-step planning integrating attribute reasoning, tool usage, and complex spatial navigation

### Multi-Agent Tasks (720 samples)
- **Compound Collaboration** (720 samples): Complex scenarios requiring autonomous coordination recognition, tool acquisition, and synchronized execution between multiple agents

## Usage

### Quick Download (from GitHub Repository)
```bash
cd data/expert_trajectory_sft/
python download_expert_data.py
```

### Direct HuggingFace Access
```python
from datasets import load_dataset

# Load complete dataset
dataset = load_dataset("wangzx1210/OmniEAR")

# Load specific splits
single_agent = load_dataset("wangzx1210/OmniEAR", data_files="single_agent/*.json")
multi_agent = load_dataset("wangzx1210/OmniEAR", data_files="centralized_agent/*.json")
```

### Fine-tuning Example
```python
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer

# Load model and tokenizer
model = AutoModelForCausalLM.from_pretrained("your-base-model")
tokenizer = AutoTokenizer.from_pretrained("your-base-model")

# Format training samples
def format_sample(example):
    return f"System: {example['system']}\n\nInstruction: {example['instruction']}\n\nResponse: {example['output']}"

# Training configuration
training_args = TrainingArguments(
    output_dir="./omni-ear-finetuned",
    per_device_train_batch_size=4,
    learning_rate=5e-5,
    num_train_epochs=3,
    logging_steps=100,
    save_strategy="epoch"
)

# Initialize trainer and start fine-tuning
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=formatted_dataset,
    tokenizer=tokenizer
)

trainer.train()
```

## Dataset Statistics

| Category | Task Type | Sample Count | Average Length | Complexity Level |
|----------|-----------|--------------|----------------|------------------|
| Single-Agent | Direct Command | 313 | ~2.1K chars | L1 - Basic |
| Single-Agent | Attribute Reasoning | 350 | ~2.3K chars | L2 - Intermediate |
| Single-Agent | Tool Use | 330 | ~2.5K chars | L2 - Intermediate |
| Single-Agent | Compound Reasoning | 269 | ~2.8K chars | L3 - Advanced |
| Multi-Agent | Compound Collaboration | 720 | ~3.2K chars | L3 - Advanced |
| **Total** | **All Categories** | **1,982** | **~2.6K chars** | **Mixed Levels** |

## Data Quality

### Expert Annotation Process
- **Generation Method**: LLM-assisted generation with expert validation
- **Quality Control**: Multi-stage validation including task feasibility, action sequence correctness, and format consistency
- **Expert Review**: Manual verification of complex reasoning chains and collaborative scenarios
- **Consistency Check**: Automated validation of instruction-output alignment and system prompt adherence

### Validation Metrics
- **Format Compliance**: 100% (all samples follow standardized JSON structure)
- **Action Validity**: 98.7% (actions are executable within environment constraints)
- **Instruction Alignment**: 97.8% (outputs correctly address instruction requirements)
- **Reasoning Coherence**: 96.5% (logical consistency in multi-step reasoning chains)

## Ethical Considerations

- **Data Privacy**: No personal or sensitive information included in trajectories
- **Bias Mitigation**: Balanced representation across task categories and complexity levels
- **Use Restrictions**: Intended for research and educational purposes in embodied AI
- **Attribution**: Please cite the original paper when using this dataset

## Citation

If you use this dataset in your research, please cite our paper:

```bibtex
@misc{wang2025omniearbenchmarkingagentreasoning,
      title={OmniEAR: Benchmarking Agent Reasoning in Embodied Tasks}, 
      author={Zixuan Wang and Dingming Li and Hongxing Li and Shuo Chen and Yuchen Yan and Wenqi Zhang and Yongliang Shen and Weiming Lu and Jun Xiao and Yueting Zhuang},
      year={2025},
      eprint={2508.05614},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2508.05614}, 
}
```

## License

This dataset is released under the MIT License.

## Contact

For questions about this dataset, please:
- Open an issue on our [GitHub repository](https://github.com/ZJU-REAL/OmniEmbodied)
- Contact the corresponding author

## Related Resources

- **Main Repository**: [ZJU-REAL/OmniEmbodied](https://github.com/ZJU-REAL/OmniEmbodied)
- **Paper**: [arXiv:2508.05614](https://arxiv.org/abs/2508.05614)
- **Documentation**: [omniembodied.readthedocs.io](https://omniembodied.readthedocs.io/en/latest/)
