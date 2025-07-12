# Data Generation Pipeline

A comprehensive, production-ready data generation system that transforms raw text into structured multi-agent collaborative scenarios using Large Language Models (LLMs). The system features a robust 4-stage pipeline with automatic quality assurance, intelligent task validation, and extensive customization options.

## 🌟 Key Features

### 🚀 Core Capabilities
- **Complete 4-Stage Pipeline**: Raw Text → Clue → Scene → Task → Validation & Repair
- **Automatic Quality Assurance**: Built-in validation and intelligent repair system
- **Enhanced Action Schema**: Rich action information with attributes, tools, and descriptions
- **Guaranteed Core Actions**: Every scene includes 'open' and 'close' actions
- **Multi-Agent Focus**: Generates collaborative tasks requiring multiple AI agents
- **English Task Generation**: Professional English task descriptions with thematic coherence

### 🔧 Technical Excellence
- **Thread-Safe Processing**: Robust concurrent processing with proper error handling
- **Modular Architecture**: Clean separation with base classes and specialized generators
- **Resume Capability**: Skip completed items to resume interrupted executions
- **Comprehensive Logging**: Detailed logs with progress tracking and validation reports
- **Token Usage Tracking**: Monitor API costs with detailed consumption statistics
- **Flexible Configuration**: Extensive customization through YAML configuration files

### 🛡️ Quality Assurance
- **Automatic Task Validation**: 3-step validation process (category → object ID → attributes)
- **Intelligent Repair**: Smart fixing using CSV database and domain knowledge
- **Detailed Fix Logs**: Complete audit trail of all validation and repair operations
- **Error Recovery**: Graceful handling of failures without interrupting the pipeline

## 📁 Project Structure

```
data_generation/
├── pipeline.py                    # 🚀 Main pipeline orchestrator with integrated validation
├── requirements.txt               # 📦 Python dependencies
├── README.md                     # 📖 Complete documentation (this file)
├── .gitignore                    # 🚫 Git ignore rules for clean repository
│
├── generators/                   # 🏭 Data generation modules
│   ├── __init__.py              # Package initialization
│   ├── base_generator.py        # Abstract base class for all generators
│   ├── clue_generator.py        # Generates conceptual clues from raw text
│   ├── scene_generator.py       # Creates detailed 3D scenes with guaranteed actions
│   └── task_generator.py        # Generates tasks with rich action schemas
│
├── utils/                       # 🛠️ Utility modules
│   ├── __init__.py              # Package initialization
│   ├── logger.py                # Centralized logging system with multiple levels
│   ├── config_loader.py         # YAML configuration management
│   ├── json_utils.py            # JSON processing and repair utilities
│   ├── thread_pool.py           # Thread pool management with retry logic
│   ├── action_manager.py        # Scene ability analysis and extraction
│   ├── scene_validator.py       # Scene validation and auto-fixing logic
│   └── task_validator.py        # Task validation and intelligent repair system
│
├── config/                      # ⚙️ Configuration files
│   ├── pipeline.yaml            # Main pipeline settings and threading
│   ├── clue_gen_config.yaml     # Clue generator LLM and prompt configuration
│   ├── scene_gen_config.yaml    # Scene generator with action schema settings
│   └── task_gen_config.yaml     # Task generator with validation criteria
│
├── data/                        # 📊 Data directory
│   ├── news.json                # Input raw text data (customizable)
│   ├── attribute_actions.csv    # Action definitions database for validation
│   ├── e2e_summary.json         # Pipeline execution summary and statistics
│   ├── clue/                    # Generated clue files (*.json)
│   ├── scene/                   # Generated scene files (*.json)
│   └── task/                    # Generated task files with embedded verification
│
└── logs/                        # 📝 Execution logs
    ├── pipeline.log             # Main pipeline logs with validation details
    ├── clue_raw.log            # Raw LLM responses for clue generation
    ├── scene_raw.log           # Raw LLM responses for scene generation
    ├── task_raw.log            # Raw LLM responses for task generation
    └── *_task_fixes_*.log      # Timestamped task validation and repair logs
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (recommended: Python 3.9 or 3.10)
- **LLM API Access**: OpenAI API, DeepSeek API, or compatible endpoint
- **4GB+ RAM** for optimal performance with multiple threads
- **Stable internet connection** for API calls

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd data_generation
   pip install -r requirements.txt
   ```

