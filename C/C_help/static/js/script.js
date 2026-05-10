// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    checkApiStatus();
    setupSyntaxHighlighting();
    initializeLineNumbers();
    setupFileUploadListeners();
    initializeTechEffects();
});

// 初始化科技风效果 - 白色主题
function initializeTechEffects() {
    // 添加输入框聚焦效果 - 白色主题
    document.querySelectorAll('.code-editor').forEach(editor => {
        editor.addEventListener('focus', function() {
            this.closest('.code-container').style.boxShadow = '0 4px 16px rgba(0, 102, 204, 0.2)';
            this.closest('.code-container').style.borderColor = 'var(--tech-primary)';
            this.style.backgroundColor = '#ffffff';
        });
        
        editor.addEventListener('blur', function() {
            this.closest('.code-container').style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.08)';
            this.closest('.code-container').style.borderColor = 'var(--tech-border)';
            this.style.backgroundColor = '#ffffff';
        });
    });
    
    // 添加按钮点击效果
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // 添加结果卡片出现动画
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.classList && node.classList.contains('result-card')) {
                        node.classList.add('fade-in-up');
                    }
                    if (node.classList && node.classList.contains('defect-card')) {
                        node.classList.add('fade-in-up');
                    }
                });
            }
        });
    });
    
    // 观察结果容器
    document.querySelectorAll('.result-container').forEach(container => {
        observer.observe(container, { childList: true, subtree: true });
    });
}

// 初始化文件上传监听器
function setupFileUploadListeners() {
    // 为每个文件上传控件添加监听器
    document.getElementById('defect-file-upload').addEventListener('change', function() {
        previewFile(this, 'defect-code');
        uploadFile('defect'); // 自动上传文件
    });
    
    document.getElementById('explain-file-upload').addEventListener('change', function() {
        previewFile(this, 'explain-code');
        uploadFile('explain'); // 自动上传文件
    });
    
    document.getElementById('debug-file-upload').addEventListener('change', function() {
        previewFile(this, 'debug-code');
        uploadFile('debug'); // 自动上传文件
    });
    
    // 添加文件上传区域的双击监听器
    document.querySelectorAll('.file-upload-container').forEach(container => {
        container.addEventListener('dblclick', function() {
            // 获取对应的文件上传控件ID
            const moduleType = this.closest('.tab-pane').id.split('-')[0];
            const fileInputId = `${moduleType}-file-upload`;
            // 触发文件上传控件的点击事件
            document.getElementById(fileInputId).click();
        });
    });
}

// 尝试使用多种编码读取文件
function tryReadFileWithEncodings(file, encodings, targetTextareaId, index = 0) {
    if (index >= encodings.length) {
        alert('无法正确读取文件编码，请尝试转换文件编码为UTF-8');
        return;
    }
    
    const encoding = encodings[index];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const content = e.target.result;
        
        // 检查内容是否含有乱码（简单判断法：检查是否有替换字符""）
        if (encoding === 'UTF-8' && content.includes('')) {
            // UTF-8读取出现乱码，尝试下一种编码
            tryReadFileWithEncodings(file, encodings, targetTextareaId, index + 1);
        } else {
            document.getElementById(targetTextareaId).value = content;
            updateLineNumbers(document.getElementById(targetTextareaId));
        }
    };
    
    reader.onerror = function() {
        // 当前编码读取失败，尝试下一个
        tryReadFileWithEncodings(file, encodings, targetTextareaId, index + 1);
    };
    
    if (encoding === 'UTF-8') {
        reader.readAsText(file); // 默认UTF-8
    } else {
        // 使用TextDecoder处理非UTF-8编码
        const blobReader = new FileReader();
        blobReader.onload = function(e) {
            try {
                const buffer = e.target.result;
                const decoder = new TextDecoder(encoding);
                const text = decoder.decode(buffer);
                document.getElementById(targetTextareaId).value = text;
                updateLineNumbers(document.getElementById(targetTextareaId));
            } catch (error) {
                // 当前编码解析失败，尝试下一个
                tryReadFileWithEncodings(file, encodings, targetTextareaId, index + 1);
            }
        };
        blobReader.readAsArrayBuffer(file);
    }
}

