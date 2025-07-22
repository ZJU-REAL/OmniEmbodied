import sys
import pandas as pd

def main():
    # 从标准输入读取文件路径
    file_path = input().strip().strip("'")
    df = pd.read_csv(file_path)

    # 检查所需列是否存在
    required_columns = {'task_category', 'subtask_completed', 'llm_interactions'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        print(f"错误: 缺少以下必要列: {', '.join(missing)}")
        return

    # 统计每个类别下的完成率、完成情况下的平均交互次数、所有情况下的平均交互次数
    result = {}
    categories = df['task_category'].unique()
    for cat in categories:
        cat_df = df[df['task_category'] == cat]
        total = len(cat_df)
        completed_df = cat_df[cat_df['subtask_completed'] == True]
        completed = len(completed_df)
        completion_rate = completed / total if total > 0 else 0
        avg_interaction_completed = completed_df['llm_interactions'].mean() if completed > 0 else 0
        avg_interaction_all = cat_df['llm_interactions'].mean() if total > 0 else 0
        result[cat] = {
            'completion_rate': completion_rate,
            'avg_interaction_completed': avg_interaction_completed,
            'avg_interaction_all': avg_interaction_all
        }

    # 整体统计
    total = len(df)
    completed_df = df[df['subtask_completed'] == True]
    completed = len(completed_df)
    completion_rate = completed / total if total > 0 else 0
    avg_interaction_completed = completed_df['llm_interactions'].mean() if completed > 0 else 0
    avg_interaction_all = df['llm_interactions'].mean() if total > 0 else 0

    # 输出
    print('每个任务类别统计:')
    for cat, stats in result.items():
        print(f'类别: {cat}')
        print(f'  完成率: {stats["completion_rate"]:.2%}')
        print(f'  完成情况下平均交互次数: {stats["avg_interaction_completed"]:.2f}')
        print(f'  所有情况下平均交互次数: {stats["avg_interaction_all"]:.2f}')
    print('\n整体统计:')
    print(f'  完成率: {completion_rate:.2%}')
    print(f'  完成情况下平均交互次数: {avg_interaction_completed:.2f}')
    print(f'  所有情况下平均交互次数: {avg_interaction_all:.2f}')

if __name__ == '__main__':
    main()