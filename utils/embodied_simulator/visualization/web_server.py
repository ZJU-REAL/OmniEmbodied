"""
可视化Web服务器模块
提供HTTP API和WebSocket接口用于实时数据传输
"""

import json
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
import os
from typing import Dict, Any, Optional
import logging


class VisualizationRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""

    def __init__(self, *args, data_provider=None, config=None, **kwargs):
        self.data_provider = data_provider
        self.config = config or {}
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """重写日志方法以禁用HTTP请求日志"""
        # 不输出任何日志，完全静默
        pass
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # API路由
        if path.startswith('/api/'):
            self._handle_api_request(path, parsed_path.query)
        elif path == '/' or path == '/index.html':
            self._serve_index_page()

        elif path.endswith('.js') or path.endswith('.css') or path.endswith('.html'):
            self._serve_static_file(path)
        else:
            self.send_error(404, "File not found")
    
    def _handle_api_request(self, path: str, query: str):
        """处理API请求"""
        try:
            if path == '/api/data':
                # 获取完整数据
                data = self.data_provider.get_complete_visualization_data()
                self._send_json_response(data)
            elif path == '/api/rooms':
                # 获取房间列表
                data = self.data_provider.get_complete_visualization_data()
                self._send_json_response(data.get('rooms', []))
            elif path.startswith('/api/room/'):
                # 获取特定房间数据
                room_id = path.split('/')[-1]
                data = self.data_provider.get_room_layout_data(room_id)
                self._send_json_response(data)
            elif path == '/api/agents':
                # 获取智能体数据
                data = self.data_provider.get_complete_visualization_data()
                self._send_json_response(data.get('agents', []))
            elif path == '/api/objects':
                # 获取物体数据
                data = self.data_provider.get_complete_visualization_data()
                self._send_json_response(data.get('objects', []))
            elif path == '/api/config':
                # 获取配置信息
                self._send_json_response(self.config)
            else:
                self.send_error(404, "API endpoint not found")
        except Exception as e:
            logging.error(f"API请求处理错误: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def _send_json_response(self, data: Any):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def _serve_index_page(self):
        """提供主页"""
        html_content = self._generate_index_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def _serve_static_file(self, path: str):
        """提供静态文件"""
        try:
            # 获取当前文件的目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            static_dir = os.path.join(current_dir, 'static')

            # 构建文件路径 - 移除/static/前缀
            filename = path.replace('/static/', '').lstrip('/')
            file_path = os.path.join(static_dir, filename)

            # 检查文件是否存在
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_error(404, "Static file not found")
                return

            # 确定内容类型
            if path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif path.endswith('.html'):
                content_type = 'text/html; charset=utf-8'
            else:
                content_type = 'text/plain; charset=utf-8'

            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        except Exception as e:
            logging.error(f"提供静态文件失败 {path}: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")


    
    def _generate_index_html(self) -> str:
        """生成主页HTML"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>模拟器可视化</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .container { display: flex; height: 100vh; }
        .sidebar { width: 380px; background: white; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; overflow: hidden; }
        .main-view { flex: 1; display: flex; flex-direction: column; }
        .header { background: white; padding: 15px 20px; border-bottom: 1px solid #e0e0e0; flex-shrink: 0; }
        .header h1 { margin: 0; font-size: 24px; color: #333; }
        .status { margin-top: 8px; font-size: 14px; color: #666; }
        .sidebar-content { flex: 1; overflow-y: auto; padding: 0; }
        .info-panel { border-bottom: 1px solid #e0e0e0; }
        .panel-header { padding: 12px 20px; background: #f8f9fa; cursor: pointer; display: flex; justify-content: space-between; align-items: center; user-select: none; }

        .panel-header h3 { margin: 0; font-size: 14px; color: #333; font-weight: 600; }
        .toggle-icon { font-size: 12px; color: #666; transition: transform 0.2s ease; }
        .info-panel.collapsed .toggle-icon { transform: rotate(-90deg); }
        .info-panel.collapsed .panel-content { display: none; }
        .panel-content { padding: 15px 20px; }
        .room-item, .agent-item, .object-item {
            padding: 12px; margin: 8px 0; background: #f8f9fa; border-radius: 6px; cursor: pointer;
            border-left: 4px solid transparent; transition: all 0.2s ease;
        }

        .room-item.selected { background: #e3f2fd; border-left-color: #2196f3; }
        .item-title { font-weight: 600; color: #333; margin-bottom: 4px; }
        .item-details { font-size: 12px; color: #666; }
        .visualization-container { flex: 1; position: relative; background: white; }
        .canvas-container { position: relative; width: 100%; height: 100%; }
        .canvas-controls { position: absolute; top: 10px; right: 10px; z-index: 10; }
        .control-btn {
            background: rgba(255,255,255,0.9); border: 1px solid #ddd; border-radius: 4px;
            padding: 8px 12px; margin-left: 5px; cursor: pointer; font-size: 12px;
        }

        #visualizationCanvas { display: block; width: 100%; height: 100%; }
        .loading { text-align: center; padding: 50px; color: #666; }
        .error { color: #d32f2f; padding: 10px; background: #ffebee; border-radius: 4px; margin: 10px 0; }

        .legend { position: absolute; bottom: 10px; left: 10px; background: rgba(255,255,255,0.95);
                 padding: 15px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 13px; }
        .legend-item { display: flex; align-items: center; margin: 6px 0; font-size: 12px; }
        .legend-color { width: 18px; height: 18px; margin-right: 10px; border-radius: 3px; }
        .object-details-panel { max-height: 400px; overflow-y: auto; }
        .object-hierarchy { margin-left: 15px; border-left: 2px solid #e0e0e0; padding-left: 10px; }
        .clickable-item { cursor: pointer; transition: background-color 0.2s ease; }




        /* 智能体状态卡片样式 */
        .agent-status-card {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .agent-status-card.selected {
            background: #e8f5e8;
            border-color: #4caf50;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
        }
        .agent-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .agent-location {
            font-size: 11px;
            color: #666;
            margin-bottom: 8px;
        }
        .agent-inventory {
            font-size: 11px;
            color: #333;
            margin-bottom: 6px;
        }
        .agent-abilities {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-top: 6px;
        }
        .ability-tag {
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 500;
        }
        .inventory-item {
            background: #fff3e0;
            color: #f57c00;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 10px;
            margin-right: 4px;
            display: inline-block;
        }
        .inventory-item.tool {
            background: #ffcc80;
            color: #e65100;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="header">
                <h1>🤖 模拟器可视化</h1>
                <div class="status" id="status">正在连接...</div>
            </div>
            <div class="sidebar-content">
                <!-- 1. 任务信息面板 -->
                <div class="info-panel">
                    <div class="panel-header" onclick="togglePanel(this)">
                        <h3>📋 任务信息</h3>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="panel-content">
                        <div id="taskInfo" style="margin-bottom: 15px;">
                            <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #666; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px;">所有任务</h4>
                            <div id="allTasksList" style="font-size: 12px; max-height: 300px; overflow-y: auto;">加载中...</div>
                        </div>

                        <div id="actionInfo">
                            <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #666; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px;">支持的动作</h4>
                            <div id="supportedActions" style="font-size: 11px; max-height: 150px; overflow-y: auto;">加载中...</div>
                        </div>
                    </div>
                </div>

                <!-- 2. 智能体信息面板 -->
                <div class="info-panel">
                    <div class="panel-header" onclick="togglePanel(this)">
                        <h3>🤖 智能体信息</h3>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="panel-content">
                        <div id="agentStatusSection">
                            <div id="agentStatusList" style="max-height: 300px; overflow-y: auto;">
                                <div class="loading">加载中...</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 3. 环境信息面板 -->
                <div class="info-panel">
                    <div class="panel-header" onclick="togglePanel(this)">
                        <h3>🌍 环境信息</h3>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="panel-content">
                        <div id="environmentOverview" style="margin-bottom: 15px;">
                            <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #666; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px;">环境概览</h4>
                            <div id="environmentStats" style="font-size: 12px; color: #333; margin-bottom: 12px;">加载中...</div>
                        </div>

                        <div id="roomsSection" style="margin-bottom: 15px;">
                            <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #666; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px;">房间列表</h4>
                            <div id="roomList" style="max-height: 200px; overflow-y: auto;">
                                <div class="loading">加载中...</div>
                            </div>
                        </div>


                    </div>
                </div>

                <!-- 4. 选中物体详情面板 -->
                <div class="info-panel">
                    <div class="panel-header" onclick="togglePanel(this)">
                        <h3>🔍 选中物体详情</h3>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="panel-content">
                        <div id="objectDetails">
                            <div style="color: #666; font-size: 12px; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 6px; border: 2px dashed #ddd;">
                                <div style="font-size: 24px; margin-bottom: 8px;">🖱️</div>
                                <div>点击地图上的物体或智能体查看详细信息</div>
                                <div style="font-size: 10px; color: #999; margin-top: 4px;">包括属性、状态、关系、能力等完整信息</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="main-view">
            <div class="visualization-container">
                <div class="canvas-container">
                    <canvas id="visualizationCanvas"></canvas>
                    <div class="canvas-controls">
                        <button class="control-btn" onclick="resetView()">重置视图</button>
                    </div>
                    <div class="legend">
                        <div style="font-weight: bold; margin-bottom: 8px; color: #333;">图例说明</div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #8d6e63;"></div>
                            <span>家具 (FURNITURE)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #2196f3;"></div>
                            <span>物品 (ITEM)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #ff9800;"></div>
                            <span>工具 🔧</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #4caf50;"></div>
                            <span>智能体 🤖</span>
                        </div>
                        <div style="margin: 10px 0; border-top: 1px solid #e0e0e0; padding-top: 8px;">
                            <div style="font-weight: bold; font-size: 11px; color: #666; margin-bottom: 4px;">边框颜色含义:</div>
                            <div class="legend-item">
                                <div class="legend-color" style="border: 3px solid #4caf50; background: transparent;"></div>
                                <span>在...内部 (in)</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="border: 3px solid #2196f3; background: transparent;"></div>
                                <span>在...上面 (on)</span>
                            </div>
                        </div>
                        <div style="margin-top: 10px; border-top: 1px solid #e0e0e0; padding-top: 8px;">
                            <div style="font-size: 11px; color: #666;">
                                • 物体以嵌套盒子形式显示<br>
                                • 点击物体或房间查看详情<br>
                                • 拖拽和滚轮缩放地图
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>

    <script src="/static/visualization.js"></script>
    <script>
        // 内联配置 - 适用于一致JSON结构的数据
        const VISUALIZATION_CONFIG = {
            gridSize: 20,
            roomColors: { 'default': '#fafafa' },
            objectColors: {
                'FURNITURE': '#d7ccc8', 'ITEM': '#bbdefb', 'AGENT': '#c8e6c9',
                'TOOL': '#ffcc80', 'CONTAINER': '#e1bee7', 'DEVICE': '#ffcdd2',
                'MATERIAL': '#dcedc8', 'default': '#f5f5f5'
            },
            relationColors: {
                'in': '#4caf50', 'on': '#2196f3', 'near': '#ff9800',
                'attached': '#9c27b0', 'default': '#757575'
            },
            selectedColors: { background: '#fff3e0', border: '#ff9800', text: '#e65100' },
            layout: {
                roomPadding: 30, minRoomSize: 400, roomMargin: 120, maxRoomCols: 2,
                roomHeaderHeight: 100, roomAspectRatio: { min: 0.7, max: 2.2 },
                objectPadding: 15, minObjectSize: 120, maxObjectSize: 180,
                objectHeaderHeight: 35, objectAspectRatio: { min: 0.5, max: 3.0 },
                agentAreaWidth: 80, agentSize: 65, agentRadius: 30, agentMargin: 20,
                fontSize: 12, titleFontSize: 14, headerHeight: 45,
                columnRules: {
                    room: [
                        { maxObjects: 2, cols: 'actual' }, { maxObjects: 4, cols: 2 },
                        { maxObjects: 9, cols: 3 }, { maxObjects: 16, cols: 4 },
                        { maxObjects: Infinity, cols: 5 }
                    ],
                    object: [
                        { maxObjects: 2, cols: 'actual' }, { maxObjects: 4, cols: 2 },
                        { maxObjects: 9, cols: 3 }, { maxObjects: Infinity, cols: 4 }
                    ]
                }
            }
        };
    </script>
    <script>
        // 全局变量
        let visualization = null;
        let currentData = null;
        let updateInterval = null;

        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            initVisualization();
            startDataUpdates();
            initializePanels();
        });

        function initializePanels() {
            // 默认展开基本信息和物品列表面板
            const panels = document.querySelectorAll('.info-panel');
            panels.forEach((panel, index) => {
                if (index > 1) { // 除了前两个面板，其他都折叠
                    panel.classList.add('collapsed');
                }
            });
        }

        function togglePanel(header) {
            const panel = header.parentElement;
            panel.classList.toggle('collapsed');
        }

        function initVisualization() {
            // 创建可视化实例，使用外部配置
            const config = window.VISUALIZATION_CONFIG || {};
            visualization = new SimulatorVisualization('visualizationCanvas', config);

            // 监听房间选择事件
            document.getElementById('visualizationCanvas').addEventListener('roomSelected', function(e) {
                selectRoom(e.detail.roomId);
            });

            // 监听智能体选择事件
            document.getElementById('visualizationCanvas').addEventListener('agentSelected', function(e) {
                selectAgent(e.detail.agent.id);
            });

            // 监听物体选择事件
            document.getElementById('visualizationCanvas').addEventListener('objectSelected', function(e) {
                selectObject(e.detail.object);
            });
        }

        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                currentData = data;

                // 更新可视化
                if (visualization) {
                    visualization.updateData(data);
                }

                // 更新UI
                updateSidebar(data);
                updateStatus('已连接 - 最后更新: ' + new Date().toLocaleTimeString());

                // 如果是第一次加载数据，设置定时器
                if (!updateInterval) {
                    const requestInterval = data?.metadata?.request_interval || 2000;
                    updateInterval = setInterval(loadData, requestInterval);
                }

            } catch (error) {
                console.error('数据加载失败:', error);
                updateStatus('<span class="error">连接失败: ' + error.message + '</span>');
            }
        }

        function updateSidebar(data) {
            // 1. 更新任务信息
            updateTaskInfo(data);

            // 2. 更新智能体信息
            updateAgentInfo(data);

            // 3. 更新环境信息
            updateEnvironmentInfo(data);

            // 4. 物体详情在选中时更新，这里不需要处理
        }

        function updateTaskInfo(data) {

            // 更新所有任务列表
            const allTasksList = document.getElementById('allTasksList');
            if (!allTasksList) return;

            // 显示TODO list形式的任务列表
            if (data.detailed_tasks && data.detailed_tasks.length > 0) {
                let tasksHtml = '';

                // 显示总体进度概览（基于详细任务计算）
                const totalTasks = data.detailed_tasks.length;
                const completedTasks = data.detailed_tasks.filter(task => task.is_completed).length;
                const completionRate = totalTasks > 0 ? completedTasks / totalTasks : 0;
                const progressBarWidth = Math.round(completionRate * 100);
                const isAllCompleted = completionRate >= 1.0;
                const statusIcon = isAllCompleted ? '✅' : '⏳';
                const statusColor = isAllCompleted ? '#4caf50' : '#ff9800';

                tasksHtml += `
                    <div style="padding: 12px; margin: 8px 0; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; border: 2px solid #007bff; box-shadow: 0 3px 6px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div style="font-weight: 600; font-size: 14px; color: #007bff;">📋 任务总览</div>
                            <div style="font-size: 12px; color: ${statusColor}; font-weight: 600;">${statusIcon} ${completedTasks}/${totalTasks} (${(completionRate * 100).toFixed(1)}%)</div>
                        </div>
                        <div style="font-size: 11px; color: #666; margin-bottom: 8px;">共 ${totalTasks} 个任务，已完成 ${completedTasks} 个</div>
                        <div style="width: 100%; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden;">
                            <div style="width: ${progressBarWidth}%; height: 100%; background: linear-gradient(90deg, ${isAllCompleted ? '#4caf50' : '#ff9800'}, ${isAllCompleted ? '#66bb6a' : '#ffb74d'}); transition: width 0.3s ease;"></div>
                        </div>
                    </div>
                `;

                // TODO List 标题
                tasksHtml += `
                    <div style="padding: 8px 0; margin: 8px 0 4px 0; border-bottom: 2px solid #e0e0e0;">
                        <div style="font-weight: 600; font-size: 13px; color: #333; display: flex; align-items: center; gap: 8px;">
                            📝 任务清单 (TODO List)
                        </div>
                    </div>
                `;

                // 显示所有任务的扁平TODO列表
                data.detailed_tasks.forEach((task, index) => {
                    const taskCompleted = task.is_completed || false;
                    const checkboxStyle = taskCompleted ?
                        'background: #4caf50; border: 2px solid #4caf50; color: white;' :
                        'background: white; border: 2px solid #ddd; color: transparent;';

                    const taskTextStyle = taskCompleted ?
                        'text-decoration: line-through; color: #666;' :
                        'color: #333;';

                    const taskBg = taskCompleted ? '#f8f9fa' : '#ffffff';
                    const borderColor = taskCompleted ? '#4caf50' : '#e0e0e0';

                    // 类别图标和颜色
                    const categoryIcon = task.category.includes('single_agent') ? '🤖' : '👥';
                    const categoryColor = task.category.includes('single_agent') ? '#2196f3' : '#ff9800';

                    tasksHtml += `
                        <div style="padding: 6px 8px; margin: 2px 0; background: ${taskBg}; border-radius: 4px; border-left: 3px solid ${borderColor}; transition: all 0.2s ease;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <!-- 序号和复选框 -->
                                <div style="display: flex; align-items: center; gap: 4px; flex-shrink: 0;">
                                    <span style="font-size: 9px; color: #999; font-weight: 500; min-width: 14px; text-align: right;">${index + 1}.</span>
                                    <div style="width: 14px; height: 14px; border-radius: 2px; ${checkboxStyle} display: flex; align-items: center; justify-content: center; font-size: 9px;">
                                        ${taskCompleted ? '✓' : ''}
                                    </div>
                                </div>

                                <!-- 任务内容 -->
                                <div style="flex: 1; min-width: 0;">
                                    <div style="font-size: 11px; line-height: 1.3; margin-bottom: 2px; ${taskTextStyle}">
                                        ${task.description || '无描述'}
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 4px;">
                                        <span style="background: ${categoryColor}15; color: ${categoryColor}; padding: 1px 3px; border-radius: 6px; font-weight: 500; font-size: 8px;">
                                            ${categoryIcon} ${task.category_name}
                                        </span>
                                    </div>
                                </div>

                                <!-- 状态图标 -->
                                <div style="font-size: 12px; flex-shrink: 0;">
                                    ${taskCompleted ? '✅' : '⭕'}
                                </div>
                            </div>
                        </div>
                    `;
                });

                allTasksList.innerHTML = tasksHtml;
            } else {
                allTasksList.innerHTML = '<div style="color: #999; font-size: 11px; text-align: center; padding: 10px;">暂无任务列表</div>';
            }

            // 更新支持的动作
            const supportedActions = document.getElementById('supportedActions');
            if (!supportedActions) return;

            if (data.supported_actions && data.supported_actions.length > 0) {
                // 按类型分组动作
                const actionsByType = {};
                data.supported_actions.forEach(action => {
                    const type = action.requires_tool ? '需要工具' : '基础动作';
                    if (!actionsByType[type]) actionsByType[type] = [];
                    actionsByType[type].push(action);
                });

                supportedActions.innerHTML = Object.entries(actionsByType).map(([type, actions]) => `
                    <div style="margin-bottom: 10px;">
                        <div style="font-weight: 600; font-size: 10px; color: #666; margin-bottom: 4px; text-transform: uppercase;">${type} (${actions.length})</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 2px;">
                            ${actions.map(action => `
                                <span style="font-size: 9px; background: ${action.requires_tool ? '#fff3e0' : '#e8f5e8'}; color: ${action.requires_tool ? '#f57c00' : '#2e7d32'}; padding: 2px 4px; border-radius: 3px; border: 1px solid ${action.requires_tool ? '#ffcc02' : '#4caf50'};">
                                    ${action.requires_tool ? '🔧' : '⚡'} ${action.name}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                `).join('');
            } else {
                supportedActions.innerHTML = '<div style="color: #999; font-size: 11px; text-align: center; padding: 10px;">暂无动作信息</div>';
            }
        }

        function updateAgentInfo(data) {
            const agentStatusList = document.getElementById('agentStatusList');
            if (!agentStatusList) return;

            if (data.agents && data.agents.length > 0) {
                agentStatusList.innerHTML = data.agents.map(agent => {
                    const inventoryItems = agent.inventory || [];
                    const abilities = agent.abilities || [];
                    const location = agent.location_id || agent.location || '未知位置';

                    // 获取物品详细信息
                    const inventoryDetails = inventoryItems.map(itemId => {
                        const item = data.objects ? data.objects.find(obj => obj.id === itemId) : null;
                        return {
                            id: itemId,
                            name: item ? item.name : itemId,
                            is_tool: item ? (item.properties && item.properties.provides_abilities) : false
                        };
                    });

                    return `
                        <div class="agent-status-card" onclick="selectAgent('${agent.id}')" data-agent-id="${agent.id}">
                            <div class="agent-name">
                                <span>🤖</span>
                                <span>${agent.name || agent.id}</span>
                                ${agent.corporate_mode_object_id ? '<span style="color: #ff9800; font-size: 10px;">🤝合作中</span>' : ''}
                            </div>

                            <div class="agent-location">
                                📍 位置: ${location}
                            </div>

                            <div class="agent-inventory">
                                🎒 库存 (${inventoryItems.length}/${agent.max_grasp_limit || 1}):
                                ${inventoryDetails.length > 0 ? `
                                    <div style="margin-top: 4px;">
                                        ${inventoryDetails.map(item => `
                                            <span class="inventory-item ${item.is_tool ? 'tool' : ''}" title="${item.name} (${item.id})">
                                                ${item.is_tool ? '🔧' : '📦'} ${item.name}
                                            </span>
                                        `).join('')}
                                    </div>
                                ` : '<span style="color: #999; font-size: 10px;">空</span>'}
                            </div>

                            ${abilities.length > 0 ? `
                                <div style="margin-top: 8px;">
                                    <div style="font-size: 11px; color: #666; margin-bottom: 4px;">⚡ 当前能力:</div>
                                    <div class="agent-abilities">
                                        ${abilities.map(ability => `
                                            <span class="ability-tag">${ability}</span>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : '<div style="font-size: 10px; color: #999; margin-top: 4px;">⚡ 暂无特殊能力</div>'}

                            ${agent.corporate_mode_object_id ? `
                                <div style="margin-top: 6px; padding: 4px 8px; background: #fff3e0; border-radius: 4px; border-left: 3px solid #ff9800;">
                                    <div style="font-size: 10px; color: #f57c00;">
                                        🤝 正在与其他智能体合作搬运: ${agent.corporate_mode_object_id}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('');
            } else {
                agentStatusList.innerHTML = '<div style="color: #999; font-size: 12px; text-align: center; padding: 20px;">暂无智能体信息</div>';
            }
        }

        function selectAgent(agentId) {
            // 高亮选中的智能体卡片
            document.querySelectorAll('.agent-status-card').forEach(card => {
                card.classList.remove('selected');
            });
            const agentCard = document.querySelector(`[data-agent-id="${agentId}"]`);
            if (agentCard) {
                agentCard.classList.add('selected');
            }

            // 在可视化中高亮智能体
            if (visualization) {
                visualization.selectAgent(agentId);
            }

            // 在详情面板显示智能体信息
            if (currentData && currentData.agents) {
                const agent = currentData.agents.find(a => a.id === agentId);
                if (agent) {
                    showAgentDetails(agent);
                }
            }
        }

        function showAgentDetails(agent) {
            const objectDetails = document.getElementById('objectDetails');
            if (!objectDetails) return;

            const inventoryItems = agent.inventory || [];
            const abilities = agent.abilities || [];

            // 获取物品详细信息
            const inventoryDetails = inventoryItems.map(itemId => {
                const item = currentData && currentData.objects ? currentData.objects.find(obj => obj.id === itemId) : null;
                return item || { id: itemId, name: itemId, type: 'UNKNOWN' };
            });

            objectDetails.innerHTML = `
                <div style="border: 2px solid #4caf50; border-radius: 8px; padding: 15px; background: #f8fff8;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                        <span style="font-size: 24px;">🤖</span>
                        <div>
                            <div style="font-weight: 600; font-size: 16px; color: #2e7d32;">${agent.name || agent.id}</div>
                            <div style="font-size: 12px; color: #666;">智能体 ID: ${agent.id}</div>
                        </div>
                    </div>

                    <div style="margin-bottom: 12px;">
                        <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 2px;">📍 位置信息</h4>
                        <div style="font-size: 12px; color: #333;">当前位置: ${agent.location_id || agent.location || '未知'}</div>
                        ${agent.near_objects && agent.near_objects.length > 0 ? `
                            <div style="font-size: 11px; color: #666; margin-top: 4px;">
                                附近物体: ${Array.from(agent.near_objects).join(', ')}
                            </div>
                        ` : ''}
                    </div>

                    <div style="margin-bottom: 12px;">
                        <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 2px;">🎒 库存信息</h4>
                        <div style="font-size: 12px; color: #333; margin-bottom: 6px;">
                            容量: ${inventoryItems.length}/${agent.max_grasp_limit || 1}
                            ${agent.properties && agent.properties.max_weight ? ` | 最大承重: ${agent.properties.max_weight}kg` : ''}
                        </div>
                        ${inventoryDetails.length > 0 ? `
                            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;">
                                ${inventoryDetails.map(item => `
                                    <div style="background: ${item.properties && item.properties.provides_abilities ? '#ffcc80' : '#e3f2fd'};
                                                color: ${item.properties && item.properties.provides_abilities ? '#e65100' : '#1976d2'};
                                                padding: 4px 8px; border-radius: 12px; font-size: 11px; cursor: pointer;"
                                         onclick="selectObject('${item.id}')">
                                        ${item.properties && item.properties.provides_abilities ? '🔧' : '📦'} ${item.name}
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<div style="color: #999; font-size: 11px;">库存为空</div>'}
                    </div>

                    <div style="margin-bottom: 12px;">
                        <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 2px;">⚡ 能力信息</h4>
                        ${abilities.length > 0 ? `
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                                ${abilities.map(ability => `
                                    <span style="background: #e8f5e8; color: #2e7d32; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">
                                        ${ability}
                                    </span>
                                `).join('')}
                            </div>
                        ` : '<div style="color: #999; font-size: 11px;">暂无特殊能力</div>'}
                    </div>

                    ${agent.corporate_mode_object_id ? `
                        <div style="margin-bottom: 12px;">
                            <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 2px;">🤝 合作状态</h4>
                            <div style="background: #fff3e0; padding: 8px; border-radius: 6px; border-left: 4px solid #ff9800;">
                                <div style="font-size: 12px; color: #f57c00; font-weight: 500;">正在合作搬运</div>
                                <div style="font-size: 11px; color: #333; margin-top: 2px;">目标物体: ${agent.corporate_mode_object_id}</div>
                            </div>
                        </div>
                    ` : ''}

                    ${agent.properties ? `
                        <div>
                            <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 2px;">🔧 属性信息</h4>
                            <div style="font-size: 11px; color: #666; line-height: 1.4;">
                                ${Object.entries(agent.properties).map(([key, value]) => `
                                    <div><strong>${key}:</strong> ${JSON.stringify(value)}</div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        function updateEnvironmentInfo(data) {
            // 更新环境统计
            const environmentStats = document.getElementById('environmentStats');
            if (!environmentStats) return;

            environmentStats.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px;">
                    <div style="text-align: center; padding: 8px; background: #e3f2fd; border-radius: 4px;">
                        <div style="font-size: 16px; font-weight: 600; color: #1976d2;">${data.rooms.length}</div>
                        <div style="font-size: 10px; color: #666;">房间</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: #e8f5e8; border-radius: 4px;">
                        <div style="font-size: 16px; font-weight: 600; color: #2e7d32;">${data.agents.length}</div>
                        <div style="font-size: 10px; color: #666;">智能体</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: #fff3e0; border-radius: 4px;">
                        <div style="font-size: 16px; font-weight: 600; color: #f57c00;">${data.objects.length}</div>
                        <div style="font-size: 10px; color: #666;">物体</div>
                    </div>
                </div>
            `;

            // 更新房间列表
            const roomList = document.getElementById('roomList');
            if (!roomList) return;

            roomList.innerHTML = data.rooms.map(room =>
                `<div class="room-item" onclick="selectRoom('${room.id}')" data-room-id="${room.id}" style="padding: 8px; margin: 4px 0; background: #f8f9fa; border-radius: 4px; cursor: pointer; border-left: 3px solid #2196f3; transition: all 0.2s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #333; margin-bottom: 2px; font-size: 12px;">🏠 ${room.name}</div>
                            <div style="font-size: 10px; color: #666;">${room.type}</div>
                        </div>
                        <div style="text-align: right; font-size: 10px; color: #666;">
                            <div>物体: ${room.objects_count}</div>
                            <div>智能体: ${room.agents_count}</div>
                        </div>
                    </div>
                </div>`
            ).join('');

            // 更新智能体列表
            const agentList = document.getElementById('agentList');
            if (!agentList) return;

            agentList.innerHTML = data.agents.map(agent =>
                `<div class="agent-item" onclick="focusAgent('${agent.id}')" style="padding: 8px; margin: 4px 0; background: #f8f9fa; border-radius: 4px; cursor: pointer; border-left: 3px solid #4caf50; transition: all 0.2s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #333; margin-bottom: 2px; font-size: 12px;">🤖 ${agent.name}</div>
                            <div style="font-size: 10px; color: #666;">${agent.location}</div>
                        </div>
                        <div style="text-align: right; font-size: 10px; color: #666;">
                            <div>${agent.status}</div>
                            <div>库存: ${agent.inventory.length}</div>
                        </div>
                    </div>
                </div>`
            ).join('');


        }









        // 切换类别展开/折叠状态
        function toggleCategory(categoryId) {
            const categoryDiv = document.getElementById('category-' + categoryId);
            const toggleIcon = document.getElementById('toggle-' + categoryId);

            if (categoryDiv && toggleIcon) {
                const isVisible = categoryDiv.style.display !== 'none';
                categoryDiv.style.display = isVisible ? 'none' : 'block';
                toggleIcon.textContent = isVisible ? '▶' : '▼';
                toggleIcon.style.transform = isVisible ? 'rotate(0deg)' : 'rotate(90deg)';
            }
        }

        function updateStatus(message) {
            const statusElement = document.getElementById('status');
            if (statusElement) {
                statusElement.innerHTML = message;
            }
        }

        function selectRoom(roomId) {
            // 更新UI选中状态
            document.querySelectorAll('.room-item').forEach(item => {
                item.classList.remove('selected');
                item.style.borderLeftColor = '#2196f3';
            });
            const selectedRoom = document.querySelector(`[data-room-id="${roomId}"]`);
            if (selectedRoom) {
                selectedRoom.classList.add('selected');
                selectedRoom.style.borderLeftColor = '#ff9800';
            }

            // 更新可视化
            if (visualization) {
                visualization.selectRoom(roomId);
            }
        }

        function focusAgent(agentId) {
            if (!currentData || !currentData.agents) return;

            const agent = currentData.agents.find(a => a.id === agentId);
            if (agent) {
                // 高亮智能体所在房间
                selectRoom(agent.location);

                // 在可视化中聚焦到智能体
                if (visualization) {
                    visualization.focusAgent(agentId);
                }
            }
        }

        function selectObject(obj) {
            // 更新物体详情显示
            showObjectDetails(obj);

            // 如果物体在某个房间，也选中该房间
            const roomId = findObjectRoom(obj);
            if (roomId) {
                selectRoom(roomId);
            }
        }

        function findObjectRoom(obj) {
            if (!obj.layout_info) return null;

            if (obj.layout_info.is_root_level) {
                return obj.layout_info.parent_id;
            }

            // 递归查找根房间
            if (currentData && currentData.objects) {
                const parentObj = currentData.objects.find(o => o.id === obj.layout_info.parent_id);
                if (parentObj) {
                    return findObjectRoom(parentObj);
                }
            }

            return obj.layout_info.parent_id;
        }

        function showObjectDetails(obj) {
            const detailsPanel = document.getElementById('objectDetails');
            if (!detailsPanel) return;

            // 获取包含的物体
            const containedObjects = obj.contained_objects ?
                obj.contained_objects.map(id => currentData.objects.find(o => o.id === id)).filter(o => o) : [];

            const containerInfo = obj.container_info || {};
            const typeIcon = obj.is_tool ? '🔧' : (obj.type === 'FURNITURE' ? '🪑' : '📦');
            const borderColor = obj.is_tool ? '#ff9800' : (obj.type === 'FURNITURE' ? '#8d6e63' : '#2196f3');

            detailsPanel.innerHTML = `
                <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid ${borderColor};">
                    <h4 style="margin: 0 0 15px 0; color: #333; font-size: 16px; display: flex; align-items: center; gap: 8px;">
                        ${typeIcon} ${obj.name}
                        <span style="font-size: 11px; background: ${borderColor}; color: white; padding: 2px 6px; border-radius: 10px; font-weight: normal;">
                            ${obj.type}
                        </span>
                    </h4>

                    <div style="font-size: 13px; line-height: 1.5; margin-bottom: 15px;">
                        <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 12px; align-items: start;">
                            <strong>ID:</strong> <span style="font-family: monospace; font-size: 11px; background: #e9ecef; padding: 2px 4px; border-radius: 3px;">${obj.id}</span>
                            <strong>位置:</strong> <span>${obj.location?.type || 'unknown'} ${obj.location?.target || ''}</span>
                            ${containerInfo.is_contained ? `
                                <strong>容器:</strong> <span>${containerInfo.relation_type} ${containerInfo.container_name}</span>
                            ` : ''}
                            ${obj.provides_abilities && obj.provides_abilities.length > 0 ? `
                                <strong>提供能力:</strong> <span>${obj.provides_abilities.join(', ')}</span>
                            ` : ''}
                            ${containedObjects.length > 0 ? `
                                <strong>包含物体:</strong> <span>${containedObjects.length} 项</span>
                            ` : ''}
                        </div>
                    </div>

                    ${obj.states && Object.keys(obj.states).length > 0 ? `
                        <div style="margin-bottom: 15px; padding: 10px; background: rgba(33,150,243,0.1); border-radius: 6px;">
                            <strong style="font-size: 12px; color: #666; display: block; margin-bottom: 6px;">状态信息:</strong>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 4px;">
                                ${Object.entries(obj.states).map(([key, value]) => `
                                    <div style="font-size: 11px; background: white; padding: 4px 6px; border-radius: 3px; border-left: 3px solid #2196f3;">
                                        <strong>${key}:</strong> ${value}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    ${obj.properties && Object.keys(obj.properties).length > 0 ? `
                        <div style="margin-bottom: 15px; padding: 10px; background: rgba(76,175,80,0.1); border-radius: 6px;">
                            <strong style="font-size: 12px; color: #666; display: block; margin-bottom: 6px;">属性信息:</strong>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 4px;">
                                ${Object.entries(obj.properties).map(([key, value]) => `
                                    <div style="font-size: 11px; background: white; padding: 4px 6px; border-radius: 3px; border-left: 3px solid #4caf50;">
                                        <strong>${key}:</strong> ${typeof value === 'object' ? JSON.stringify(value) : value}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    ${containedObjects.length > 0 ? `
                        <div style="margin-bottom: 15px; padding: 10px; background: rgba(255,152,0,0.1); border-radius: 6px;">
                            <strong style="font-size: 12px; color: #666; display: block; margin-bottom: 8px;">包含的物体 (${containedObjects.length}):</strong>
                            <div style="max-height: 150px; overflow-y: auto;">
                                ${containedObjects.map(cObj => {
                                    const cTypeIcon = cObj.is_tool ? '🔧' : (cObj.type === 'FURNITURE' ? '🪑' : '📦');
                                    const cBorderColor = cObj.is_tool ? '#ff9800' : (cObj.type === 'FURNITURE' ? '#8d6e63' : '#2196f3');
                                    return `
                                        <div onclick="selectObject(currentData.objects.find(o => o.id === '${cObj.id}'))" style="margin: 4px 0; padding: 6px 8px; background: white; border-radius: 4px; cursor: pointer; border-left: 3px solid ${cBorderColor}; transition: background-color 0.2s ease;">
                                            <div style="font-size: 12px; font-weight: 500; color: #333; margin-bottom: 2px;">
                                                ${cTypeIcon} ${cObj.name}
                                            </div>
                                            <div style="font-size: 10px; color: #666;">
                                                ${cObj.type} | ${cObj.location?.type || 'unknown'}
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <div style="font-size: 11px; color: #999; font-style: italic; text-align: center; padding-top: 10px; border-top: 1px solid #e0e0e0;">
                        💡 点击地图上的其他物体或房间查看详情
                    </div>
                </div>
            `;
        }



        function startDataUpdates() {
            loadData(); // 立即加载一次，定时器会在loadData中设置
        }

        function stopDataUpdates() {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }

        // 控制函数
        function resetView() {
            if (visualization) {
                visualization.fitToContent();
            }
        }



        // 页面卸载时清理
        window.addEventListener('beforeunload', function() {
            stopDataUpdates();
        });
    </script>

    <!-- 外部可视化JavaScript -->
    <script src="/static/visualization.js"></script>
    <script>
        // 页面特定的JavaScript代码
        // SimulatorVisualization类已在外部文件中定义
    </script>
</body>
</html>"""


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """支持多线程的HTTP服务器"""
    daemon_threads = True



class VisualizationWebServer:
    """可视化Web服务器"""

    def __init__(self, data_provider, config: Optional[Dict] = None):
        """
        初始化Web服务器

        Args:
            data_provider: 数据提供器
            config: 服务器配置
        """
        self.data_provider = data_provider
        self.config = config or {}
        self.server = None
        self.server_thread = None
        self.running = False

        # 服务器配置
        self.host = self.config.get('web_server', {}).get('host', 'localhost')
        self.port = self.config.get('web_server', {}).get('port', 8080)
        self.auto_open_browser = self.config.get('web_server', {}).get('auto_open_browser', True)

    def start(self):
        """启动Web服务器"""
        if self.running:
            logging.warning("Web服务器已在运行")
            return

        try:
            # 创建请求处理器类
            handler_class = lambda *args, **kwargs: VisualizationRequestHandler(
                *args, data_provider=self.data_provider, config=self.config, **kwargs
            )

            # 创建服务器
            self.server = ThreadingHTTPServer((self.host, self.port), handler_class)

            # 在单独线程中运行服务器
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

            self.running = True

            server_url = f"http://{self.host}:{self.port}"
            logging.info(f"可视化Web服务器已启动: {server_url}")

            # 自动打开浏览器
            if self.auto_open_browser:
                try:
                    webbrowser.open(server_url)
                    logging.info("已自动打开浏览器")
                except Exception as e:
                    logging.warning(f"无法自动打开浏览器: {e}")

        except Exception as e:
            logging.error(f"启动Web服务器失败: {e}")
            raise

    def stop(self):
        """停止Web服务器"""
        if not self.running:
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()

            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)

            self.running = False
            logging.info("可视化Web服务器已停止")

        except Exception as e:
            logging.error(f"停止Web服务器失败: {e}")

    def _run_server(self):
        """运行服务器的内部方法"""
        try:
            self.server.serve_forever()
        except Exception as e:
            if self.running:  # 只有在应该运行时才记录错误
                logging.error(f"Web服务器运行错误: {e}")

    def is_running(self) -> bool:
        """检查服务器是否在运行"""
        return self.running

    def get_server_url(self) -> str:
        """获取服务器URL"""
        return f"http://{self.host}:{self.port}"