2. **Configure API settings:**

   Edit the configuration files in `config/` directory. All generators need API configuration:

   **For OpenAI:**
   ```yaml
   # In clue_gen_config.yaml, scene_gen_config.yaml, task_gen_config.yaml
   api: openai
   endpoint: https://api.openai.com/v1
   model: gpt-4
   api_key: "sk-your-openai-api-key-here"
   ```

   **For DeepSeek (recommended for cost-effectiveness):**
   ```yaml
   api: openai
   endpoint: https://api.deepseek.com
   model: deepseek-chat
   api_key: "sk-your-deepseek-api-key-here"
   ```

3. **Prepare input data:**

   Create or edit `data/news.json` with your raw text data:
   ```json
   [
     {
       "id": 1,
       "raw_text": "A bustling restaurant kitchen during dinner rush with multiple chefs coordinating complex orders."
     },
     {
       "id": 2,
       "raw_text": "A high-tech laboratory where researchers collaborate on sensitive experiments."
     },
     {
       "id": 3,
       "raw_text": "A construction site where workers must coordinate to build a complex structure safely."
     }
   ]
   ```

### Running the Pipeline

#### Basic Usage

**Run complete pipeline:**
```bash
python pipeline.py
```

**Process specific range:**
```bash
# Process items 1-5 with 4 threads
python pipeline.py --start-id 1 --end-id 5 --threads 4
```

**Resume interrupted execution:**
```bash
# Automatically skips completed items
python pipeline.py --start-id 1 --end-id 100
```

#### Advanced Usage

**Custom input file:**
```bash
python pipeline.py --input data/custom_scenarios.json --start-id 1 --end-id 20
```

**Debug mode with detailed logging:**
```bash
python pipeline.py --log-level DEBUG --threads 1
```

**High-throughput processing:**
```bash
python pipeline.py --threads 8 --start-id 1 --end-id 1000
```

#### Standalone Generator Mode

Run individual generators for batch processing:

```bash
# Generate clues only (uses clue_gen_config.yaml thread_num)
python -m generators.clue_generator

# Generate scenes only (uses scene_gen_config.yaml thread_num)
python -m generators.scene_generator

# Generate tasks only (uses task_gen_config.yaml thread_num)
python -m generators.task_generator
```

## 📋 Command Line Reference

### Basic Syntax
```bash
python pipeline.py [OPTIONS]
```

### Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--input` | PATH | `data/news.json` | Input JSON file with raw text data |
| `--start-id` | INT | `0` | Starting ID (inclusive) |
| `--end-id` | INT | `null` | Ending ID (inclusive, null = process all) |
| `--threads` | INT | `4` | Number of parallel threads |
| `--log-level` | STR | `INFO` | Logging level: DEBUG\|INFO\|WARNING\|ERROR |
| `--help` | - | - | Show help message and exit |

### Usage Examples

```bash
# Process all items with default settings
python pipeline.py

# Process specific range with custom threading
python pipeline.py --start-id 10 --end-id 50 --threads 8

# Use custom input file
python pipeline.py --input data/custom_scenarios.json

# Debug mode with single thread
python pipeline.py --log-level DEBUG --threads 1

# High-performance batch processing
python pipeline.py --start-id 1 --end-id 1000 --threads 12
```

## 🔄 Data Flow & Pipeline Architecture

The system processes data through four sequential stages with automatic quality assurance:

```
📝 Raw Text → 🔍 Clue Generation → 🏗️ Scene Generation → 📋 Task Generation → ✅ Validation & Repair
```

### Stage 1: Clue Generation 🔍
**Transform raw text into structured conceptual clues**

