class DatasetCorrectionTool {
    constructor() {
        this.failedTasks = [];
        this.currentIndex = 0;
        this.editors = {};
        this.currentTask = null;
        this.originalData = {}; // 存储原始数据用于重置
        
        this.init();
    }
    
    async init() {
        this.showStatus('正在加载数据...', 'info');
        
        try {
            // 初始化JSON编辑器
            this.initEditors();
            
            // 绑定事件
            this.bindEvents();
            
            // 加载失败任务
            await this.loadFailedTasks();
            
            // 加载第一个任务
            if (this.failedTasks.length > 0) {
                await this.loadTask(0);
            } else {
                this.showStatus('没有找到失败的任务', 'info');
            }
        } catch (error) {
            console.error('初始化失败:', error);
            this.showStatus('初始化失败: ' + error.message, 'error');
        }
    }
    
    initEditors() {
        // 任务编辑器
        this.editors.task = new JSONEditor(document.getElementById('task-editor'), {
            mode: 'code',
            modes: ['code', 'tree', 'form'],
            search: true,
            searchBox: true, // 默认显示搜索框
            history: true,
            navigationBar: true,
            statusBar: true,
            expandAll: true, // 默认展开所有级别
            enableSort: true,
            enableTransform: true,
            mainMenuBar: true,
            onEditable: function (node) {
                // 允许编辑所有节点
                return true;
            },
            onChange: () => {
                console.log('Task editor changed, triggering auto-save');
                this.autoSave('task');
            }
        });

        // 场景编辑器
        this.editors.scene = new JSONEditor(document.getElementById('scene-editor'), {
            mode: 'code',
            modes: ['code', 'tree', 'form'],
            search: true,
            searchBox: true, // 默认显示搜索框
            history: true,
            navigationBar: true,
            statusBar: true,
            enableSort: true,
            enableTransform: true,
            mainMenuBar: true,
            onEditable: function (node) {
                // 允许编辑所有节点
                return true;
            },
            onChange: () => {
                console.log('Scene editor changed, triggering auto-save');
                this.autoSave('scene');
            }
        });

        // 轨迹编辑器 - 只读模式
        this.editors.trajectory = new JSONEditor(document.getElementById('trajectory-editor'), {
            mode: 'code', // 代码模式，但只读
            modes: ['code', 'view'],
            search: true,
            searchBox: true, // 默认显示搜索框
            navigationBar: true,
            statusBar: true,
            sortObjectKeys: false,
            expandAll: true, // 默认展开所有级别
            readOnly: true // 设置为只读
        });
    }
    