// 预览选择的文件内容
function previewFile(fileInput, targetTextareaId) {
    const file = fileInput.files[0];
    if (!file) return;
    
    // 验证文件类型
    const validExtensions = ['.c', '.cpp', '.h'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
        alert('请上传有效的C语言文件 (.c, .cpp, .h)');
        fileInput.value = '';
        return;
    }
    
    // 限制文件大小（1MB）
    if (file.size > 1024 * 1024) {
        alert('文件大小不能超过1MB');
        fileInput.value = '';
        return;
    }
    
    // 读取文件内容，尝试使用多种编码
    tryReadFileWithEncodings(file, ['UTF-8', 'GBK', 'GB18030', 'GB2312'], targetTextareaId);
}

// 上传文件处理
function uploadFile(targetType) {
    const fileInputId = `${targetType}-file-upload`;
    const codeTextareaId = `${targetType}-code`;
    const resultContainerId = `${targetType}-result`; // 用于显示上传状态/错误

    const fileInput = document.getElementById(fileInputId);
    const codeTextarea = document.getElementById(codeTextareaId);
    const resultContainer = document.getElementById(resultContainerId); // 获取对应的结果区域

    if (!fileInput.files || fileInput.files.length === 0) {
        alert('请先选择一个文件');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // 可选：在结果区域显示加载状态
    if (resultContainer) {
        resultContainer.innerHTML = '<div class="alert alert-info"><i class="bi bi-hourglass-split"></i> 正在上传文件...</div>';
    }

    fetch('/api/upload_file', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            // 在结果区域显示错误
            if (resultContainer) {
                resultContainer.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 上传失败: ${data.error}</div>`;
            } else {
                alert(`上传失败: ${data.error}`); // Fallback
            }
        } else if (data.status === 'success') {
            codeTextarea.value = data.content; // 将文件内容填入文本框
            // 清空结果区域或显示成功消息
            if (resultContainer) {
                resultContainer.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> 文件 "${data.filename}" 上传成功！内容已加载。</div>`;
                // 可选：短暂显示后清除
                // setTimeout(() => { resultContainer.innerHTML = ''; }, 3000);
            }
            alert(`文件 "${data.filename}" 上传成功！`);
        } else {
             if (resultContainer) {
                resultContainer.innerHTML = `<div class="alert alert-warning"><i class="bi bi-exclamation-triangle"></i> 上传时发生未知问题。</div>`;
            } else {
                alert('上传时发生未知问题。');
            }
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
         if (resultContainer) {
            resultContainer.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 上传请求失败: ${error.message}</div>`;
        } else {
            alert(`上传请求失败: ${error.message}`);
        }
    });
}

// 初始化所有代码编辑器的行号
function initializeLineNumbers() {
    const textareas = document.querySelectorAll('.code-editor');
    textareas.forEach(textarea => {
        // 初始化行号
        updateLineNumbers(textarea);
        
        // 添加输入事件监听器
        textarea.addEventListener('input', function() {
            updateLineNumbers(this);
        });
        
        // 添加滚动事件监听器
        textarea.addEventListener('scroll', function() {
            const container = this.closest('.code-container');
            const lineNumbers = container.querySelector('.line-numbers');
            lineNumbers.scrollTop = this.scrollTop;
        });
        
        // 添加粘贴事件监听器
        textarea.addEventListener('paste', function(e) {
            // 阻止默认粘贴行为
            e.preventDefault();
            
            // 获取剪贴板数据
            const clipboardData = e.clipboardData || window.clipboardData;
            const pastedData = clipboardData.getData('Text');
            
            // 在光标位置插入文本
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.substring(0, start) + pastedData + this.value.substring(end);
            
            // 更新光标位置
            this.selectionStart = this.selectionEnd = start + pastedData.length;
            
            // 立即更新行号
            updateLineNumbers(this);
        });
        
        // 监听窗口大小变化
        window.addEventListener('resize', function() {
            updateLineNumbers(textarea);
        });
    });
}

// 更新行号
function updateLineNumbers(textarea) {
    const container = textarea.closest('.code-container');
    const lineNumbers = container.querySelector('.line-numbers');
    const lines = textarea.value.split('\n');
    const lineCount = lines.length;
    
    // 生成行号HTML
    lineNumbers.innerHTML = Array.from({length: lineCount}, (_, i) => i + 1).join('\n');
    
    // 确保行号区域的高度与文本区域匹配
    lineNumbers.style.height = textarea.clientHeight + 'px';
    
    // 同步滚动位置
    lineNumbers.scrollTop = textarea.scrollTop;
}

// 检查API状态
function checkApiStatus() {
    const statusBadge = document.getElementById('api-status');
    
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                statusBadge.className = 'badge bg-success';
                statusBadge.innerHTML = '<i class="bi bi-check-circle"></i> API已连接';
            } else {
                statusBadge.className = 'badge bg-danger';
                statusBadge.innerHTML = '<i class="bi bi-x-circle"></i> API连接失败';
            }
        })
        .catch(error => {
            statusBadge.className = 'badge bg-danger';
            statusBadge.innerHTML = '<i class="bi bi-x-circle"></i> API连接错误';
            console.error('API状态检查失败:', error);
        });
}

// 设置语法高亮
function setupSyntaxHighlighting() {
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightBlock(block);
    });
}

// 显示加载动画 - 科技风
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="text-center my-5">
                <div class="spinner-border text-primary pulse-glow" role="status">
                    <span class="visually-hidden">AI分析中...</span>
                </div>
                <p class="mt-3 text-primary">AI智能分析中，请稍候...</p>
            </div>
        `;
    }
}

function hideLoading(containerId) {
    // 仅清除加载指示器，实际内容将由调用函数设置
    // 这个函数不需要做任何事情，因为调用它的函数会立即设置新内容
}

// 隐藏加载动画
function hideLoading() {
    document.getElementById('loading-overlay').classList.add('d-none');
}

// 假设 showLoading 和 hideLoading 函数已定义

// 修改 detectDefects 函数以获取代码
function detectDefects() {
    const codeInput = document.getElementById('defect-code').value;
    const resultContainer = document.getElementById('defect-result');

    if (!codeInput.trim()) {
        resultContainer.innerHTML = '<div class="alert alert-warning"><i class="bi bi-exclamation-triangle"></i> 请输入C代码</div>';
        return;
    }

    showLoading('defect-result');

    fetch('/api/detect_defects', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: codeInput })
    })
    .then(response => {
        // 即使状态码不是200，也尝试解析响应
        return response.json().catch(e => {
            console.error('解析响应失败:', e);
            return { 
                error: `请求失败：HTTP错误! 状态: ${response.status}`,
                details: '无法解析服务器响应',
                defects: []
            };
        });
    })
    .then(data => {
        hideLoading('defect-result');
        console.log('服务器响应:', data);  // 调试日志

        // 确保data.defects存在且是数组
        if (!data.defects || !Array.isArray(data.defects)) {
            data.defects = [];
        }

        if (data.error) {
            // 显示错误信息 - 科技风
            let errorHtml = `
                <div class="card defect-card fade-in-up">
                    <div class="card-header">
                        <i class="bi bi-exclamation-triangle"></i> 检测错误
                    </div>
                    <div class="card-body">
                        <p><strong>错误信息：</strong>${data.error}</p>
                        ${data.details ? `<p><strong>详情：</strong>${data.details}</p>` : ''}
                    </div>
                </div>
            `;
            
            // 即使有错误，也尝试显示缺陷（如果有的话）
            if (data.defects && data.defects.length > 0) {
                errorHtml += '<h5 class="mt-4 mb-3"><i class="bi bi-list-ul"></i> 已检测到的缺陷：</h5>';
                resultContainer.innerHTML = errorHtml;
                displayDefectsBelow(data.defects, resultContainer);
            } else {
                resultContainer.innerHTML = errorHtml;
            }
        } else {
            // 显示检测结果 - 科技风
            if (data.defects.length === 0) {
                resultContainer.innerHTML = `
                    <div class="card success-card fade-in-up">
                        <div class="card-header">
                            <i class="bi bi-check-circle"></i> 检测完成
                        </div>
                        <div class="card-body">
                            <p>🎉 恭喜！未检测到明显缺陷，您的代码看起来很棒！</p>
                        </div>
                    </div>
                `;
            } else {
                displayDefects(data.defects);
            }
        }
    })
    .catch(error => {
        console.error('请求或处理错误:', error);
        hideLoading('defect-result');
        resultContainer.innerHTML =
            `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 请求失败：${error.message}</div>`;
    });
}

