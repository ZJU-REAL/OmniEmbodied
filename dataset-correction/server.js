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

// Data path configuration
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

// Initialize evaluation results CSV
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

// Read failed tasks
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

// Read evaluation results
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

// API: Get failed tasks list
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

// API: Get task data
app.get('/api/task-data/:type/:scenarioId/:taskIndex', (req, res) => {
  try {
    const { type, scenarioId, taskIndex } = req.params;
    const paths = DATA_PATHS[type];
    
    if (!paths) {
      return res.status(400).json({ error: 'Invalid dataset type' });
    }
    
    const data = {};
    
    // Read trajectory file - fix filename format
    // Trajectory filename format: {scenarioId}_task_00001_trajectory.json (task index is always 00001)
    const trajectoryPath = path.resolve(__dirname, paths.trajectories, `${scenarioId.padStart(5, '0')}_task_00001_trajectory.json`);
    if (fs.existsSync(trajectoryPath)) {
      data.trajectory = JSON.parse(fs.readFileSync(trajectoryPath, 'utf8'));
    }
    
    // Read scene file
    const scenePath = path.resolve(__dirname, paths.scenes, `${scenarioId.padStart(5, '0')}_scene.json`);
    if (fs.existsSync(scenePath)) {
      data.scene = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
    }

    // Read task file
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

// API: Get original data (for reset)
app.get('/api/original-data/:type/:scenarioId/:taskIndex', (req, res) => {
  try {
    const { type, scenarioId, taskIndex } = req.params;
    const paths = DATA_PATHS[type];

    if (!paths) {
      return res.status(400).json({ error: 'Invalid dataset type' });
    }

    const data = {};

    // Read scene file
    const scenePath = path.resolve(__dirname, paths.scenes, `${scenarioId.padStart(5, '0')}_scene.json`);
    if (fs.existsSync(scenePath)) {
      data.scene = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
    }

    // Read task file
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

// API: Save JSON file
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

    // Backup original file
    if (fs.existsSync(filePath)) {
      const backupPath = filePath + '.backup.' + Date.now();
      fs.copyFileSync(filePath, backupPath);
      console.log(`Backup created: ${backupPath}`);
    }

    // Save new file
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    console.log(`File saved successfully: ${filePath}`);
    res.json({ success: true });
  } catch (error) {
    console.error('Error saving JSON:', error);
    res.status(500).json({ error: 'Failed to save JSON' });
  }
});

// API: Save evaluation results
app.post('/api/save-evaluation', async (req, res) => {
  try {
    const { type, scenarioId, taskIndex, taskCategory, taskDescription, evaluationResult, notes } = req.body;
    
    // Read existing results
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
    
    // Add new result
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
    
    // Write to CSV
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

// Initialize
initEvaluationCSV();

app.listen(PORT, () => {
  console.log(`Dataset Correction Tool started successfully!`);
console.log(`Please visit: http://localhost:${PORT}`);
});
