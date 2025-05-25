// UI/graph.js
let graphInstance = null;
let nodeTypes = [];
let currentNodeType = '';
let currentLimit = 100;

// 暴露到全局作用域，使外部可以访问
window.graphInstance = null;

// 节点类型对应的颜色（Neo4j风格）
const nodeColors = {
    'Disease': '#C990C0',   // 紫色
    'Symptom': '#F79767',   // 橙色
    'Drug': '#57C7E3',      // 蓝色
    'Food': '#F16667',      // 红色
    'Check': '#8DCC93',     // 绿色
    'Department': '#ECB5C9', // 粉色
    'Producer': '#4C8EDA',  // 深蓝色
    'Chinese': '#FFC454'    // 黄色
};

// 初始化图谱界面函数，可以被外部调用
function initGraphInterface() {
    console.log('初始化知识图谱界面...');
    
    // 确保全局变量重置
    graphInstance = null;
    window.graphInstance = null;
    nodeTypes = [];
    currentNodeType = '';
    currentLimit = 100;
    
    // 显示加载动画
    toggleGraphLoading(true);
    
    // 加载节点类型
    loadNodeTypes();
    
    // 设置事件监听器
    $('#node-type-select').off('change').on('change', function() {
        currentNodeType = $(this).val();
        loadGraphData();
    });
    
    $('#node-limit').off('change').on('change', function() {
        currentLimit = parseInt($(this).val());
        loadGraphData();
    });
    
    $('#refresh-graph').off('click').on('click', loadGraphData);
    
    // 初始加载图谱数据
    setTimeout(loadGraphData, 100);
}

// 页面首次加载时初始化
$(document).ready(() => {
    initGraphInterface();
});

// 加载节点类型
async function loadNodeTypes() {
    try {
        showLoading(true);
        const response = await fetch('/api/graph/types', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`请求失败: ${response.status}`);
        }
        
        const data = await response.json();
        nodeTypes = data.types || [];
        
        // 填充下拉框
        const select = $('#node-type-select');
        select.find('option:not(:first)').remove();
        
        nodeTypes.forEach(type => {
            select.append(`<option value="${type}">${type}</option>`);
        });
    } catch (error) {
        console.error('加载节点类型失败:', error);
        showNotification('error', '加载节点类型失败');
    } finally {
        showLoading(false);
    }
}

