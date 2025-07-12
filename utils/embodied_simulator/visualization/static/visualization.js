/**
 * 模拟器可视化前端JavaScript
 * 使用嵌套Box布局展示物品关系
 */

class SimulatorVisualization {
    constructor(canvasId, config = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // 合并外部配置和默认配置
        this.config = {
            gridSize: 20,
            roomColors: {
                'industrial': '#e8f4fd',
                'storage': '#f8e8ff',
                'workshop': '#fff8f0',
                'server_room': '#f0f8f0',
                'default': '#fafafa'
            },
            objectColors: {
                'FURNITURE': '#d7ccc8',  // 浅棕色 - 家具
                'ITEM': '#bbdefb',      // 浅蓝色 - 物品
                'AGENT': '#c8e6c9',     // 浅绿色 - 智能体
                'TOOL': '#ffcc80'       // 浅橙色 - 工具
            },
            relationColors: {
                'in': '#4caf50',        // 绿色边框表示"在...内"
                'on': '#2196f3',        // 蓝色边框表示"在...上"
                'default': '#757575'    // 中灰色
            },
            selectedColors: {
                background: '#fff3e0',  // 浅橙色背景
                border: '#ff9800',      // 橙色边框
                text: '#e65100'         // 深橙色文字
            },
            // 布局配置 - 可泛化的通用配置
            layout: {
                // 房间配置
                roomPadding: 30,
                minRoomSize: 400,
                roomMargin: 120,
                maxRoomCols: 2,
                roomHeaderHeight: 100,
                roomAspectRatio: {
                    min: 0.7,  // 最小长宽比（高度不超过宽度的1.43倍）
                    max: 2.2   // 最大长宽比（宽度不超过高度的2.2倍）
                },

                // 物体配置
                objectPadding: 15,
                minObjectSize: 120,
                maxObjectSize: 180,
                objectHeaderHeight: 35,
                objectAspectRatio: {
                    min: 0.5,  // 最小长宽比（高度不超过宽度的2倍）
                    max: 3.0   // 最大长宽比（宽度不超过高度的3倍）
                },

                // 智能体配置
                agentAreaWidth: 80,
                agentSize: 65,
                agentRadius: 30,
                agentMargin: 20,

                // 字体配置
                fontSize: 12,
                titleFontSize: 14,
                headerHeight: 45,

                // 列数计算配置
                columnRules: {
                    room: [
                        { maxObjects: 2, cols: 'actual' },      // 1-2个物体：按实际数量
                        { maxObjects: 4, cols: 2 },             // 3-4个物体：2列
                        { maxObjects: 9, cols: 3 },             // 5-9个物体：3列
                        { maxObjects: 16, cols: 4 },            // 10-16个物体：4列
                        { maxObjects: Infinity, cols: 5 }       // 17+个物体：5列
                    ],
                    object: [
                        { maxObjects: 2, cols: 'actual' },      // 1-2个物体：按实际数量
                        { maxObjects: 4, cols: 2 },             // 3-4个物体：2列
                        { maxObjects: 9, cols: 3 },             // 5-9个物体：3列
                        { maxObjects: Infinity, cols: 4 }       // 10+个物体：4列
                    ]
                }
            },
            ...config
        };

        this.data = null;
        this.selectedRoom = null;
        this.selectedObject = null;
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isDragging = false;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
        this.objectPositions = new Map(); // 存储物体位置信息
        this.roomPositions = null; // 缓存房间位置

        this.setupCanvas();
        this.setupEventListeners();
    }



    setupCanvas() {
        // 设置Canvas尺寸
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;

        // 高DPI支持
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
    }

    setupEventListeners() {
        // 鼠标事件
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.onWheel(e));
        this.canvas.addEventListener('click', (e) => this.onClick(e));
        this.canvas.addEventListener('mouseleave', (e) => this.onMouseLeave(e));

        // 窗口大小变化
        window.addEventListener('resize', () => this.setupCanvas());