// 辅助函数：在指定容器下方显示缺陷
function displayDefectsBelow(defects, container) {
    if (!defects || defects.length === 0) {
        return;
    }

    let html = '<ul class="list-group">';
    defects.forEach((defect, index) => {
        html += `
            <li class="list-group-item">
                <h6 class="mb-1"><span class="badge bg-danger me-2">缺陷 ${index + 1}</span> ${escapeHtml(defect.description || 'N/A')}</h6>
                <p class="mb-1"><strong>影响:</strong> ${escapeHtml(defect.impact || 'N/A')}</p>
                <p class="mb-0"><strong>建议:</strong> ${escapeHtml(defect.suggestion || 'N/A')}</p>
            </li>
        `;
    });
    html += '</ul>';
    
    // 创建新元素并添加到容器后面
    const defectsElement = document.createElement('div');
    defectsElement.innerHTML = html;
    container.appendChild(defectsElement);
}

// 显示缺陷 - 科技风风格
function displayDefects(defects) {
    const resultContainer = document.getElementById('defect-result');
    if (!defects || defects.length === 0) {
        resultContainer.innerHTML = `
            <div class="card success-card fade-in-up">
                <div class="card-header">
                    <i class="bi bi-check-circle"></i> 检测完成
                </div>
                <div class="card-body">
                    <p>🎉 恭喜！未检测到明显缺陷，您的代码看起来很棒！</p>
                </div>
            </div>
        `;
        return;
    }

    let html = '<div class="defects-summary mb-4">';
    html += `<h5><i class="bi bi-exclamation-triangle"></i> 检测到 ${defects.length} 个缺陷</h5>`;
    html += '</div>';
    
    defects.forEach((defect, index) => {
        const severity = defect.severity || 'medium';
        const severityColor = severity === 'high' ? 'var(--tech-error)' :
                             severity === 'medium' ? 'var(--tech-warning)' : 'var(--tech-success)';
        
        html += `
            <div class="card defect-card fade-in-up" style="animation-delay: ${index * 0.1}s">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-bug"></i> 缺陷 ${index + 1}</span>
                        <span class="badge" style="background: ${severityColor}">${severity.toUpperCase()}</span>
                    </div>
                </div>
                <div class="card-body">
                    <h6 class="text-danger mb-3">${escapeHtml(defect.description || 'N/A')}</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>🚨 影响:</strong></p>
                            <p class="text-warning">${escapeHtml(defect.impact || 'N/A')}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>💡 建议:</strong></p>
                            <p class="text-success">${escapeHtml(defect.suggestion || 'N/A')}</p>
                        </div>
                    </div>
                    ${defect.line ? `<p class="mt-2"><small><strong>位置:</strong> 第 ${defect.line} 行</small></p>` : ''}
                </div>
            </div>
        `;
    });
    
    resultContainer.innerHTML = html;
}