- **Input**: Raw text from `data/news.json`
- **Output**: Structured clues in `data/clue/`
- **Purpose**: Extract key information and generate detailed conceptual clues
- **Process**:
  - Analyze raw text for key entities, relationships, and events
  - Generate rich contextual information for scene creation
  - Create thematic foundations for multi-agent scenarios

### Stage 2: Scene Generation 🏗️
**Create detailed 3D interactive environments**

- **Input**: Generated clues from Stage 1
- **Output**: Structured scenes in `data/scene/`
- **Purpose**: Create interactive environments with objects, states, and abilities
- **Enhanced Features**:
  - **Guaranteed Core Actions**: Every scene includes 'open' and 'close' actions
  - **Rich Action Schemas**: Detailed action information from CSV database
  - **Format**: `- repair: is_broken=false, requires_tool=true, Fixes a broken object`
  - **Comprehensive Validation**: Automatic scene validation and repair
  - **High Density**: Scenes with 20+ objects for complex interactions

### Stage 3: Task Generation 📋
**Generate collaborative tasks with embedded verification**

- **Input**: Generated scenes from Stage 2
- **Output**: Task definitions with embedded verification in `data/task/`
- **Purpose**: Generate specific tasks with validation criteria based on scene capabilities
- **Advanced Features**:
  - **14 Tasks per Scene**: 7 categories × 2 tasks each
  - **English Descriptions**: Professional English with thematic coherence
  - **Embedded Validation**: Built-in verification criteria for each task
  - **Rich Context**: Task background stories for narrative coherence
  - **Detailed Action Schemas**: Complete action information in prompts
  - **Multi-Agent Focus**: Tasks requiring collaboration between agents

### Stage 4: Validation & Repair ✅
**Automatic quality assurance and intelligent repair**

- **Input**: Generated task data from Stage 3
- **Output**: Validated and repaired task files + detailed fix logs
- **Purpose**: Ensure data quality through automatic validation and repair
- **Intelligent Features**:
  - **3-Step Validation**: Category → Object ID → Attributes
  - **Smart Repair**: Attribute name/value correction using CSV database
  - **Value Inversion**: Automatic target state calculation
  - **Invalid Task Removal**: Clean removal of unfixable tasks
  - **Comprehensive Logging**: Detailed fix logs with timestamps
  - **Transparency**: Complete audit trail of all changes



## 📊 Data Formats & Output Examples

### Input Data Format

#### Raw Text Input (`data/news.json`)
```json
[
  {
    "id": 1,
    "raw_text": "A bustling restaurant kitchen during dinner rush with multiple chefs coordinating complex orders, managing hot surfaces, sharp tools, and time-sensitive preparations."
  },
  {
    "id": 2,
    "raw_text": "A high-tech laboratory where researchers collaborate on sensitive experiments requiring precise measurements, sterile conditions, and careful handling of hazardous materials."
  }
]
```

### Output Data Formats

#### 1. Clue Output (`data/clue/00001_clue.json`)
```json
{
  "id": 1,
  "clue_data": {
    "key_information": "Professional restaurant kitchen environment with multiple cooking stations, commercial equipment, and collaborative workflow requirements.",
    "context": "High-pressure dinner service requiring coordination between multiple chefs, precise timing, and safety protocols for hot surfaces and sharp tools.",
    "details": {
      "entities": ["head_chef", "sous_chef", "line_cooks", "commercial_stove", "prep_station", "walk_in_cooler"],
      "relationships": [
        {"subject": "head_chef", "relation": "coordinates", "object": "kitchen_staff"},
        {"subject": "line_cooks", "relation": "operate", "object": "cooking_stations"}
      ],
      "events": [
        {
          "event_name": "dinner_rush_coordination",
          "participants": ["head_chef", "sous_chef", "line_cooks"],
          "time": "peak_service_hours"
        }
      ]
    }
  },
  "token_usage": 245,
  "timestamp": "2025-06-27T12:00:00Z"
}
```

