#!/usr/bin/env python3
"""
运行 results_analysis.ipynb 中的分析代码
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for beautiful visualizations with light color scheme
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#E5E5E5'
plt.rcParams['grid.linewidth'] = 0.5
plt.rcParams['text.color'] = '#333333'
plt.rcParams['axes.labelcolor'] = '#333333'
plt.rcParams['xtick.color'] = '#666666'
plt.rcParams['ytick.color'] = '#666666'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Define beautiful light color palettes
LIGHT_COLORS = {
    'primary': ['#E8F4FD', '#B3E0FF', '#7CC7FF', '#4DAAFF', '#1A8CFF', '#0066CC'],
    'success': ['#E8F5E8', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A', '#4CAF50'],
    'warning': ['#FFF8E1', '#FFECB3', '#FFE082', '#FFD54F', '#FFCA28', '#FFC107'],
    'error': ['#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#EF5350', '#F44336'],
    'info': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3'],
    'purple': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#BA68C8', '#AB47BC', '#9C27B0'],
    'teal': ['#E0F2F1', '#B2DFDB', '#80CBC4', '#4DB6AC', '#26A69A', '#009688'],
    'orange': ['#FFF3E0', '#FFE0B2', '#FFCC80', '#FFB74D', '#FFA726', '#FF9800']
}

# Set seaborn style with light theme
sns.set_style("whitegrid", {
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "grid.linewidth": 0.5,
    "grid.color": "#E5E5E5"
})

# Configure display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

print("✅ Libraries imported successfully!")
print("🎨 Beautiful light color scheme configured!")

def find_latest_log_file(output_dir='../output', custom_csv_path=None):
    """
    Find the latest subtask_execution_log.csv file or use custom path
    """
    # Check custom CSV path first (highest priority)
    if custom_csv_path:
        if os.path.exists(custom_csv_path):
            if custom_csv_path.endswith('.csv'):
                print(f"📁 Using custom CSV path: {custom_csv_path}")
                return custom_csv_path
            else:
                print(f"⚠️  Warning: Custom path '{custom_csv_path}' is not a CSV file, but proceeding...")
                return custom_csv_path
        else:
            print(f"❌ Custom CSV path does not exist: {custom_csv_path}")
            print(f"🔍 Falling back to auto-detection...")
    
    # Auto-detection: Find all subtask_execution_log.csv files
    pattern = os.path.join(output_dir, '**/subtask_execution_log.csv')
    log_files = glob.glob(pattern, recursive=True)
    
    if not log_files:
        raise FileNotFoundError(f"❌ No subtask_execution_log.csv files found in {output_dir}")
    
    # Sort by modification time and get the latest
    latest_file = max(log_files, key=os.path.getmtime)
    print(f"📁 Using latest log file: {latest_file}")
    return latest_file

def validate_data_for_plotting(df):
    """
    Validate data and report potential issues that could cause empty plots
    """
    print("\n🔍 DATA VALIDATION FOR PLOTTING")
    print("-" * 40)
    
    # Check for required columns
    required_cols = ['task_category', 'subtask_completed', 'total_steps', 'duration_seconds', 'command_success_rate_numeric']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"⚠️ Missing columns: {missing_cols}")
    
    # Check data distribution
    print(f"📊 Data shape: {df.shape}")
    print(f"📋 Task categories: {list(df['task_category'].unique())}")
    print(f"✅ Completed tasks: {df['subtask_completed'].sum()}/{len(df)} ({df['subtask_completed'].mean()*100:.1f}%)")
    
    # Check for empty categories
    category_counts = df['task_category'].value_counts()
    print(f"📈 Tasks per category:")
    for cat, count in category_counts.items():
        success_rate = df[df['task_category']==cat]['subtask_completed'].mean() * 100
        print(f"  - {cat}: {count} tasks ({success_rate:.1f}% success)")
    
    # Check for NaN values
    nan_cols = df.isnull().sum()
    nan_cols = nan_cols[nan_cols > 0]
    if len(nan_cols) > 0:
        print(f"⚠️ Columns with NaN values: {dict(nan_cols)}")
    
    return True

def load_and_preprocess_data(file_path):
    """
    Load and preprocess the subtask execution log data
    """
    # Load data
    df = pd.read_csv(file_path)
    
    # Convert timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    
    # Convert boolean columns
    df['task_executed'] = df['task_executed'].astype(bool)
    df['subtask_completed'] = df['subtask_completed'].astype(bool)
    
    # Convert command_success_rate from percentage string to float
    df['command_success_rate'] = df['command_success_rate'].astype(str)
    df['command_success_rate_numeric'] = df['command_success_rate'].str.rstrip('%').astype(float)
    
    # Extract scenario number from scenario_id
    df['scenario_id'] = df['scenario_id'].astype(str)
    scenario_numbers = df['scenario_id'].str.extract(r'(\d+)')
    df['scenario_number'] = pd.to_numeric(scenario_numbers[0], errors='coerce').fillna(0).astype(int)
    
    # Add derived columns
    df['failure_rate'] = 100 - df['command_success_rate_numeric']
    df['steps_per_second'] = df['total_steps'] / df['duration_seconds']
    df['efficiency_score'] = (df['command_success_rate_numeric'] * df['subtask_completed'].astype(int)) / (df['total_steps'] + 1)
    
    print(f"📊 Loaded {len(df)} records from {file_path}")
    print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"📋 Task categories: {', '.join(df['task_category'].unique())}")
    print(f"🤖 Agent types: {', '.join(df['agent_type'].unique())}")
    
    return df

def analyze_overall_performance(df):
    """
    Create comprehensive overall performance analysis with beautiful visualizations
    """
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('📊 Overall Performance Analysis Dashboard', fontsize=20, fontweight='bold', y=0.98)

    # 1. Completion Rate Pie Chart
    ax1 = axes[0, 0]
    completion_counts = df['subtask_completed'].value_counts()

    # Create labels and values based on what exists in the data
    values = []
    labels = []
    colors = []

    # Add failed tasks if they exist
    if False in completion_counts.index:
        values.append(completion_counts[False])
        labels.append('Failed')
        colors.append(LIGHT_COLORS['error'][2])

    # Add completed tasks if they exist
    if True in completion_counts.index:
        values.append(completion_counts[True])
        labels.append('Completed')
        colors.append(LIGHT_COLORS['success'][2])

    wedges, texts, autotexts = ax1.pie(values, labels=labels,
                                      autopct='%1.1f%%', colors=colors, startangle=90,
                                      wedgeprops=dict(edgecolor='white', linewidth=3))
    ax1.set_title('🎯 Task Success Rate\n(Most Important Metric)', fontweight='bold', pad=20, fontsize=14)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)

    # 2. Command Success Rate Distribution
    ax2 = axes[0, 1]
    ax2.hist(df['command_success_rate_numeric'], bins=20, color=LIGHT_COLORS['info'][3],
             alpha=0.8, edgecolor='white', linewidth=1.5)
    ax2.set_title('📈 Command Success Rate Distribution', fontweight='bold', pad=20, fontsize=14)
    ax2.set_xlabel('Command Success Rate (%)', fontweight='bold')
    ax2.set_ylabel('Number of Tasks', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.axvline(df['command_success_rate_numeric'].mean(), color=LIGHT_COLORS['warning'][4],
                linestyle='--', linewidth=2, label=f'Mean: {df["command_success_rate_numeric"].mean():.1f}%')
    ax2.legend()

    # 3. Steps vs Duration Scatter Plot
    ax3 = axes[1, 0]
    completed_mask = df['subtask_completed']
    ax3.scatter(df[completed_mask]['total_steps'], df[completed_mask]['duration_seconds'],
               color=LIGHT_COLORS['success'][3], alpha=0.7, s=60, label='Completed', edgecolors='white')
    ax3.scatter(df[~completed_mask]['total_steps'], df[~completed_mask]['duration_seconds'],
               color=LIGHT_COLORS['error'][3], alpha=0.7, s=60, label='Failed', edgecolors='white')
    ax3.set_title('⏱️ Steps vs Duration Analysis', fontweight='bold', pad=20, fontsize=14)
    ax3.set_xlabel('Total Steps', fontweight='bold')
    ax3.set_ylabel('Duration (seconds)', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Key Metrics Summary
    ax4 = axes[1, 1]
    ax4.axis('off')

    # Calculate key metrics
    total_tasks = len(df)
    completed_tasks = df['subtask_completed'].sum()
    success_rate = (completed_tasks / total_tasks) * 100
    avg_steps = df['total_steps'].mean()
    avg_duration = df['duration_seconds'].mean()
    avg_command_success = df['command_success_rate_numeric'].mean()
    avg_llm_interactions = df['llm_interactions'].mean()

    # Create metrics text
    metrics_text = f"""