// 假设 explainCode 函数存在，并进行类似修改
function explainCode() {
    const codeInput = document.getElementById('explain-code').value; // 获取代码
    const resultContainer = document.getElementById('explain-result');
    const queryInput = document.getElementById('explain-query').value; // 获取可选的查询问题

    if (!codeInput.trim()) {
        resultContainer.innerHTML = '<div class="alert alert-warning"><i class="bi bi-exclamation-triangle"></i> 请输入C代码</div>';
        return;
    }

    showLoading('explain-result');

    fetch('/api/explain_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: codeInput, query: queryInput }) // 发送代码和查询
    })
    .then(response => response.json())
    .then(data => {
        hideLoading('explain-result');

        if (data.error) {
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i> 错误：${data.error}
                </div>`;
        } else {
            if (data.explanation) {
                // 预处理解释内容，改进标题和列表格式
                let processedExplanation = data.explanation
                    // 确保所有标题都有适当的上下间距
                    .replace(/\n(#{1,3})\s+/g, '\n\n$1 ')
                    // 确保所有列表项都有序号和缩进
                    .replace(/^(\d+)\.(\s+)/gm, '$1.$2')
                    .replace(/^[*-](\s+)/gm, '- $1');

                // 使用科技风卡片样式显示解释内容
                const explanationContent = marked.parse(processedExplanation);
                
                let html = '<div class="card fade-in-up">';
                html += '<div class="card-header"><i class="bi bi-lightbulb"></i> 代码功能解释</div>';
                html += '<div class="card-body markdown-body">' + explanationContent + '</div>';
                html += '</div>';
                
                resultContainer.innerHTML = html;
                
                // 应用语法高亮
                document.querySelectorAll('#explain-result pre code').forEach((block) => {
                    hljs.highlightBlock(block); // 假设 highlight.js 已引入和配置
                });
            } else {
                resultContainer.innerHTML = '<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 无法获取代码解释</div>';
            }
        }
    })
    .catch(error => {
        hideLoading('explain-result');
        resultContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-circle"></i> 请求失败：${error.message}
            </div>`;
    });
}