#### 2. Scene Output (`data/scene/00001_scene.json`)
```json
{
  "scene_id": 1,
  "scene_data": {
    "description": "A professional restaurant kitchen with multiple cooking stations, commercial equipment, and storage areas designed for high-volume food preparation.",
    "rooms": [
      {
        "id": "main_kitchen",
        "name": "Main Kitchen",
        "properties": {
          "type": "kitchen",
          "size": [12.0, 8.0, 3.5],
          "temperature": 28.5
        },
        "connected_to_room_ids": ["prep_area", "walk_in_cooler"]
      }
    ],
    "objects": [
      {
        "id": "commercial_stove_1",
        "name": "Commercial Gas Stove",
        "type": "FURNITURE",
        "location_id": "in:main_kitchen",
        "properties": {
          "size": [1.8, 0.9, 0.95],
          "weight": 180.0,
          "material": "stainless_steel",
          "provides_abilities": ["heat", "cook"]
        },
        "states": {
          "is_on": false,
          "is_hot": false,
          "is_clean": true
        }
      },
      {
        "id": "chef_knife_1",
        "name": "Professional Chef Knife",
        "type": "ITEM",
        "location_id": "on:prep_station_1",
        "properties": {
          "weight": 0.3,
          "material": "carbon_steel",
          "provides_abilities": ["cut", "chop", "slice"]
        },
        "states": {
          "is_sharp": true,
          "is_clean": true
        }
      }
    ],
    "abilities": ["open", "close", "heat", "cook", "cut", "chop", "slice", "clean", "store"]
  },
  "token_usage": 892,
  "timestamp": "2025-06-27T12:05:00Z"
}
```

#### 3. Task Output (`data/task/00001_task.json`)
```json
{
  "scene_id": "00001",
  "task_background": "Prepare the professional restaurant kitchen for the evening dinner rush. The kitchen staff must coordinate to set up cooking stations, organize ingredients, and ensure all equipment is properly configured for high-volume food preparation while maintaining safety and hygiene standards.",
  "agents_config": [
    {
      "name": "robot_1",
      "max_grasp_limit": 1,
      "max_weight": 40.0,
      "max_size": [1.5, 1.5, 1.5]
    },
    {
      "name": "robot_2",
      "max_grasp_limit": 1,
      "max_weight": 40.0,
      "max_size": [1.5, 1.5, 1.5]
    }
  ],
  "tasks": [
    {
      "task_description": "Place the chef_knife_1 on the prep_station_1 for vegetable preparation.",
      "task_category": "direct_command",
      "validation_checks": [
        {
          "id": "chef_knife_1",
          "location_id": "on:prep_station_1"
        }
      ]
    },
    {
      "task_description": "Turn on the commercial stove that will be used for the soup preparation.",
      "task_category": "attribute_reasoning",
      "validation_checks": [
        {
          "id": "commercial_stove_1",
          "is_on": true
        }
      ]
    },
    {
      "task_description": "Open the walk-in cooler to access fresh ingredients for tonight's menu.",
      "task_category": "tool_use",
      "validation_checks": [
        {
          "id": "walk_in_cooler_1",
          "is_open": true
        }
      ]
    }
  ]
}
```

#### 4. Validation Log (`logs/00001_task_fixes_20250627_183412.log`)
```
=== Task Validation Report ===
File: data/task/00001_task.json
Timestamp: 2025-06-27 18:34:12

=== Validation Errors ===
1. Task 9: No scene abilities matched task description

=== Fixes Applied ===
1. Task 4: Fixed attribute 'is_heated' → 'is_on'
2. Task 4: Fixed value 'false' → 'true' (inverted)
3. Task 7: Fixed attribute 'is_opened' → 'is_open'
4. Removed Task 9: No scene abilities matched task description

=== Summary ===
Total tasks before: 14
Total tasks after: 13
Fixes applied: 4
Tasks removed: 1
```



## ⚙️ Configuration & Customization

### 🏗️ Configuration Architecture

The system uses a **layered configuration approach** supporting two distinct usage modes:

#### 📋 Pipeline Mode vs Standalone Mode

