const express = require('express');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const cors = require('cors');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// 数据路径配置
const DATA_PATHS = {
  single: {
    csv: '../raw_output/20250723_220044_single_independent_00001_to_00800_qianduoduo_4o_wo_single/subtask_execution_log.csv',
    trajectories: '../raw_output/20250723_220044_single_independent_00001_to_00800_qianduoduo_4o_wo_single/trajectories',
    scenes: '../data/eval/single-independent/scene',
    tasks: '../data/eval/single-independent/task'
  },
  multi: {
    csv: '../raw_output/20250723_225455_multi_independent_00001_to_00600_qianduoduo_4o_wo_multi/subtask_execution_log.csv',
    trajectories: '../raw_output/20250723_225455_multi_independent_00001_to_00600_qianduoduo_4o_wo_multi/trajectories',
    scenes: '../data/eval/multi-independent/scene',
    tasks: '../data/eval/multi-independent/task'
  }
};

const EVALUATION_CSV = 'evaluation_results.csv';

// 初始化评估结果CSV
function initEvaluationCSV() {
  if (!fs.existsSync(EVALUATION_CSV)) {
    const csvWriter = createCsvWriter({
      path: EVALUATION_CSV,
      header: [
        { id: 'dataset_type', title: 'dataset_type' },
        { id: 'scenario_id', title: 'scenario_id' },
        { id: 'task_index', title: 'task_index' },
        { id: 'task_category', title: 'task_category' },
        { id: 'task_description', title: 'task_description' },
        { id: 'evaluation_result', title: 'evaluation_result' },
        { id: 'timestamp', title: 'timestamp' },
        { id: 'notes', title: 'notes' }
      ]
    });
    csvWriter.writeRecords([]);
  }
}

// 读取失败任务
async function getFailedTasks() {
  const failedTasks = [];
  
  for (const [type, paths] of Object.entries(DATA_PATHS)) {
    const csvPath = path.resolve(__dirname, paths.csv);
    if (fs.existsSync(csvPath)) {
      await new Promise((resolve) => {
        fs.createReadStream(csvPath)
          .pipe(csv())
          .on('data', (row) => {
            if (row.status === 'failed') {
              failedTasks.push({
                type,
                scenario_id: row.scenario_id,
                task_index: row.task_index,
                task_description: row.task_description,
                task_category: row.task_category,
                ...row
              });
            }
          })
          .on('end', resolve);
      });
    }
  }
  
  return failedTasks;
}

// 读取评估结果
async function getEvaluationResults() {
  const results = {};
  if (fs.existsSync(EVALUATION_CSV)) {
    await new Promise((resolve) => {
      fs.createReadStream(EVALUATION_CSV)
        .pipe(csv())
        .on('data', (row) => {
          const key = `${row.dataset_type}-${row.scenario_id}-${row.task_index}`;
          results[key] = row.evaluation_result;
        })
        .on('end', resolve);
    });
  }
  return results;
}

// API: 获取失败任务列表
app.get('/api/failed-tasks', async (req, res) => {
  try {
    const failedTasks = await getFailedTasks();
    const evaluationResults = await getEvaluationResults();
    
    const tasksWithResults = failedTasks.map(task => {
      const key = `${task.type}-${task.scenario_id}-${task.task_index}`;
      return {
        ...task,
        previous_result: evaluationResults[key] || null
      };
    });
    
    res.json(tasksWithResults);
  } catch (error) {
    console.error('Error getting failed tasks:', error);
    res.status(500).json({ error: 'Failed to get tasks' });
  }
});

// API: 获取任务数据
app.get('/api/task-data/:type/:scenarioId/:taskIndex', (req, res) => {
  try {
    const { type, scenarioId, taskIndex } = req.params;
    const paths = DATA_PATHS[type];
    
    if (!paths) {
      return res.status(400).json({ error: 'Invalid dataset type' });
    }
    
    const data = {};
    
    // 读取轨迹文件 - 修正文件名格式
    // 轨迹文件名格式: {scenarioId}_task_00001_trajectory.json (任务索引始终为00001)
    const trajectoryPath = path.resolve(__dirname, paths.trajectories, `${scenarioId.padStart(5, '0')}_task_00001_trajectory.json`);
    if (fs.existsSync(trajectoryPath)) {
      data.trajectory = JSON.parse(fs.readFileSync(trajectoryPath, 'utf8'));
    }
    
    // 读取场景文件
    const scenePath = path.resolve(__dirname, paths.scenes, `${scenarioId.padStart(5, '0')}_scene.json`);
    if (fs.existsSync(scenePath)) {
      data.scene = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
    }

    // 读取任务文件
    const taskPath = path.resolve(__dirname, paths.tasks, `${scenarioId.padStart(5, '0')}_task.json`);
    if (fs.existsSync(taskPath)) {
      data.task = JSON.parse(fs.readFileSync(taskPath, 'utf8'));
    }
    
    res.json(data);
  } catch (error) {
    console.error('Error getting task data:', error);
    res.status(500).json({ error: 'Failed to get task data' });
  }
});