// 加载图谱数据
async function loadGraphData() {
    try {
        showLoading(true);
        toggleGraphLoading(true);
        $('#node-details-card').hide();
        
        // 显示加载中的提示
        showNotification('info', '正在加载图谱数据...');
        
        // 构建请求URL
        let url = `/api/graph?limit=${currentLimit}`;
        if (currentNodeType) {
            url += `&type=${currentNodeType}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`请求失败: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 检查数据是否为空
        if (!data.nodes || data.nodes.length === 0) {
            toggleGraphLoading(false);
            showNotification('error', `未找到${currentNodeType ? currentNodeType + '类型的' : ''}节点数据`);
            
            // 清空现有图谱
            if (graphInstance) {
                graphInstance.destroy();
                graphInstance = null;
                window.graphInstance = null;
            }
            
            // 显示空数据提示
            const container = document.getElementById('graph-container');
            if (container) {
                const emptyMsg = document.createElement('div');
                emptyMsg.className = 'text-center text-muted p-5';
                emptyMsg.innerHTML = `
                    <i class="bi bi-exclamation-circle fs-1"></i>
                    <p class="mt-3">未找到${currentNodeType ? currentNodeType + '类型的' : ''}节点数据</p>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadGraphData()">
                        <i class="bi bi-arrow-clockwise me-1"></i>重试
                    </button>
                `;
                
                // 清空容器并添加提示
                container.innerHTML = '';
                container.appendChild(emptyMsg);
            }
            return;
        }
        
        // 渲染图谱
        renderGraph(data);
        
        // 显示节点和关系数量
        const nodeCount = data.nodes.length;
        const linkCount = data.links.length;
        showNotification('success', `已加载 ${nodeCount} 个节点和 ${linkCount} 个关系`);
        
        // 如果筛选了节点类型，显示类型分布
        if (currentNodeType) {
            // 统计与所选类型相关的其他类型节点
            const relatedTypes = {};
            data.nodes.forEach(node => {
                const label = node.labels[0];
                if (label !== currentNodeType) {
                    relatedTypes[label] = (relatedTypes[label] || 0) + 1;
                }
            });
            
            // 构建类型分布信息
            let typeDistribution = '';
            for (const [type, count] of Object.entries(relatedTypes)) {
                typeDistribution += `${type}: ${count}个, `;
            }
            
            // 如果有相关类型，显示分布信息
            if (typeDistribution) {
                typeDistribution = typeDistribution.slice(0, -2); // 移除末尾的逗号和空格
                console.log(`相关节点类型分布: ${typeDistribution}`);
            }
        }
    } catch (error) {
        console.error('加载图谱数据失败:', error);
        showNotification('error', '加载图谱数据失败: ' + error.message);
        
        // 显示错误提示
        toggleGraphLoading(false);
        const container = document.getElementById('graph-container');
        if (container) {
            const errorMsg = document.createElement('div');
            errorMsg.className = 'text-center text-danger p-5';
            errorMsg.innerHTML = `
                <i class="bi bi-exclamation-triangle fs-1"></i>
                <p class="mt-3">加载图谱数据失败: ${error.message}</p>
                <button class="btn btn-sm btn-outline-danger mt-2" onclick="loadGraphData()">
                    <i class="bi bi-arrow-clockwise me-1"></i>重试
                </button>
            `;
            
            // 清空容器并添加错误提示
            container.innerHTML = '';
            container.appendChild(errorMsg);
        }
    } finally {
        showLoading(false);
        // 图谱渲染后会自动隐藏加载动画
    }
}

// 渲染图谱
function renderGraph(data) {
    // 清理之前的图谱
    if (graphInstance) {
        try {
        graphInstance.destroy();
            graphInstance = null;
        } catch (error) {
            console.error('清理旧图谱失败:', error);
        }
    }
    
    // 确保容器存在
    const container = document.getElementById('graph-container');
    if (!container) {
        console.error('图谱容器不存在');
        return;
    }
    
    // 处理数据格式，采用Neo4j风格
    const graphData = {
        nodes: data.nodes.map(node => {
            const label = node.labels[0];
            return {
                id: node.id.toString(),
                label: node.name,
                title: generateNodeTooltip(node),
                color: {
                    background: nodeColors[label] || '#D9C8AE',
                    border: darkenColor(nodeColors[label] || '#D9C8AE', 20),
                    highlight: {
                        background: lightenColor(nodeColors[label] || '#D9C8AE', 10),
                        border: darkenColor(nodeColors[label] || '#D9C8AE', 30)
                    },
                    hover: {
                        background: lightenColor(nodeColors[label] || '#D9C8AE', 10),
                        border: darkenColor(nodeColors[label] || '#D9C8AE', 30)
                    }
                },
                font: { 
                    color: '#FFFFFF',
                    size: 14,
                    face: 'Noto Sans SC',
                    strokeWidth: 2,
                    strokeColor: 'rgba(0,0,0,0.5)'
                },
                shape: 'dot',
                size: label === 'Disease' ? 25 : 18, // 疾病节点稍大
                properties: node.properties,
                labelType: label,
                borderWidth: 2,
                shadow: {
                    enabled: true,
                    color: 'rgba(0,0,0,0.2)',
                    size: 3,
                    x: 1,
                    y: 1
                }
            };
        }),
        edges: data.links.map(link => {
            // 根据关系类型设置不同颜色
            const relationColor = getRelationColor(link.type);
            
            // 修正箭头方向，确保与Neo4j一致
            // 在Neo4j中，箭头是从源节点指向目标节点
            return {
                from: link.source.toString(),
                to: link.target.toString(),
                label: link.type,
                title: link.type,
                arrows: {
                    to: {
                        enabled: true,
                        type: 'arrow',
                        scaleFactor: 0.7
                    }
                },
                color: {
                    color: relationColor,
                    highlight: lightenColor(relationColor, 20),
                    hover: lightenColor(relationColor, 20)
                },
                font: {
                    size: 11,
                    color: '#666666',
                    strokeWidth: 0,
                    align: 'middle',
                    vadjust: -10,
                    background: 'rgba(255,255,255,0.7)',
                    multi: false
                },
                smooth: {
                    enabled: true,
                    type: 'dynamic',
                    roundness: 0.5
                },
                width: 1.5,
                selectionWidth: 2,
                hoverWidth: 2,
                shadow: {
                    enabled: true,
                    color: 'rgba(0,0,0,0.1)',
                    size: 5
                }
            };
        })
    };
    
    // Neo4j风格的图谱配置
    const options = {
        nodes: {
            shape: 'dot',
            scaling: {
                min: 15,
                max: 30,
                label: {
                    enabled: true,
                    min: 14,
                    max: 24
                }
            },
            margin: 10,
            shadow: true
        },
        edges: {
            width: 1.5,
            shadow: true,
            smooth: {
                type: 'dynamic',
                forceDirection: 'none',
                roundness: 0.5
            },
            selectionWidth: function(width) { return width * 2; },
            // 确保箭头方向与Neo4j一致
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.7
                }
            }
        },
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -8000,
                centralGravity: 0.6,
                springLength: 140,
                springConstant: 0.04,
                damping: 0.09,
                avoidOverlap: 0.2
            },
            maxVelocity: 50,
            minVelocity: 0.1,
            solver: 'barnesHut',
            stabilization: {
                enabled: true,
                iterations: 1000,
                updateInterval: 100,
                onlyDynamicEdges: false,
                fit: true
            },
            timestep: 0.5,
            adaptiveTimestep: true
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            hideEdgesOnDrag: false,
            navigationButtons: true,
            keyboard: true,
            multiselect: true,
            selectable: true,
            selectConnectedEdges: true,
            hoverConnectedEdges: true,
            zoomView: true
        },
        layout: {
            improvedLayout: true,
            hierarchical: {
                enabled: false
            }
        }
    };
    
    // 创建图谱实例
    graphInstance = new vis.Network(container, graphData, options);
    
    // 同步到全局变量
    window.graphInstance = graphInstance;
    
    // 节点点击事件
    graphInstance.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = graphData.nodes.find(n => n.id === nodeId);
            if (node) {
                showNodeDetails(node);
            }
        } else {
            // 点击空白处隐藏详情
            $('#node-details-card').hide();
        }
    });
    
    // 双击事件 - 居中显示
    graphInstance.on('doubleClick', function(params) {
        if (params.nodes.length > 0) {
            graphInstance.focus(params.nodes[0], {
                scale: 1.2,
                animation: {
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }
    });
    
    // 稳定后事件 - 隐藏加载动画
    graphInstance.on('stabilizationIterationsDone', function() {
        toggleGraphLoading(false);
    });
}

// 切换图谱加载动画
function toggleGraphLoading(show) {
    if (show) {
        $('.graph-loading').fadeIn(200);
        $('.graph-controls-hint').hide();
    } else {
        $('.graph-loading').fadeOut(200);
        setTimeout(() => {
            $('.graph-controls-hint').fadeIn(200);
        }, 300);
    }
}

// 生成节点提示
function generateNodeTooltip(node) {
    const label = node.labels[0];
    const name = node.properties.name || '未命名';
    
    let tooltip = `<div class="node-tooltip">
                      <div class="node-tooltip-header" style="background-color:${nodeColors[label]}">
                          <strong>${label}</strong>
                      </div>
                      <div class="node-tooltip-body">
                          <strong>${name}</strong>`;
    
    // 添加最多3个关键属性
    let propCount = 0;
    for (const [key, value] of Object.entries(node.properties)) {
        if (key !== 'name' && value && propCount < 3) {
            tooltip += `<br/><span>${formatPropertyName(key)}: ${truncateText(value, 50)}</span>`;
            propCount++;
        }
    }
    
    tooltip += `</div></div>`;
    return tooltip;
}

// 获取关系颜色
function getRelationColor(relationType) {
    // 根据不同关系类型返回不同颜色
    const relationColors = {
        'has_symptom': '#68BDF6',
        'need_check': '#6DCE9E',
        'belongs_to': '#FF756E',
        'do_eat': '#DE9BF9',
        'no_eat': '#FB95AF',
        'recommand_eat': '#FFD86E',
        'common_drug': '#A5ABB6',
        'recommand_drug': '#9FAADF',
        'drugs_of': '#8DCC93',
        'acompany_with': '#F79767',
        'chinese_cure': '#FFC454'
    };
    
    return relationColors[relationType] || '#A5ABB6';  // 默认灰色
}

// 获取节点颜色
function getNodeColor(label) {
    return nodeColors[label] || '#D9C8AE';
}

// 显示节点详情
function showNodeDetails(node) {
    const detailsCard = $('#node-details-card');
    const detailsContent = $('#node-details-content');
    
    // 生成属性表格，Neo4j风格
    const nodeColor = node.color.background;
    
    let tableHTML = `
        <div class="node-header" style="background-color: ${nodeColor}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <h5 class="mb-0">${node.labelType} <small style="color: rgba(255,255,255,0.9);">${node.properties.name || '未命名'}</small></h5>
        </div>
        <table class="property-table">
            <tbody>
    `;
    
    // 添加属性行
    for (const [key, value] of Object.entries(node.properties)) {
        // 跳过空值
        if (value) {
            tableHTML += `
                <tr>
                    <th>${formatPropertyName(key)}</th>
                    <td>${formatPropertyValue(value)}</td>
                </tr>
            `;
        }
    }
    
    tableHTML += `
            </tbody>
        </table>
    `;
    
    detailsContent.html(tableHTML);
    detailsCard.show();
}

// 格式化属性名称
function formatPropertyName(name) {
    // 将下划线转换为空格并首字母大写
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// 格式化属性值
function formatPropertyValue(value) {
    if (Array.isArray(value)) {
        return value.join(', ');
    } else if (typeof value === 'string' && value.length > 100) {
        return value.substring(0, 100) + '...';
    }
    return value;
}

// 截断文本
function truncateText(text, maxLength) {
    if (typeof text === 'string' && text.length > maxLength) {
        return text.substring(0, maxLength) + '...';
    }
    return text;
}

// 颜色处理函数
function darkenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16),
          amt = Math.round(2.55 * percent),
          R = (num >> 16) - amt,
          G = (num >> 8 & 0x00FF) - amt,
          B = (num & 0x0000FF) - amt;
    return '#' + (0x1000000 + (R < 0 ? 0 : R) * 0x10000 + (G < 0 ? 0 : G) * 0x100 + (B < 0 ? 0 : B)).toString(16).slice(1);
}

function lightenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16),
          amt = Math.round(2.55 * percent),
          R = Math.min(255, (num >> 16) + amt),
          G = Math.min(255, (num >> 8 & 0x00FF) + amt),
          B = Math.min(255, (num & 0x0000FF) + amt);
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
} 