**Pipeline Mode** (End-to-End Processing):
- Uses `config/pipeline.yaml` for overall execution control
- Processes items sequentially: Raw Text → Clue → Scene → Task → Validation
- Individual generator `thread_num` settings are **ignored**
- Recommended for production data generation

**Standalone Mode** (Independent Batch Generation):
- Each generator uses its own config file for batch processing
- Can run generators independently with their specific `thread_num` settings
- Useful for processing large batches of a single generation type
- Ideal for development and testing

### 🔧 Pipeline Configuration (`config/pipeline.yaml`)

Controls the main end-to-end pipeline execution:

```yaml
# ============================================================================
# Threading Configuration
# ============================================================================
thread_num: 4              # Number of parallel data items through entire pipeline

# ============================================================================
# ID Range Configuration (can be overridden by command-line arguments)
# ============================================================================
start_id: 0                # Starting ID (inclusive)
end_id: 4                  # Ending ID (inclusive, null = process all)

# ============================================================================
# Generation Control
# ============================================================================
continue_generation: true  # Continue from last interruption point (skip completed items)

# ============================================================================
# Output Configuration
# ============================================================================
output_dir: "./data"       # Base output directory for all generated data
summary_file: "summary.json"  # Pipeline execution summary file

# ============================================================================
# Logging Configuration
# ============================================================================
log_dir: "./logs"          # Log directory for pipeline execution logs
```

### 🎯 Generator-Specific Configurations

Each generator has its own comprehensive configuration file:

| Config File | Pipeline Mode | Standalone Mode | `thread_num` Used? |
|-------------|---------------|-----------------|-------------------|
| `clue_gen_config.yaml` | Single calls | Batch generation | ❌ / ✅ |
| `scene_gen_config.yaml` | Single calls | Batch generation | ❌ / ✅ |
| `task_gen_config.yaml` | Single calls | Batch generation | ❌ / ✅ |

#### Complete Generator Configuration Example:

```yaml
# ============================================================================
# API Configuration
# ============================================================================
api: openai                # API type: openai
endpoint: https://api.deepseek.com  # API endpoint URL
model: deepseek-chat       # Model name
api_key: "sk-your-api-key-here"    # Your API key

# ============================================================================
# Generation Parameters
# ============================================================================
temperature: 1.3           # LLM temperature (0.0-2.0, higher = more creative)
max_tokens: 2048          # Maximum tokens per generation
timeout: 600              # API call timeout in seconds

# ============================================================================
# Threading Configuration (ONLY used in standalone mode)
# ============================================================================
thread_num: 5             # Parallel threads for standalone batch generation
# ⚠️  IGNORED in pipeline mode - pipeline uses its own threading!

# ============================================================================
# Retry Configuration
# ============================================================================
max_retries: 3            # Maximum retry attempts for failed generations
retry_delay: 2            # Base retry delay in seconds (exponential backoff)

# ============================================================================
# Prompts (customizable for different domains)
# ============================================================================
system_prompt: |
  You are a highly experienced Scene Concept Designer...
  [Full prompt content here]

user_prompt: |
  Based on the provided inputs, generate...
  [Full prompt content here]
```

### 🚀 Configuration Usage Examples

#### Pipeline Mode:
```bash
# Uses pipeline.yaml thread_num setting (ignores generator thread_num)
python pipeline.py --threads 4
```

#### Standalone Mode:
```bash
# Each uses its own thread_num setting from respective config files
python -m generators.clue_generator     # Uses clue_gen_config.yaml thread_num: 5
python -m generators.scene_generator    # Uses scene_gen_config.yaml thread_num: 10
python -m generators.task_generator     # Uses task_gen_config.yaml thread_num: 20
```

### ⚙️ Performance Tuning Guidelines

| Component | Recommended `thread_num` | Memory Usage | API Calls/Min | Reason |
|-----------|-------------------------|--------------|---------------|---------|
| **Clue Generator** | 5 | Low | 150-300 | Creative generation, moderate complexity |
| **Scene Generator** | 10 | High | 300-600 | Structured generation, high memory usage |
| **Task Generator** | 20 | Medium | 600-1200 | Fast structured output with validation |
| **Pipeline** | 4 | Medium | 200-400 | Overall coordination, balanced resource usage |