// API: 获取原始数据（用于重置）
app.get('/api/original-data/:type/:scenarioId/:taskIndex', (req, res) => {
  try {
    const { type, scenarioId, taskIndex } = req.params;
    const paths = DATA_PATHS[type];

    if (!paths) {
      return res.status(400).json({ error: 'Invalid dataset type' });
    }

    const data = {};

    // 读取场景文件
    const scenePath = path.resolve(__dirname, paths.scenes, `${scenarioId.padStart(5, '0')}_scene.json`);
    if (fs.existsSync(scenePath)) {
      data.scene = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
    }

    // 读取任务文件
    const taskPath = path.resolve(__dirname, paths.tasks, `${scenarioId.padStart(5, '0')}_task.json`);
    if (fs.existsSync(taskPath)) {
      data.task = JSON.parse(fs.readFileSync(taskPath, 'utf8'));
    }

    res.json(data);
  } catch (error) {
    console.error('Error getting original data:', error);
    res.status(500).json({ error: 'Failed to get original data' });
  }
});

// API: 保存JSON文件
app.post('/api/save-json', (req, res) => {
  try {
    const { type, scenarioId, fileType, data } = req.body;
    const paths = DATA_PATHS[type];
    
    if (!paths) {
      return res.status(400).json({ error: 'Invalid dataset type' });
    }
    
    let filePath;
    switch (fileType) {
      case 'trajectory':
        filePath = path.resolve(__dirname, paths.trajectories, `${scenarioId.padStart(5, '0')}_task_00001_trajectory.json`);
        break;
      case 'scene':
        filePath = path.resolve(__dirname, paths.scenes, `${scenarioId.padStart(5, '0')}_scene.json`);
        break;
      case 'task':
        filePath = path.resolve(__dirname, paths.tasks, `${scenarioId.padStart(5, '0')}_task.json`);
        break;
      default:
        return res.status(400).json({ error: 'Invalid file type' });
    }
    
    console.log(`Saving ${fileType} file to: ${filePath}`);

    // 备份原文件
    if (fs.existsSync(filePath)) {
      const backupPath = filePath + '.backup.' + Date.now();
      fs.copyFileSync(filePath, backupPath);
      console.log(`Backup created: ${backupPath}`);
    }

    // 保存新文件
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    console.log(`File saved successfully: ${filePath}`);
    res.json({ success: true });
  } catch (error) {
    console.error('Error saving JSON:', error);
    res.status(500).json({ error: 'Failed to save JSON' });
  }
});

// API: 保存评估结果
app.post('/api/save-evaluation', async (req, res) => {
  try {
    const { type, scenarioId, taskIndex, taskCategory, taskDescription, evaluationResult, notes } = req.body;
    
    // 读取现有结果
    const existingResults = [];
    if (fs.existsSync(EVALUATION_CSV)) {
      await new Promise((resolve) => {
        fs.createReadStream(EVALUATION_CSV)
          .pipe(csv())
          .on('data', (row) => {
            const key = `${row.dataset_type}-${row.scenario_id}-${row.task_index}`;
            const currentKey = `${type}-${scenarioId}-${taskIndex}`;
            if (key !== currentKey) {
              existingResults.push(row);
            }
          })
          .on('end', resolve);
      });
    }
    
    // 添加新结果
    existingResults.push({
      dataset_type: type,
      scenario_id: scenarioId,
      task_index: taskIndex,
      task_category: taskCategory,
      task_description: taskDescription,
      evaluation_result: evaluationResult,
      timestamp: new Date().toISOString(),
      notes: notes || ''
    });
    
    // 写入CSV
    const csvWriter = createCsvWriter({
      path: EVALUATION_CSV,
      header: [
        { id: 'dataset_type', title: 'dataset_type' },
        { id: 'scenario_id', title: 'scenario_id' },
        { id: 'task_index', title: 'task_index' },
        { id: 'task_category', title: 'task_category' },
        { id: 'task_description', title: 'task_description' },
        { id: 'evaluation_result', title: 'evaluation_result' },
        { id: 'timestamp', title: 'timestamp' },
        { id: 'notes', title: 'notes' }
      ]
    });
    
    await csvWriter.writeRecords(existingResults);
    res.json({ success: true });
  } catch (error) {
    console.error('Error saving evaluation:', error);
    res.status(500).json({ error: 'Failed to save evaluation' });
  }
});

// 初始化
initEvaluationCSV();

app.listen(PORT, () => {
  console.log(`数据集矫正工具启动成功！`);
  console.log(`请访问: http://localhost:${PORT}`);
});