    bindEvents() {
        // 单选按钮事件
        document.querySelectorAll('input[name="completable"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const correctnessQuestion = document.getElementById('correctness-question');
                if (e.target.value === 'yes') {
                    correctnessQuestion.style.display = 'block';
                } else {
                    correctnessQuestion.style.display = 'none';
                    // 清除第二个问题的选择
                    document.querySelectorAll('input[name="correctness"]').forEach(r => r.checked = false);
                }
            });
        });
        
        // 按钮事件
        document.getElementById('save-evaluation').addEventListener('click', () => this.saveEvaluation());
        document.getElementById('prev-task').addEventListener('click', () => this.prevTask());
        document.getElementById('next-task').addEventListener('click', () => this.nextTask());
        document.getElementById('jump-task').addEventListener('click', () => this.jumpToTask());

        // 保存按钮事件
        document.getElementById('save-task').addEventListener('click', () => this.manualSave('task'));
        document.getElementById('save-scene').addEventListener('click', () => this.manualSave('scene'));

        // 重置按钮事件
        document.getElementById('reset-task').addEventListener('click', () => this.resetEditor('task'));
        document.getElementById('reset-scene').addEventListener('click', () => this.resetEditor('scene'));
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        this.prevTask();
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        this.nextTask();
                        break;
                    case 's':
                        e.preventDefault();
                        this.saveEvaluation();
                        break;
                }
            }
        });
    }
    
    async loadFailedTasks() {
        const response = await fetch('/api/failed-tasks');
        if (!response.ok) {
            throw new Error('加载失败任务列表失败');
        }
        
        this.failedTasks = await response.json();
        this.updateProgress();
    }
    
    async loadTask(index) {
        if (index < 0 || index >= this.failedTasks.length) {
            return;
        }
        
        this.currentIndex = index;
        this.currentTask = this.failedTasks[index];
        
        this.showStatus('正在加载任务数据...', 'info');
        
        try {
            // 更新界面信息
            this.updateTaskInfo();
            
            // 加载JSON数据
            const response = await fetch(`/api/task-data/${this.currentTask.type}/${this.currentTask.scenario_id}/${this.currentTask.task_index}`);
            if (!response.ok) {
                throw new Error('加载任务数据失败');
            }
            
            const data = await response.json();

            // 存储原始数据用于重置
            this.originalData = {
                task: JSON.parse(JSON.stringify(data.task || {})),
                scene: JSON.parse(JSON.stringify(data.scene || {})),
                trajectory: JSON.parse(JSON.stringify(data.trajectory || {}))
            };

            // 更新编辑器内容
            this.setTaskWithSmartExpansion(data.task || {});
            this.setSceneWithSmartExpansion(data.scene || {});
            this.editors.trajectory.set(data.trajectory || {});

            // 更新评估状态
            this.updateEvaluationState();
            
            this.showStatus('任务数据加载完成', 'success');
            
        } catch (error) {
            console.error('加载任务失败:', error);
            this.showStatus('加载任务失败: ' + error.message, 'error');
        }
    }

    updateTaskInfo() {
        document.getElementById('current-task').textContent =
            `${this.currentTask.type}-${this.currentTask.scenario_id}-task_${this.currentTask.task_index}`;
        document.getElementById('task-category').textContent = this.currentTask.task_category;
        document.getElementById('task-description').textContent = this.currentTask.task_description;

        // 更新跳转输入框的最大值
        const jumpInput = document.getElementById('jump-index');
        jumpInput.max = this.failedTasks.length;
        jumpInput.value = this.currentIndex + 1;
    }

    updateProgress() {
        document.getElementById('progress').textContent =
            `${this.currentIndex + 1}/${this.failedTasks.length}`;

        // 更新导航按钮状态
        document.getElementById('prev-task').disabled = this.currentIndex === 0;
        document.getElementById('next-task').disabled = this.currentIndex === this.failedTasks.length - 1;
    }

    updateEvaluationState() {
        // 清除之前的选择
        document.querySelectorAll('input[name="completable"]').forEach(r => r.checked = false);
        document.querySelectorAll('input[name="correctness"]').forEach(r => r.checked = false);
        document.getElementById('notes').value = '';
        document.getElementById('correctness-question').style.display = 'none';

        // 显示上次结果
        const previousResult = this.currentTask.previous_result || 'None';
        document.getElementById('previous-result').textContent = previousResult;

        // 根据上次结果预设选择
        if (previousResult === 'True') {
            document.querySelector('input[name="completable"][value="yes"]').checked = true;
            document.querySelector('input[name="correctness"][value="correct"]').checked = true;
            document.getElementById('correctness-question').style.display = 'block';
        } else if (previousResult === 'False') {
            document.querySelector('input[name="completable"][value="yes"]').checked = true;
            document.querySelector('input[name="correctness"][value="incorrect"]').checked = true;
            document.getElementById('correctness-question').style.display = 'block';
        } else if (previousResult === 'None') {
            document.querySelector('input[name="completable"][value="no"]').checked = true;
        }
    }

    async autoSave(fileType) {
        if (!this.currentTask) return;

        // 轨迹数据是只读的，不需要保存
        if (fileType === 'trajectory') return;

        try {
            const data = this.editors[fileType].get();
            console.log(`Auto-saving ${fileType} for task ${this.currentTask.type}-${this.currentTask.scenario_id}`);

            const response = await fetch('/api/save-json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: this.currentTask.type,
                    scenarioId: this.currentTask.scenario_id,
                    fileType: fileType,
                    data: data
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`保存失败: ${response.status} - ${errorText}`);
            }

            console.log(`Auto-save successful for ${fileType}`);

        } catch (error) {
            console.error('自动保存失败:', error);
            // 显示保存失败的提示
            this.showStatus(`自动保存${fileType === 'task' ? '任务' : '场景'}失败: ${error.message}`, 'error');
        }
    }

    async manualSave(fileType) {
        if (!this.currentTask) {
            this.showStatus('没有当前任务', 'error');
            return;
        }

        // 轨迹数据是只读的，不需要保存
        if (fileType === 'trajectory') {
            this.showStatus('轨迹数据是只读的', 'info');
            return;
        }

        try {
            this.showStatus(`正在保存${fileType === 'task' ? '任务定义' : '场景配置'}...`, 'info');

            const data = this.editors[fileType].get();
            console.log(`Manual save ${fileType} for task ${this.currentTask.type}-${this.currentTask.scenario_id}`);

            const response = await fetch('/api/save-json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: this.currentTask.type,
                    scenarioId: this.currentTask.scenario_id,
                    fileType: fileType,
                    data: data
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`保存失败: ${response.status} - ${errorText}`);
            }

            console.log(`Manual save successful for ${fileType}`);
            this.showStatus(`${fileType === 'task' ? '任务定义' : '场景配置'}保存成功`, 'success');

        } catch (error) {
            console.error('手动保存失败:', error);
            this.showStatus(`保存${fileType === 'task' ? '任务定义' : '场景配置'}失败: ${error.message}`, 'error');
        }
    }

    async saveEvaluation() {
        if (!this.currentTask) return;

        const completableRadio = document.querySelector('input[name="completable"]:checked');
        if (!completableRadio) {
            this.showStatus('请选择任务是否可以完成', 'error');
            return;
        }

        let evaluationResult;
        if (completableRadio.value === 'no') {
            evaluationResult = 'None';
        } else {
            const correctnessRadio = document.querySelector('input[name="correctness"]:checked');
            if (!correctnessRadio) {
                this.showStatus('请选择4o是否完成正确', 'error');
                return;
            }
            evaluationResult = correctnessRadio.value === 'correct' ? 'True' : 'False';
        }

        const notes = document.getElementById('notes').value.trim();

        try {
            const response = await fetch('/api/save-evaluation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: this.currentTask.type,
                    scenarioId: this.currentTask.scenario_id,
                    taskIndex: this.currentTask.task_index,
                    taskCategory: this.currentTask.task_category,
                    taskDescription: this.currentTask.task_description,
                    evaluationResult: evaluationResult,
                    notes: notes
                })
            });

            if (!response.ok) {
                throw new Error('保存评估失败');
            }

            // 更新当前任务的结果
            this.currentTask.previous_result = evaluationResult;

            // 更新评估状态显示
            this.updateEvaluationState();

            this.showStatus('评估结果已保存', 'success');

        } catch (error) {
            console.error('保存评估失败:', error);
            this.showStatus('保存评估失败: ' + error.message, 'error');
        }
    }

    async prevTask() {
        if (this.currentIndex > 0) {
            await this.loadTask(this.currentIndex - 1);
            this.updateProgress();
        }
    }

    async nextTask() {
        if (this.currentIndex < this.failedTasks.length - 1) {
            await this.loadTask(this.currentIndex + 1);
            this.updateProgress();
        }
    }

    async jumpToTask() {
        const jumpInput = document.getElementById('jump-index');
        const targetIndex = parseInt(jumpInput.value) - 1;

        if (targetIndex >= 0 && targetIndex < this.failedTasks.length) {
            await this.loadTask(targetIndex);
            this.updateProgress();
        } else {
            this.showStatus('无效的任务编号', 'error');
        }
    }

    showStatus(message, type = 'info') {
        const statusElement = document.getElementById('status');
        statusElement.textContent = message;
        statusElement.className = `status ${type}`;

        // 3秒后清除状态
        setTimeout(() => {
            statusElement.textContent = '';
            statusElement.className = 'status';
        }, 3000);
    }

    // 重置编辑器到原始状态
    async resetEditor(editorType) {
        if (!this.currentTask) {
            this.showStatus('没有当前任务', 'error');
            return;
        }

        try {
            this.showStatus('正在获取原始数据...', 'info');

            // 从服务器获取原始数据
            const response = await fetch(`/api/original-data/${this.currentTask.type}/${this.currentTask.scenario_id}/${this.currentTask.task_index}`);
            if (!response.ok) {
                throw new Error('获取原始数据失败');
            }

            const originalData = await response.json();

            if (!originalData[editorType]) {
                this.showStatus('没有原始数据可以重置', 'error');
                return;
            }

            if (editorType === 'scene') {
                this.setSceneWithSmartExpansion(originalData[editorType]);
            } else if (editorType === 'task') {
                this.setTaskWithSmartExpansion(originalData[editorType]);
            } else {
                this.editors[editorType].set(originalData[editorType]);
            }

            this.showStatus(`${editorType === 'task' ? '任务定义' : '场景配置'}已重置`, 'success');

        } catch (error) {
            console.error('重置失败:', error);
            this.showStatus('重置失败: ' + error.message, 'error');
        }
    }

    // 智能展开任务定义
    setTaskWithSmartExpansion(taskData) {
        this.editors.task.set(taskData);

        // 如果是树形模式，才执行展开操作
        if (this.editors.task.getMode() === 'tree') {
            setTimeout(() => {
                this.expandTaskNodes();
            }, 100); // 延迟执行，确保编辑器已渲染
        }
    }

    // 展开任务定义的特定节点
    expandTaskNodes() {
        try {
            const editor = this.editors.task;

            // 收起根级别的所有节点
            editor.collapseAll();

            // 展开tasks节点及其所有子节点
            setTimeout(() => {
                try {
                    // 展开tasks数组
                    editor.expandPath(['tasks']);

                    // 获取tasks数组的长度
                    const taskData = editor.get();
                    if (taskData.tasks && Array.isArray(taskData.tasks)) {
                        taskData.tasks.forEach((task, index) => {
                            // 展开每个task对象
                            editor.expandPath(['tasks', index]);

                            // 展开task的所有子属性
                            Object.keys(task).forEach(key => {
                                try {
                                    editor.expandPath(['tasks', index, key]);

                                    // 如果是validation_checks数组，展开其所有元素
                                    if (key === 'validation_checks' && Array.isArray(task[key])) {
                                        task[key].forEach((check, checkIndex) => {
                                            editor.expandPath(['tasks', index, key, checkIndex]);
                                        });
                                    }
                                } catch (e) {
                                    // 忽略无法展开的路径
                                }
                            });
                        });
                    }
                } catch (e) {
                    console.log('展开tasks节点时出错:', e);
                }
            }, 50);

        } catch (error) {
            console.log('智能展开任务定义时出错:', error);
        }
    }

    // 智能展开场景配置
    setSceneWithSmartExpansion(sceneData) {
        this.editors.scene.set(sceneData);

        // 如果是树形模式，才执行展开操作
        if (this.editors.scene.getMode() === 'tree') {
            setTimeout(() => {
                this.expandSceneNodes();
            }, 100); // 延迟执行，确保编辑器已渲染
        }
    }

    // 展开场景配置的特定节点
    expandSceneNodes() {
        try {
            const editor = this.editors.scene;

            // 收起根级别的所有节点
            editor.collapseAll();

            // 展开objects节点
            setTimeout(() => {
                try {
                    editor.expandPath(['objects']);

                    // 获取objects数组的长度，展开每个对象的第一层
                    const sceneData = editor.get();
                    if (sceneData.objects && Array.isArray(sceneData.objects)) {
                        sceneData.objects.forEach((obj, index) => {
                            try {
                                editor.expandPath(['objects', index]);
                            } catch (e) {
                                // 忽略无法展开的路径
                            }
                        });
                    }
                } catch (e) {
                    console.log('展开objects节点时出错:', e);
                }
            }, 50);

        } catch (error) {
            console.log('智能展开场景配置时出错:', error);
        }
    }

}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new DatasetCorrectionTool();
});