### 🎨 Customization Options

#### 1. Custom Prompts

Edit the `system_prompt` and `user_prompt` sections in configuration files:

```yaml
system_prompt: |
  You are a specialized [DOMAIN] expert...
  Focus on [SPECIFIC_REQUIREMENTS]...

user_prompt: |
  Generate [SPECIFIC_OUTPUT] based on:
  Input: {input_variable}
  Requirements: [CUSTOM_REQUIREMENTS]
```

#### 2. Custom Action Database

Modify `data/attribute_actions.csv` to add domain-specific actions:

```csv
action_name,attribute,value,requires_tool,description
custom_action,custom_attribute,target_value,true,"Custom action description"
domain_specific,domain_attr,expected_val,false,"Domain-specific action"
```

#### 3. Custom Task Categories

Add new task categories by modifying the validation system:

```python
# In utils/task_validator.py
VALID_TASK_CATEGORIES = [
    "direct_command",
    "attribute_reasoning",
    "tool_use",
    "compound_reasoning",
    "explicit_collaboration",
    "implicit_collaboration",
    "compound_collaboration",
    "custom_category"  # Add your custom category
]
```

#### 4. Custom Input Data Format

Extend the input data structure in `data/news.json`:

```json
[
  {
    "id": 1,
    "raw_text": "Your scenario description",
    "domain": "healthcare",           // Custom field
    "complexity": "high",             // Custom field
    "required_agents": 3,             // Custom field
    "custom_metadata": {              // Custom nested data
      "priority": "urgent",
      "tags": ["collaborative", "precision"]
    }
  }
]
```

## �️ Task Validation System

### Overview

The Task Validation System is a sophisticated quality assurance component that automatically validates and repairs generated task data. It operates as Stage 4 of the pipeline, ensuring high-quality output through intelligent analysis and repair.

### 🔍 Three-Step Validation Process

#### Step 1: Task Category Validation
**Ensures task categories are valid and properly formatted**

- **Valid Categories**:
  - `direct_command` - Direct object manipulation tasks
  - `attribute_reasoning` - Tasks requiring attribute-based selection
  - `tool_use` - Tasks requiring specific tools
  - `compound_reasoning` - Complex reasoning combining multiple factors
  - `explicit_collaboration` - Tasks explicitly requiring multiple agents
  - `implicit_collaboration` - Tasks implicitly requiring collaboration
  - `compound_collaboration` - Complex collaborative tasks
- **Action**: Delete tasks with invalid categories

#### Step 2: Object ID Existence Validation
**Verifies all referenced objects exist in the scene**

- **Process**: Cross-reference task object IDs with scene objects and rooms
- **Validation**: Ensure every `id` in `validation_checks` exists in scene data
- **Action**: Delete tasks referencing non-existent objects

#### Step 3: Attribute Validation & Repair
**Validates and intelligently fixes attribute names and values**

- **Location ID Validation**: Verify `in:`/`on:` relationship consistency
- **Attribute Matching**: Match task descriptions against scene abilities
- **CSV Database Lookup**: Find correct attribute names and values
- **Value Inversion**: Apply target state logic (e.g., `false` → `true`)
- **Action**: Fix attributes or delete unfixable tasks

### 🔧 Intelligent Repair Mechanisms

#### Attribute Name Correction
```json
// Before repair
{"id": "printer_1", "is_broken": false}

// After repair
{"id": "printer_1", "is_screwed_in": true}
```

#### Value Inversion Logic
```json
// CSV defines: repair,is_broken,false,true,"Fixes broken objects"
// Task: "Repair the broken printer"
// Result: is_broken=false (inverted from CSV value)
```

#### Compound Action Handling
```json
// Handles complex actions like "turn_on", "take_down", "screw_in"
// Splits by underscore and matches all parts in task description
```

### 📊 Validation Logging