        this.selectedAgent = null;
    }

    updateData(newData) {
        const isFirstLoad = !this.data;
        this.data = newData;
        this.roomPositions = null; // 清除缓存
        this.render();

        // 首次加载数据时自动适应内容
        if (isFirstLoad && this.data && this.data.rooms && this.data.rooms.length > 0) {
            // 延迟执行以确保渲染完成
            setTimeout(() => {
                this.fitToContent();
            }, 100);
        }
    }

    render() {
        if (!this.data) return;

        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 保存变换状态
        this.ctx.save();
        this.ctx.translate(this.offsetX, this.offsetY);
        this.ctx.scale(this.scale, this.scale);

        // 绘制网格
        this.drawGrid();

        // 绘制房间
        this.drawRooms();

        // 绘制连接线 - 暂时禁用以减少视觉混乱
        // this.drawConnections();

        // 绘制物体
        this.drawObjects();

        // 绘制智能体
        this.drawAgents();

        // 恢复变换状态
        this.ctx.restore();

        // 绘制UI元素（不受变换影响）
        this.drawUI();
    }

    drawGrid() {
        const gridSize = this.config.gridSize;
        const width = this.canvas.width / this.scale;
        const height = this.canvas.height / this.scale;

        this.ctx.strokeStyle = '#e0e0e0';
        this.ctx.lineWidth = 0.5;

        // 垂直线
        for (let x = 0; x < width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, height);
            this.ctx.stroke();
        }

        // 水平线
        for (let y = 0; y < height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(width, y);
            this.ctx.stroke();
        }
    }

    drawRooms() {
        if (!this.data.rooms) return;

        const roomPositions = this.calculateRoomPositions();

        this.data.rooms.forEach((room) => {
            const pos = roomPositions[room.id];
            if (!pos) return;

            // 房间背景
            const isRoomSelected = this.selectedRoom === room.id;
            const color = this.config.roomColors[room.type] || this.config.roomColors.default;
            this.ctx.fillStyle = isRoomSelected ? '#e3f2fd' : color;
            this.ctx.fillRect(pos.x, pos.y, pos.width, pos.height);

            // 房间边框
            this.ctx.strokeStyle = isRoomSelected ? '#1976d2' : '#bdbdbd';
            this.ctx.lineWidth = isRoomSelected ? 3 : 1;
            this.ctx.strokeRect(pos.x, pos.y, pos.width, pos.height);

            // 房间标题 - 支持换行
            this.ctx.fillStyle = isRoomSelected ? '#1565c0' : '#212121';
            this.ctx.font = 'bold 18px Arial';
            this.ctx.textAlign = 'center';

            // 使用换行绘制房间标题
            const maxTitleWidth = pos.width - 40;
            const titleLines = this.wrapText(room.name, maxTitleWidth, 'bold 18px Arial');
            let titleY = pos.y + 30;

            titleLines.forEach((line, index) => {
                if (index < 2) { // 最多显示2行标题
                    this.ctx.fillText(line, pos.x + pos.width / 2, titleY);
                    titleY += 22;
                }
            });

            // 房间信息 - 增大字体，修正计数
            this.ctx.font = '14px Arial';
            this.ctx.fillStyle = isRoomSelected ? '#1565c0' : '#424242';
            const objectsInRoom = this.countObjectsInRoom(room.id);
            const agentsInRoom = this.countAgentsInRoom(room.id);
            this.ctx.fillText(`物体: ${objectsInRoom} | 智能体: ${agentsInRoom}`,
                pos.x + pos.width / 2, titleY + 10);
        });
    }

    calculateRoomPositions() {
        // 使用缓存避免重复计算
        if (this.roomPositions) {
            return this.roomPositions;
        }

        const positions = {};
        const minRoomSize = this.config.layout.minRoomSize;
        const margin = this.config.layout.roomMargin;
        const cols = Math.min(this.config.layout.maxRoomCols, Math.ceil(Math.sqrt(this.data.rooms.length)));

        // 首先计算每个房间需要的实际大小
        const roomSizes = {};
        this.data.rooms.forEach(room => {
            const requiredSize = this.calculateRequiredRoomSize(room.id);
            roomSizes[room.id] = {
                width: Math.max(minRoomSize, requiredSize.width),
                height: Math.max(minRoomSize, requiredSize.height)
            };
        });

        // 计算总布局尺寸以便居中
        let totalLayoutWidth = 0;
        let totalLayoutHeight = 0;
        let currentRowWidth = 0;
        let currentRowHeight = 0;
        let roomsInCurrentRow = 0;

        // 第一遍：计算总布局尺寸
        this.data.rooms.forEach((room) => {
            const roomSize = roomSizes[room.id];

            // 检查是否需要换行
            if (roomsInCurrentRow >= cols) {
                totalLayoutWidth = Math.max(totalLayoutWidth, currentRowWidth - margin);
                totalLayoutHeight += currentRowHeight + margin;
                currentRowWidth = 0;
                currentRowHeight = 0;
                roomsInCurrentRow = 0;
            }

            currentRowWidth += roomSize.width + margin;
            currentRowHeight = Math.max(currentRowHeight, roomSize.height);
            roomsInCurrentRow++;
        });

        // 处理最后一行
        totalLayoutWidth = Math.max(totalLayoutWidth, currentRowWidth - margin);
        totalLayoutHeight += currentRowHeight;

        // 计算居中偏移量（基于画布的逻辑尺寸）
        const canvasLogicalWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasLogicalHeight = this.canvas.height / (window.devicePixelRatio || 1);
        const offsetX = Math.max(margin, (canvasLogicalWidth - totalLayoutWidth) / 2);
        const offsetY = Math.max(margin, (canvasLogicalHeight - totalLayoutHeight) / 2);

        // 第二遍：计算实际位置（居中）
        let currentY = offsetY;
        currentRowHeight = 0;
        let currentX = offsetX;
        roomsInCurrentRow = 0;

        this.data.rooms.forEach((room) => {
            const roomSize = roomSizes[room.id];

            // 检查是否需要换行
            if (roomsInCurrentRow >= cols) {
                currentY += currentRowHeight + margin;
                currentX = offsetX;
                currentRowHeight = 0;
                roomsInCurrentRow = 0;
            }

            positions[room.id] = {
                x: currentX,
                y: currentY,
                width: roomSize.width,
                height: roomSize.height
            };

            currentX += roomSize.width + margin;
            currentRowHeight = Math.max(currentRowHeight, roomSize.height);
            roomsInCurrentRow++;
        });

        // 缓存结果
        this.roomPositions = positions;
        return positions;
    }

    // 通用的列数计算函数
    calculateOptimalColumns(objectCount, type = 'object') {
        const rules = this.config.layout.columnRules[type] || this.config.layout.columnRules.object;

        for (const rule of rules) {
            if (objectCount <= rule.maxObjects) {
                return rule.cols === 'actual' ? objectCount : rule.cols;
            }
        }

        // 默认回退
        return Math.min(4, Math.ceil(Math.sqrt(objectCount)));
    }

    // 通用的长宽比优化函数
    optimizeAspectRatio(width, height, type = 'object') {
        const aspectRatioConfig = type === 'room'
            ? this.config.layout.roomAspectRatio
            : this.config.layout.objectAspectRatio;

        const aspectRatio = width / height;
        let finalWidth = width;
        let finalHeight = height;

        if (aspectRatio < aspectRatioConfig.min) {
            // 太高了，增加宽度
            finalWidth = finalHeight * aspectRatioConfig.min;
        } else if (aspectRatio > aspectRatioConfig.max) {
            // 太宽了，增加高度
            finalHeight = finalWidth / aspectRatioConfig.max;
        }

        return {
            width: Math.round(finalWidth),
            height: Math.round(finalHeight)
        };
    }

    calculateRequiredRoomSize(roomId) {
        // 计算房间内容所需的实际空间
        const padding = this.config.layout.roomPadding;
        const headerHeight = this.config.layout.roomHeaderHeight;

        // 动态计算智能体区域宽度
        const agentsInRoom = this.data.agents ? this.data.agents.filter(a => a.location === roomId) : [];
        const agentAreaWidth = agentsInRoom.length > 0 ? this.config.layout.agentAreaWidth : 0;

        // 获取房间内的根级物体
        const roomObjects = this.data.objects.filter(obj => {
            const rootRoom = this.findObjectRootRoom(obj);
            return rootRoom === roomId && obj.layout_info && obj.layout_info.is_root_level;
        });

        if (roomObjects.length === 0) {
            // 空房间使用配置的最小尺寸和合理的长宽比
            const minSize = this.config.layout.minRoomSize;
            return this.optimizeAspectRatio(minSize, Math.round(minSize * 0.75), 'room');
        }

        // 计算所有物体的布局需求
        const objectLayouts = roomObjects.map(obj => this.calculateObjectLayout(obj));
        const objectCount = objectLayouts.length;

        // 使用通用的列数计算函数
        const idealCols = this.calculateOptimalColumns(objectCount, 'room');

        // 计算每列的平均宽度
        const avgObjectWidth = objectLayouts.reduce((sum, layout) => sum + layout.width, 0) / objectCount;

        // 计算理想的房间宽度（基于列数和平均物体宽度）
        const idealWidth = idealCols * avgObjectWidth + (idealCols + 1) * this.config.layout.objectPadding;

        // 使用流式布局计算实际所需空间
        let totalHeight = headerHeight;
        let currentRowWidth = 0;
        let currentRowHeight = 0;
        let maxRowWidth = 0;
        const maxRowWidthLimit = Math.max(idealWidth, 350); // 使用理想宽度作为换行基准，降低最小值

        objectLayouts.forEach(layout => {
            // 检查是否需要换行
            if (currentRowWidth + layout.width > maxRowWidthLimit) {
                // 换行
                maxRowWidth = Math.max(maxRowWidth, currentRowWidth);
                totalHeight += currentRowHeight + this.config.layout.objectPadding;
                currentRowWidth = layout.width + this.config.layout.objectPadding;
                currentRowHeight = layout.height;
            } else {
                currentRowWidth += layout.width + this.config.layout.objectPadding;
                currentRowHeight = Math.max(currentRowHeight, layout.height);
            }
        });

        // 处理最后一行
        maxRowWidth = Math.max(maxRowWidth, currentRowWidth);
        totalHeight += currentRowHeight;

        // 计算最终尺寸，确保合理的长宽比
        const minRoomSize = this.config.layout.minRoomSize;
        let finalWidth = Math.max(minRoomSize, maxRowWidth + padding * 2 + agentAreaWidth);
        let finalHeight = Math.max(Math.round(minRoomSize * 0.75), totalHeight + padding * 2);

        // 使用通用的长宽比优化函数
        return this.optimizeAspectRatio(finalWidth, finalHeight, 'room');
    }

    countObjectsInRoom(roomId) {
        if (!this.data.objects) return 0;
        return this.data.objects.filter(obj => {
            const rootRoom = this.findObjectRootRoom(obj);
            return rootRoom === roomId;
        }).length;
    }

    countAgentsInRoom(roomId) {
        if (!this.data.agents) return 0;
        return this.data.agents.filter(agent => (agent.location || agent.location_id) === roomId).length;
    }

    drawConnections() {
        if (!this.data.rooms) return;

        const roomPositions = this.calculateRoomPositions();

        this.ctx.strokeStyle = '#9e9e9e';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);

        this.data.rooms.forEach(room => {
            const fromPos = roomPositions[room.id];
            if (!fromPos) return;

            room.connected_rooms.forEach(connectedRoomId => {
                const toPos = roomPositions[connectedRoomId];
                if (!toPos) return;

                // 绘制连接线
                this.ctx.beginPath();
                this.ctx.moveTo(fromPos.x + fromPos.width / 2, fromPos.y + fromPos.height / 2);
                this.ctx.lineTo(toPos.x + toPos.width / 2, toPos.y + toPos.height / 2);
                this.ctx.stroke();
            });
        });

        this.ctx.setLineDash([]);
    }

    drawObjects() {
        if (!this.data.objects) return;

        const roomPositions = this.calculateRoomPositions();
        this.objectPositions.clear();

        // 按房间分组物体
        const objectsByRoom = this.groupObjectsByRoom();

        // 为每个房间绘制物体层次结构
        Object.entries(objectsByRoom).forEach(([roomId, roomObjects]) => {
            const roomPos = roomPositions[roomId];
            if (!roomPos) return;

            this.drawRoomObjects(roomPos, roomObjects);
        });
    }

    groupObjectsByRoom() {
        const objectsByRoom = {};

        this.data.objects.forEach(obj => {
            // 过滤掉智能体类型的对象，避免重复绘制
            if (obj.type === 'AGENT') return;

            // 找到物体所在的根房间
            const roomId = this.findObjectRootRoom(obj);
            if (!roomId) return;

            if (!objectsByRoom[roomId]) {
                objectsByRoom[roomId] = [];
            }

            // 只添加直接在房间内的物体（根级物体）
            if (obj.layout_info && obj.layout_info.is_root_level) {
                objectsByRoom[roomId].push(obj);
            }
        });

        return objectsByRoom;
    }

    findObjectRootRoom(obj) {
        if (!obj.layout_info) return null;

        if (obj.layout_info.is_root_level) {
            return obj.layout_info.parent_id;
        }

        // 递归查找根房间
        const parentObj = this.data.objects.find(o => o.id === obj.layout_info.parent_id);
        if (parentObj) {
            return this.findObjectRootRoom(parentObj);
        }

        return obj.layout_info.parent_id;
    }

    drawRoomObjects(roomPos, objects) {
        if (!objects.length) return;

        // 动态计算智能体占用的空间
        const padding = this.config.layout.roomPadding;
        const agentsInRoom = this.data.agents ? this.data.agents.filter(a => a.location === this.getRoomIdFromPosition(roomPos)) : [];
        const agentAreaWidth = agentsInRoom.length > 0 ? this.config.layout.agentAreaWidth : 0;

        let currentX = roomPos.x + padding + agentAreaWidth;
        let currentY = roomPos.y + this.config.layout.roomHeaderHeight;
        let rowHeight = 0;

        objects.forEach(obj => {
            const objLayout = this.calculateObjectLayout(obj);

            // 检查是否需要换行
            if (currentX + objLayout.width > roomPos.x + roomPos.width - padding) {
                currentX = roomPos.x + padding;
                currentY += rowHeight + this.config.layout.objectPadding;
                rowHeight = 0;
            }

            // 绘制物体及其嵌套内容
            this.drawObjectHierarchy(obj, currentX, currentY, objLayout);

            // 更新位置
            currentX += objLayout.width + this.config.layout.objectPadding;
            rowHeight = Math.max(rowHeight, objLayout.height);
        });
    }

    calculateObjectLayout(obj) {
        // 计算物体及其嵌套内容所需的布局空间
        const minSize = this.config.layout.minObjectSize;
        const padding = this.config.layout.objectPadding;
        const headerHeight = this.config.layout.objectHeaderHeight;

        // 获取包含的物体
        const containedObjects = this.getContainedObjects(obj);

        if (containedObjects.length === 0) {
            // 没有嵌套物体，使用最小尺寸，但确保合理的长宽比
            return {
                width: minSize,
                height: minSize
            };
        }

        // 递归计算所有嵌套物体的布局
        const nestedLayouts = containedObjects.map(nestedObj =>
            this.calculateObjectLayout(nestedObj)
        );

        // 使用通用的列数计算函数
        const objectCount = containedObjects.length;
        const idealCols = this.calculateOptimalColumns(objectCount, 'object');

        const rows = Math.ceil(objectCount / idealCols);

        // 计算每列的最大宽度和每行的最大高度
        const colWidths = new Array(idealCols).fill(0);
        const rowHeights = new Array(rows).fill(0);

        nestedLayouts.forEach((layout, index) => {
            const col = index % idealCols;
            const row = Math.floor(index / idealCols);
            colWidths[col] = Math.max(colWidths[col], layout.width);
            rowHeights[row] = Math.max(rowHeights[row], layout.height);
        });

        // 计算总的内容区域尺寸
        const contentWidth = colWidths.reduce((sum, width) => sum + width, 0) +
            (idealCols - 1) * padding;
        const contentHeight = rowHeights.reduce((sum, height) => sum + height, 0) +
            (rows - 1) * padding;

        // 容器需要足够大来容纳标题和所有嵌套物体
        let containerWidth = Math.max(minSize, contentWidth + padding * 2);
        let containerHeight = Math.max(minSize, contentHeight + headerHeight + padding * 2);

        // 使用通用的长宽比优化函数
        const optimizedSize = this.optimizeAspectRatio(containerWidth, containerHeight, 'object');

        return {
            width: optimizedSize.width,
            height: optimizedSize.height,
            contentLayout: {
                cols: idealCols,
                rows,
                colWidths,
                rowHeights,
                contentWidth,
                contentHeight
            }
        };
    }

    getContainedObjects(containerObj) {
        if (!containerObj.contained_objects) return [];

        return containerObj.contained_objects.map(id =>
            this.data.objects.find(obj => obj.id === id)
        ).filter(obj => obj);
    }

    drawObjectHierarchy(obj, x, y, layout) {
        // 绘制容器物体本身
        this.drawObjectBox(obj, x, y, layout.width, layout.height);

        // 记录物体位置
        this.objectPositions.set(obj.id, { x, y, width: layout.width, height: layout.height });

        // 绘制包含的物体
        const containedObjects = this.getContainedObjects(obj);
        if (containedObjects.length > 0) {
            this.drawContainedObjectsInBox(containedObjects, x, y, layout.width, layout.height, layout);
        }
    }

    drawObjectBox(obj, x, y, width, height) {
        const isSelected = this.selectedObject === obj.id;

        // 选择填充颜色
        let fillColor = this.config.objectColors[obj.type] || '#f5f5f5';
        if (obj.is_tool) {
            fillColor = this.config.objectColors.TOOL;
        }

        // 绘制背景
        this.ctx.fillStyle = isSelected ? this.config.selectedColors.background : fillColor;
        this.ctx.fillRect(x, y, width, height);

        // 选择边框颜色 - 根据关系类型
        let borderColor = this.config.relationColors.default;
        if (isSelected) {
            borderColor = this.config.selectedColors.border;
        } else if (obj.relation_type) {
            borderColor = this.config.relationColors[obj.relation_type] || this.config.relationColors.default;
        }

        // 绘制边框
        this.ctx.strokeStyle = borderColor;
        this.ctx.lineWidth = isSelected ? 3 : 2;
        this.ctx.strokeRect(x, y, width, height);

        // 绘制物体标题
        this.ctx.fillStyle = isSelected ? this.config.selectedColors.text : '#212121';
        this.ctx.font = `bold ${this.config.layout.titleFontSize}px Arial`;
        this.ctx.textAlign = 'left';

        let title = obj.name;
        if (obj.is_tool) {
            title = '🔧 ' + title;
        }

        // 使用换行绘制标题
        const maxTitleWidth = width - 8;
        const titleLines = this.wrapText(title, maxTitleWidth, `bold ${this.config.layout.titleFontSize}px Arial`);
        let currentY = y + 18;

        titleLines.forEach((line, index) => {
            if (index < 2) { // 最多显示2行标题
                this.ctx.fillText(line, x + 4, currentY);
                currentY += this.config.layout.titleFontSize + 2;
            }
        });

        // 显示物体类型
        this.ctx.font = `${this.config.layout.fontSize}px Arial`;
        this.ctx.fillStyle = isSelected ? this.config.selectedColors.text : '#424242';

        const typeLines = this.wrapText(obj.type, maxTitleWidth, `${this.config.layout.fontSize}px Arial`);
        typeLines.forEach((line, index) => {
            if (index < 1) { // 类型只显示1行
                this.ctx.fillText(line, x + 4, currentY);
                currentY += this.config.layout.fontSize + 2;
            }
        });
    }

    drawContainedObjectsInBox(containedObjects, containerX, containerY, containerWidth, containerHeight, parentLayout) {
        const padding = this.config.layout.objectPadding;
        const headerHeight = this.config.layout.objectHeaderHeight;

        // 使用父容器的布局信息进行精确定位
        if (!parentLayout || !parentLayout.contentLayout) {
            // 回退到简单布局
            this.drawContainedObjectsSimple(containedObjects, containerX, containerY, containerWidth, containerHeight);
            return;
        }

        const { cols, colWidths, rowHeights } = parentLayout.contentLayout;

        containedObjects.forEach((obj, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);

            // 计算精确位置
            let objX = containerX + padding;
            for (let c = 0; c < col; c++) {
                objX += colWidths[c] + padding;
            }

            let objY = containerY + headerHeight + padding;
            for (let r = 0; r < row; r++) {
                objY += rowHeights[r] + padding;
            }

            // 递归绘制嵌套物体
            const objLayout = this.calculateObjectLayout(obj);
            this.drawObjectHierarchy(obj, objX, objY, objLayout);
        });
    }

    drawContainedObjectsSimple(containedObjects, containerX, containerY, containerWidth) {
        const padding = this.config.layout.objectPadding;
        const headerHeight = this.config.layout.objectHeaderHeight;

        let currentX = containerX + padding;
        let currentY = containerY + headerHeight + padding;
        let rowHeight = 0;

        containedObjects.forEach(obj => {
            const objLayout = this.calculateObjectLayout(obj);

            // 检查是否需要换行
            if (currentX + objLayout.width > containerX + containerWidth - padding) {
                currentX = containerX + padding;
                currentY += rowHeight + padding;
                rowHeight = 0;
            }

            // 递归绘制嵌套物体
            this.drawObjectHierarchy(obj, currentX, currentY, objLayout);

            // 更新位置
            currentX += objLayout.width + padding;
            rowHeight = Math.max(rowHeight, objLayout.height);
        });
    }

    drawAgents() {
        if (!this.data.agents) return;

        const roomPositions = this.calculateRoomPositions();

        this.data.agents.forEach((agent) => {
            const agentLocation = agent.location || agent.location_id;
            const roomPos = roomPositions[agentLocation];
            if (!roomPos) return;

            // 计算智能体在房间内的位置 - 放在房间左上角，紧凑布局
            const margin = this.config.layout.agentMargin;
            const agentSize = this.config.layout.agentSize;

            // 获取同一房间内的所有智能体
            const agentsInRoom = this.data.agents.filter(a => (a.location || a.location_id) === agentLocation);
            const agentIndexInRoom = agentsInRoom.indexOf(agent);

            // 在房间左上角垂直排列智能体，更紧凑
            const agentX = roomPos.x + margin + this.config.layout.agentRadius;
            const agentY = roomPos.y + this.config.layout.roomHeaderHeight + agentIndexInRoom * agentSize;

            this.drawSingleAgent(agent, agentX, agentY);
        });
    }

    drawSingleAgent(agent, x, y) {
        const isSelected = this.selectedAgent === agent.id;

        // 绘制智能体背景圆
        this.ctx.fillStyle = isSelected ? '#c8e6c9' : this.config.objectColors.AGENT;
        this.ctx.beginPath();
        this.ctx.arc(x, y, this.config.layout.agentRadius, 0, 2 * Math.PI);
        this.ctx.fill();

        // 智能体边框 - 选中时使用不同颜色和宽度
        this.ctx.strokeStyle = isSelected ? '#4caf50' : '#2e7d32';
        this.ctx.lineWidth = isSelected ? 4 : 2;
        this.ctx.stroke();

        // 选中时添加外圈高亮
        if (isSelected) {
            this.ctx.strokeStyle = '#81c784';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.arc(x, y, this.config.layout.agentRadius + 6, 0, 2 * Math.PI);
            this.ctx.stroke();
        }

        // 智能体名称显示在圆圈内部
        this.ctx.fillStyle = '#2e7d32';
        this.ctx.font = 'bold 11px Arial';
        this.ctx.textAlign = 'center';

        // 将名称分行显示以适应圆形
        const name = agent.name;
        const lines = this.wrapTextForCircle(name, 50); // 50px是圆形内部可用宽度

        if (lines.length === 1) {
            // 单行显示
            this.ctx.fillText(lines[0], x, y + 4);
        } else if (lines.length === 2) {
            // 两行显示
            this.ctx.fillText(lines[0], x, y - 4);
            this.ctx.fillText(lines[1], x, y + 8);
        } else {
            // 超过两行则显示缩写
            const shortName = name.length > 8 ? name.substring(0, 8) + '...' : name;
            this.ctx.fillText(shortName, x, y + 4);
        }

        // 状态指示器
        if (agent.status !== 'idle') {
            this.ctx.fillStyle = '#ff9800';
            this.ctx.beginPath();
            this.ctx.arc(x + 22, y - 22, 6, 0, 2 * Math.PI);
            this.ctx.fill();

            // 状态边框
            this.ctx.strokeStyle = '#e65100';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
        }

        // 显示持有物品信息 - 优化版本
        if (agent.inventory && agent.inventory.length > 0) {
            this.drawAgentInventory(agent, x, y);
        }
    }

    drawAgentInventory(agent, agentX, agentY) {
        const inventory = agent.inventory || [];
        if (inventory.length === 0) return;

        // 配置
        const radius = this.config.layout.agentRadius;
        const itemSize = 16;
        const itemSpacing = 2;
        const maxItemsPerRow = 3;

        // 计算物品显示区域
        const totalRows = Math.ceil(inventory.length / maxItemsPerRow);
        const inventoryHeight = totalRows * (itemSize + itemSpacing) - itemSpacing;
        const inventoryWidth = Math.min(inventory.length, maxItemsPerRow) * (itemSize + itemSpacing) - itemSpacing;

        // 物品显示位置（在智能体右侧）
        const inventoryX = agentX + radius + 10;
        const inventoryY = agentY - inventoryHeight / 2;

        // 绘制背景框
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        this.ctx.fillRect(inventoryX - 4, inventoryY - 4, inventoryWidth + 8, inventoryHeight + 8);

        // 绘制边框
        this.ctx.strokeStyle = '#1976d2';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(inventoryX - 4, inventoryY - 4, inventoryWidth + 8, inventoryHeight + 8);

        // 绘制每个物品
        inventory.forEach((itemId, index) => {
            const row = Math.floor(index / maxItemsPerRow);
            const col = index % maxItemsPerRow;

            const itemX = inventoryX + col * (itemSize + itemSpacing);
            const itemY = inventoryY + row * (itemSize + itemSpacing);

            // 查找物品信息
            const item = this.data.objects ? this.data.objects.find(obj => obj.id === itemId) : null;

            // 绘制物品图标
            this.drawInventoryItem(item, itemX, itemY, itemSize);
        });

        // 绘制连接线（从智能体到物品栏）
        this.ctx.strokeStyle = '#1976d2';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([3, 3]);
        this.ctx.beginPath();
        this.ctx.moveTo(agentX + radius, agentY);
        this.ctx.lineTo(inventoryX - 4, agentY);
        this.ctx.stroke();
        this.ctx.setLineDash([]); // 重置虚线
    }

    drawInventoryItem(item, x, y, size) {
        if (!item) {
            // 未知物品 - 显示问号
            this.ctx.fillStyle = '#f5f5f5';
            this.ctx.fillRect(x, y, size, size);
            this.ctx.strokeStyle = '#bdbdbd';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(x, y, size, size);

            this.ctx.fillStyle = '#757575';
            this.ctx.font = 'bold 12px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('?', x + size / 2, y + size / 2 + 4);
            return;
        }

        // 根据物品类型选择颜色
        let itemColor = this.config.objectColors[item.type] || '#f5f5f5';
        if (item.is_tool) {
            itemColor = this.config.objectColors.TOOL;
        }

        // Draw item background
        this.ctx.fillStyle = itemColor;
        this.ctx.fillRect(x, y, size, size);

        // Draw item border
        this.ctx.strokeStyle = item.is_tool ? '#ff9800' : '#757575';
        this.ctx.lineWidth = item.is_tool ? 2 : 1;
        this.ctx.strokeRect(x, y, size, size);

        // Draw item icon/text
        this.ctx.fillStyle = '#212121';
        this.ctx.font = 'bold 8px Arial';
        this.ctx.textAlign = 'center';

        // Display first letter of item name or special icon
        let displayText = '';
        if (item.is_tool) {
            displayText = '🔧';
        } else if (item.name) {
            // Take first Chinese character or English letter
            const firstChar = item.name.charAt(0);
            displayText = /[\u4e00-\u9fa5]/.test(firstChar) ? firstChar : firstChar.toUpperCase();
        } else {
            displayText = 'I';
        }

        this.ctx.fillText(displayText, x + size / 2, y + size / 2 + 3);

        // 工具物品添加小图标
        if (item.is_tool) {
            this.ctx.fillStyle = '#ff6f00';
            this.ctx.beginPath();
            this.ctx.arc(x + size - 3, y + 3, 2, 0, 2 * Math.PI);
            this.ctx.fill();
        }
    }

    drawUI() {
        // UI已移除 - 不再显示缩放、位置、选中房间信息
    }


    // 事件处理
    onMouseDown(e) {
        this.isDragging = true;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
    }

    onMouseMove(e) {
        if (this.isDragging) {
            const deltaX = e.clientX - this.lastMouseX;
            const deltaY = e.clientY - this.lastMouseY;

            this.offsetX += deltaX;
            this.offsetY += deltaY;

            this.lastMouseX = e.clientX;
            this.lastMouseY = e.clientY;

            this.render();
        }
    }

    onMouseUp() {
        this.isDragging = false;
    }

    onWheel(e) {
        e.preventDefault();

        const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
        const newScale = Math.max(0.1, Math.min(3, this.scale * scaleFactor));

        // 以鼠标位置为中心缩放
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        this.offsetX = mouseX - (mouseX - this.offsetX) * (newScale / this.scale);
        this.offsetY = mouseY - (mouseY - this.offsetY) * (newScale / this.scale);
        this.scale = newScale;

        this.render();
    }

    onClick(e) {
        if (this.isDragging) return;

        const rect = this.canvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left - this.offsetX) / this.scale;
        const mouseY = (e.clientY - rect.top - this.offsetY) / this.scale;

        // 首先检查点击的智能体（最高优先级）
        const clickedAgent = this.getAgentAtPosition(mouseX, mouseY);
        if (clickedAgent) {
            this.selectedAgent = this.selectedAgent === clickedAgent.id ? null : clickedAgent.id;
            this.selectedObject = null; // 清除物体选择
            this.selectedRoom = null; // 清除房间选择
            this.render();
            this.onAgentSelected(clickedAgent);
            return;
        }

        // 然后检查点击的物体
        const clickedObject = this.getObjectAtPosition(mouseX, mouseY);
        if (clickedObject) {
            this.selectedObject = this.selectedObject === clickedObject.id ? null : clickedObject.id;
            this.selectedAgent = null; // 清除智能体选择
            this.selectedRoom = null; // 清除房间选择
            this.render();
            this.onObjectSelected(clickedObject);
            return;
        }

        // 最后检查点击的房间
        const roomPositions = this.calculateRoomPositions();
        for (const [roomId, pos] of Object.entries(roomPositions)) {
            if (mouseX >= pos.x && mouseX <= pos.x + pos.width &&
                mouseY >= pos.y && mouseY <= pos.y + pos.height) {
                this.selectedRoom = this.selectedRoom === roomId ? null : roomId;
                this.selectedObject = null; // 清除物体选择
                this.selectedAgent = null; // 清除智能体选择
                this.render();
                this.onRoomSelected(roomId);
                return;
            }
        }

        // 清除所有选择
        this.selectedRoom = null;
        this.selectedObject = null;
        this.selectedAgent = null;
        this.render();
    }

    getAgentAtPosition(x, y) {
        if (!this.data.agents) return null;

        const roomPositions = this.calculateRoomPositions();

        for (const agent of this.data.agents) {
            const agentLocation = agent.location || agent.location_id;
            const roomPos = roomPositions[agentLocation];
            if (!roomPos) continue;

            // 计算智能体位置
            const agentX = roomPos.x + this.config.layout.agentMargin;
            const agentY = roomPos.y + this.config.layout.roomHeaderHeight + this.config.layout.agentMargin;
            const radius = this.config.layout.agentRadius;

            // 检查点击是否在智能体圆圈内
            const distance = Math.sqrt((x - agentX) ** 2 + (y - agentY) ** 2);
            if (distance <= radius) {
                return agent;
            }

            // 检查点击是否在智能体的物品栏内
            if (agent.inventory && agent.inventory.length > 0) {
                const inventoryX = agentX + radius + 10;
                const inventoryY = agentY - 20; // 大致的物品栏位置
                const inventoryWidth = 60; // 大致的物品栏宽度
                const inventoryHeight = 40; // 大致的物品栏高度

                if (x >= inventoryX - 4 && x <= inventoryX + inventoryWidth + 8 &&
                    y >= inventoryY - 4 && y <= inventoryY + inventoryHeight + 8) {
                    return agent;
                }
            }
        }

        return null;
    }

    getObjectAtPosition(x, y) {
        // 收集所有匹配的物体，按层级排序（子物体优先）
        const matchingObjects = [];

        for (const [objectId, pos] of this.objectPositions.entries()) {
            if (x >= pos.x && x <= pos.x + pos.width &&
                y >= pos.y && y <= pos.y + pos.height) {
                const obj = this.data.objects.find(obj => obj.id === objectId);
                if (obj) {
                    // 计算物体的嵌套深度
                    const depth = this.getObjectDepth(obj);
                    matchingObjects.push({ obj, depth, area: pos.width * pos.height });
                }
            }
        }

        if (matchingObjects.length === 0) return null;

        // 按深度排序（深度大的优先），如果深度相同则按面积排序（面积小的优先）
        matchingObjects.sort((a, b) => {
            if (a.depth !== b.depth) return b.depth - a.depth;
            return a.area - b.area;
        });

        return matchingObjects[0].obj;
    }

    getObjectDepth(obj) {
        // 计算物体的嵌套深度
        let depth = 0;
        let current = obj;

        while (current && current.container_info && current.container_info.is_contained) {
            depth++;
            // 查找容器物体
            const containerId = current.container_info.container_id;
            current = this.data.objects.find(o => o.id === containerId);
        }

        return depth;
    }

    wrapText(text, maxWidth, font) {
        // 设置字体以测量文字宽度
        const originalFont = this.ctx.font;
        this.ctx.font = font;

        const words = text.split(' ');
        const lines = [];
        let currentLine = '';

        for (let i = 0; i < words.length; i++) {
            const testLine = currentLine + (currentLine ? ' ' : '') + words[i];
            const metrics = this.ctx.measureText(testLine);

            if (metrics.width > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = words[i];
            } else {
                currentLine = testLine;
            }
        }

        if (currentLine) {
            lines.push(currentLine);
        }

        // 恢复原字体
        this.ctx.font = originalFont;

        return lines.length > 0 ? lines : [text];
    }

    wrapTextForCircle(text, maxWidth) {
        // 专门为圆形内部文字换行的方法
        const originalFont = this.ctx.font;
        this.ctx.font = 'bold 11px Arial';

        // 如果文字很短，直接返回
        if (this.ctx.measureText(text).width <= maxWidth) {
            this.ctx.font = originalFont;
            return [text];
        }

        // 尝试按下划线或空格分割
        let parts = [];
        if (text.includes('_')) {
            parts = text.split('_');
        } else if (text.includes(' ')) {
            parts = text.split(' ');
        } else {
            // 如果没有分隔符，按长度分割
            const mid = Math.ceil(text.length / 2);
            parts = [text.substring(0, mid), text.substring(mid)];
        }

        // 检查分割后的部分是否适合
        const lines = [];
        for (const part of parts) {
            if (this.ctx.measureText(part).width <= maxWidth) {
                lines.push(part);
            } else {
                // 如果单个部分还是太长，进一步缩短
                let shortened = part;
                while (this.ctx.measureText(shortened + '...').width > maxWidth && shortened.length > 1) {
                    shortened = shortened.substring(0, shortened.length - 1);
                }
                lines.push(shortened + (shortened !== part ? '...' : ''));
            }
        }

        this.ctx.font = originalFont;
        return lines.slice(0, 2); // 最多返回2行
    }

    getRoomIdFromPosition(roomPos) {
        // 根据房间位置查找房间ID
        const roomPositions = this.calculateRoomPositions();
        for (const [roomId, pos] of Object.entries(roomPositions)) {
            if (pos.x === roomPos.x && pos.y === roomPos.y) {
                return roomId;
            }
        }
        return null;
    }



    onMouseLeave() {
        // 鼠标离开画布时的处理
    }



    onAgentSelected(agent) {
        // 触发智能体选择事件
        const event = new CustomEvent('agentSelected', { detail: { agent } });
        this.canvas.dispatchEvent(event);
    }

    onObjectSelected(obj) {
        // 触发物体选择事件，让web_server.py中的selectObject函数处理详情显示
        const event = new CustomEvent('objectSelected', { detail: { object: obj } });
        this.canvas.dispatchEvent(event);
    }

    onRoomSelected(roomId) {
        // 触发房间选择事件
        const event = new CustomEvent('roomSelected', { detail: { roomId } });
        this.canvas.dispatchEvent(event);
    }

    // 公共方法
    selectRoom(roomId) {
        this.selectedRoom = roomId;
        this.render();
    }

    selectAgent(agentId) {
        this.selectedAgent = agentId;
        this.selectedObject = null;
        this.selectedRoom = null;
        this.render();
    }

    resetView() {
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.render();
    }

    fitToContent() {
        if (!this.data || !this.data.rooms.length) return;

        const roomPositions = this.calculateRoomPositions();
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

        Object.values(roomPositions).forEach(pos => {
            minX = Math.min(minX, pos.x);
            minY = Math.min(minY, pos.y);
            maxX = Math.max(maxX, pos.x + pos.width);
            maxY = Math.max(maxY, pos.y + pos.height);
        });

        const contentWidth = maxX - minX;
        const contentHeight = maxY - minY;

        // 使用逻辑画布尺寸而不是物理像素尺寸
        const canvasLogicalWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasLogicalHeight = this.canvas.height / (window.devicePixelRatio || 1);

        // 留出更多边距以确保内容完全可见
        const margin = 150;
        const scaleX = (canvasLogicalWidth - margin) / contentWidth;
        const scaleY = (canvasLogicalHeight - margin) / contentHeight;
        this.scale = Math.min(scaleX, scaleY, 1);

        // 计算居中偏移量
        this.offsetX = (canvasLogicalWidth - contentWidth * this.scale) / 2 - minX * this.scale;
        this.offsetY = (canvasLogicalHeight - contentHeight * this.scale) / 2 - minY * this.scale;

        this.render();
    }
}