🎯 KEY PERFORMANCE METRICS

✅ Task Success Rate: {success_rate:.1f}%
📊 Total Tasks: {total_tasks}
🏆 Completed Tasks: {completed_tasks}
❌ Failed Tasks: {total_tasks - completed_tasks}

📈 Average Command Success: {avg_command_success:.1f}%
👣 Average Steps: {avg_steps:.1f}
⏱️ Average Duration: {avg_duration:.1f}s
🤖 Average LLM Interactions: {avg_llm_interactions:.1f}

🔥 Efficiency Score: {df['efficiency_score'].mean():.3f}
"""

    ax4.text(0.1, 0.9, metrics_text, transform=ax4.transAxes, fontsize=12,
             verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5",
             facecolor=LIGHT_COLORS['info'][0], edgecolor=LIGHT_COLORS['info'][2], linewidth=2))

    plt.tight_layout()
    return fig

def analyze_task_categories(df):
    """
    Analyze performance by task category
    """
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('📋 Task Category Performance Analysis', fontsize=20, fontweight='bold', y=0.98)

    # 1. Success Rate by Category
    ax1 = axes[0, 0]
    category_success = df.groupby('task_category')['subtask_completed'].agg(['mean', 'count']).reset_index()
    category_success['success_rate'] = category_success['mean'] * 100

    bars = ax1.bar(category_success['task_category'], category_success['success_rate'],
                   color=[LIGHT_COLORS['primary'][i % len(LIGHT_COLORS['primary'])] for i in range(len(category_success))],
                   edgecolor='white', linewidth=2)
    ax1.set_title('🎯 Success Rate by Task Category', fontweight='bold', pad=20, fontsize=14)
    ax1.set_ylabel('Success Rate (%)', fontweight='bold')
    ax1.set_xlabel('Task Category', fontweight='bold')
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar, value in zip(bars, category_success['success_rate']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')

    return fig

def main():
    """
    Main function to run the complete analysis
    """
    print("🚀 Starting Results Analysis...")
    print("=" * 50)

    # Find and load data
    try:
        # Use the latest CSV file
        custom_csv_path = "../output/20250706_164540_single_parallel_independent_scenario_multi_demo/subtask_execution_log.csv"
        csv_file = find_latest_log_file(custom_csv_path=custom_csv_path)
        df = load_and_preprocess_data(csv_file)

        # Validate data
        validate_data_for_plotting(df)

        print("\n📊 GENERATING ANALYSIS PLOTS...")
        print("-" * 40)

        # Generate overall performance analysis
        print("1️⃣ Creating overall performance analysis...")
        overall_fig = analyze_overall_performance(df)
        overall_fig.savefig('overall_performance_analysis.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: overall_performance_analysis.png")

        # Generate task category analysis
        print("2️⃣ Creating task category analysis...")
        category_fig = analyze_task_categories(df)
        category_fig.savefig('task_category_analysis.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: task_category_analysis.png")

        # Display summary statistics
        print("\n📈 SUMMARY STATISTICS")
        print("-" * 40)
        print(f"📊 Total Tasks: {len(df)}")
        print(f"✅ Completed Tasks: {df['subtask_completed'].sum()}")
        print(f"❌ Failed Tasks: {len(df) - df['subtask_completed'].sum()}")
        print(f"🎯 Success Rate: {df['subtask_completed'].mean() * 100:.1f}%")
        print(f"📈 Avg Command Success: {df['command_success_rate_numeric'].mean():.1f}%")
        print(f"👣 Avg Steps: {df['total_steps'].mean():.1f}")
        print(f"⏱️ Avg Duration: {df['duration_seconds'].mean():.1f}s")
        print(f"🤖 Avg LLM Interactions: {df['llm_interactions'].mean():.1f}")

        # Task category breakdown
        print(f"\n📋 TASK CATEGORY BREAKDOWN")
        print("-" * 40)
        category_stats = df.groupby('task_category').agg({
            'subtask_completed': ['count', 'sum', 'mean'],
            'total_steps': 'mean',
            'duration_seconds': 'mean'
        }).round(2)

        for category in df['task_category'].unique():
            cat_data = df[df['task_category'] == category]
            total = len(cat_data)
            completed = cat_data['subtask_completed'].sum()
            success_rate = (completed / total) * 100
            avg_steps = cat_data['total_steps'].mean()
            avg_duration = cat_data['duration_seconds'].mean()

            print(f"📌 {category}:")
            print(f"   Tasks: {total} | Completed: {completed} | Success: {success_rate:.1f}%")
            print(f"   Avg Steps: {avg_steps:.1f} | Avg Duration: {avg_duration:.1f}s")

        print(f"\n🎉 Analysis completed successfully!")
        print(f"📁 Generated files:")
        print(f"   - overall_performance_analysis.png")
        print(f"   - task_category_analysis.png")

    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