#### Console Output
```
[T1] Item 5: Validating and fixing task...
[T1] Item 5: Found 1 validation issues
[T1] Item 5:   1. Task 9: No scene abilities matched task description
[T1] Item 5: Applied 4 fixes:
[T1] Item 5:   1. Task 4: Fixed attribute 'is_soldered' → 'is_ironed'
[T1] Item 5:   2. Task 4: Fixed value 'false' → 'true' (inverted)
[T1] Item 5:   3. Task 7: Fixed attribute 'is_peeled' → 'is_mended'
[T1] Item 5:   4. Removed Task 9: No scene abilities matched task description
```

#### Detailed Fix Logs
- **Filename**: `{task_id}_task_fixes_{timestamp}.log`
- **Location**: `logs/` directory
- **Content**: Complete validation report with before/after comparison

### 🎯 Validation Benefits

- **Quality Assurance**: Automatic detection and repair of data quality issues
- **Consistency**: Ensures all tasks follow the same validation rules
- **Transparency**: Complete audit trail of all changes
- **Efficiency**: No manual intervention required
- **Reliability**: Graceful handling of edge cases and errors

## 📈 Performance Monitoring

The pipeline provides comprehensive performance tracking and monitoring:

### Real-Time Progress Display
```
┌──────────────────────────────────────────────────┐
│                   📊 Progress                    │
├──────────────────────────────────────────────────┤
│ Done: 45/100 | Skip: 12 | Fail: 2 | Work: 4     │
├──────────────────────────────────────────────────┤
│ T1: Item 67: Generating scene                    │
│ T2: Item 68: Validating task                     │
│ T3: Item 69: Generating clue                     │
│ T4: Item 70: Generating task                     │
└──────────────────────────────────────────────────┘
```

### Performance Metrics
- **Throughput**: Items processed per minute
- **Token Usage**: Detailed API consumption per stage
- **Success Rate**: Completion vs failure statistics
- **Validation Stats**: Fixes applied and tasks removed
- **Execution Time**: Average time per stage and overall

### Execution Summary
```json
{
  "total_items": 100,
  "completed": 95,
  "failed": 3,
  "skipped": 2,
  "total_time": "2h 15m 30s",
  "token_usage": {
    "clue_generation": 45000,
    "scene_generation": 120000,
    "task_generation": 85000,
    "total": 250000
  },
  "validation_stats": {
    "tasks_validated": 95,
    "fixes_applied": 234,
    "tasks_removed": 12,
    "fix_rate": "92.3%"
  }
}
```

## 🔍 Comprehensive Logging System

### Log Directory Structure
```
logs/
├── pipeline.log                    # Main pipeline execution logs
├── clue_raw.log                   # Raw LLM responses for clue generation
├── scene_raw.log                  # Raw LLM responses for scene generation
├── task_raw.log                   # Raw LLM responses for task generation
└── *_task_fixes_*.log            # Task validation and repair logs
```

### Log Types & Contents

#### 1. Pipeline Logs (`pipeline.log`)
- **Content**: Main execution flow, progress tracking, error handling
- **Format**: Timestamped entries with thread IDs and item IDs
- **Includes**: Validation results, fix summaries, performance metrics

#### 2. Raw Response Logs (`*_raw.log`)
- **Content**: Complete LLM API responses for debugging
- **Format**: JSON responses with metadata
- **Purpose**: Troubleshooting generation issues and prompt optimization

#### 3. Validation Fix Logs (`*_task_fixes_*.log`)
- **Content**: Detailed validation reports and repair operations
- **Format**: Structured reports with before/after comparisons
- **Naming**: `{task_id}_task_fixes_{timestamp}.log`

### Log Level Configuration

```bash
# Set log level via command line
python pipeline.py --log-level DEBUG    # Maximum detail
python pipeline.py --log-level INFO     # Standard operation (default)
python pipeline.py --log-level WARNING  # Warnings and errors only
python pipeline.py --log-level ERROR    # Errors only
```

## 🛠️ Development & Extension

### Adding Custom Generators

1. **Create Generator Class**
   ```python
   from generators.base_generator import BaseGenerator

   class CustomGenerator(BaseGenerator):
       def __init__(self, config_override=None):
           super().__init__('custom', config_override)

       def generate_single(self, input_item, thread_id=0):
           # Implement your generation logic
           pass

       def validate_result(self, result):
           # Implement result validation
           pass
   ```

2. **Add Configuration File**
   ```yaml
   # config/custom_gen_config.yaml
   api: openai
   endpoint: https://api.deepseek.com
   model: deepseek-chat
   api_key: "your-api-key"
   temperature: 0.7
   max_tokens: 2048
   thread_num: 5
   ```

3. **Register in Pipeline** (if needed)
   ```python
   # In pipeline.py
   from generators.custom_generator import CustomGenerator

   # Add to pipeline stages
   custom_generator = CustomGenerator()
   ```

### Adding Custom Validation Rules

1. **Extend TaskValidator**
   ```python
   # In utils/task_validator.py
   def _validate_custom_rules(self, task_data, scene_data):
       errors = []
       # Add your custom validation logic
       return errors
   ```

2. **Add Custom Repair Logic**
   ```python
   def _apply_custom_fixes(self, task_data, scene_data):
       fixes = []
       # Add your custom repair logic
       return fixes
   ```

### Custom Action Database

Extend `data/attribute_actions.csv` with domain-specific actions:

```csv
action_name,attribute,value,requires_tool,description
medical_scan,is_scanned,true,true,"Performs medical scanning procedure"
sterilize,is_sterile,true,true,"Sterilizes medical equipment"
calibrate,is_calibrated,true,false,"Calibrates precision instruments"
```

### Error Handling Best Practices

The system includes comprehensive error handling:

- **Automatic Retries**: Exponential backoff for API failures
- **Thread Safety**: All logging and state management is thread-safe
- **Graceful Degradation**: Individual failures don't stop the pipeline
- **Resume Capability**: Skip completed items on restart
- **Detailed Error Reporting**: Complete stack traces and context

### Testing & Validation

```bash
# Test individual components
python -c "from generators.clue_generator import ClueGenerator; cg = ClueGenerator(); print('Clue generator OK')"

# Test with small dataset
python pipeline.py --start-id 1 --end-id 3 --threads 1 --log-level DEBUG

# Validate configuration
python -c "from utils.config_loader import config_loader; print('Config OK')"
```

## 🚀 Production Deployment

### Recommended Production Settings

```yaml
# config/pipeline.yaml (Production)
thread_num: 8                    # Adjust based on server capacity
continue_generation: true        # Enable resume capability
max_retries: 5                  # Increase for production reliability

# Generator configs (Production)
temperature: 0.7                # Balanced creativity/consistency
max_tokens: 4096               # Sufficient for complex outputs
timeout: 900                   # Longer timeout for stability
```

### Monitoring & Maintenance

1. **Monitor Log Files**: Set up log rotation and monitoring
2. **Track Token Usage**: Monitor API costs and usage patterns
3. **Performance Metrics**: Track throughput and success rates
4. **Validation Stats**: Monitor fix rates and data quality

### Scaling Considerations

- **Horizontal Scaling**: Run multiple pipeline instances with different ID ranges
- **API Rate Limits**: Adjust thread counts based on API provider limits
- **Memory Management**: Monitor memory usage with high thread counts
- **Storage**: Ensure sufficient disk space for logs and generated data

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the existing code style
4. Add tests for new functionality
5. Update documentation as needed
6. Submit a pull request

### Code Standards
- Follow existing architecture patterns
- Use type hints where appropriate
- Add comprehensive logging
- Include error handling
- Write clear docstrings
- Follow the existing naming conventions

### Testing Requirements
- Test new generators with sample data
- Verify configuration changes work correctly
- Ensure thread safety for concurrent operations
- Test error handling and recovery scenarios

## 📞 Support

For questions, issues, or contributions:
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check this README for comprehensive guidance
- **Logs**: Check the `logs/` directory for debugging information
- **Configuration**: Verify your `config/` files are properly set up

---

**Happy Data Generation! 🎉**