// 修改 debugCode 函数，添加调试日志
function debugCode() {
    console.log('Debug function called');
    
    const codeInput = document.getElementById('debug-code');
    const errorMessage = document.getElementById('error-message');
    const resultContainer = document.getElementById('debug-result');
    
    console.log('Code input element:', codeInput);
    console.log('Error message element:', errorMessage);
    console.log('Result container element:', resultContainer);
    
    if (!codeInput) {
        console.error('Code input element not found');
        return;
    }
    
    if (!errorMessage) {
        console.error('Error message element not found');
        return;
    }
    
    const codeValue = codeInput.value;
    const errorValue = errorMessage.value;
    
    console.log('Code value:', codeValue);
    console.log('Error value:', errorValue);

    // 检查是否输入了代码
    if (!codeValue.trim()) {
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="card warning-card fade-in-up">
                    <div class="card-header">
                        <i class="bi bi-exclamation-triangle"></i> 输入提示
                    </div>
                    <div class="card-body">
                        <p>请输入C代码以便进行调试分析。</p>
                    </div>
                </div>
            `;
        }
        return;
    }

    // 检查是否输入了错误信息
    if (!errorValue || !errorValue.trim()) {
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="card warning-card fade-in-up">
                    <div class="card-header">
                        <i class="bi bi-exclamation-triangle"></i> 输入提示
                    </div>
                    <div class="card-body">
                        <p>请提供错误信息或问题描述，这将帮助AI更准确地分析您的问题。</p>
                    </div>
                </div>
            `;
        }
        return;
    }

    // 显示加载状态
    if (resultContainer) {
        showLoading('debug-result');
    }

    fetch('/api/debug_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: codeValue, error_message: errorValue })
    })
    .then(response => response.json())
    .then(data => {
        if (resultContainer) {
            hideLoading('debug-result');
        }

        if (data.error) {
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle"></i> 错误：${data.error}
                    </div>`;
            }
        } else {
            if (data.debug_suggestions && resultContainer) { // 修正字段名称
                // 预处理调试建议，改进格式
                let processedSuggestions = data.debug_suggestions
                    // 确保所有标题都有适当的上下间距
                    .replace(/\n(#{1,3})\s+/g, '\n\n$1 ')
                    // 确保所有列表项都有序号和缩进
                    .replace(/^(\d+)\.(\s+)/gm, '$1.$2')
                    .replace(/^[*-](\s+)/gm, '- $1')
                    // 统一代码块格式
                    .replace(/```(\w+)\n/g, '```$1\n');
                
                // 使用科技风卡片样式显示调试建议
                const debugContent = marked.parse(processedSuggestions);
                
                let html = '<div class="card fade-in-up">';
                html += '<div class="card-header"><i class="bi bi-tools"></i> 调试分析与解决方案</div>';
                html += '<div class="card-body markdown-body">' + debugContent + '</div>';
                html += '</div>';
                
                resultContainer.innerHTML = html;
                
                // 应用语法高亮
                document.querySelectorAll('#debug-result pre code').forEach((block) => {
                    hljs.highlightBlock(block);
                });
            } else if (resultContainer) {
                resultContainer.innerHTML = '<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 无法获取调试建议</div>';
            }
        }
    })
    .catch(error => {
        if (resultContainer) {
            hideLoading('debug-result');
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i> 请求失败：${error.message}
                </div>`;
        }
    });
}

// 用于防止XSS攻击的辅助函数
function escapeHtml(unsafe) {
    if (unsafe === null || typeof unsafe === 'undefined') {
        return '';
    }
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }