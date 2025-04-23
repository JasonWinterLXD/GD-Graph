// UI/app.js
let currentUser = null;
let chatHistory = [];

// 初始化页面
$(document).ready(() => {
    // 检查主题设置
    initTheme();
    
    loadComponent('navbar', '#navbar');
    checkLoginStatus();

    // 添加主题切换按钮事件
    $('body').on('click', '#theme-toggle', toggleTheme);
});

// 初始化主题设置
function initTheme() {
    const isDarkTheme = localStorage.getItem('dark-theme') === 'true';
    if (isDarkTheme) {
        $('body').addClass('dark-theme');
        // 稍后在导航加载后更新图标
        setTimeout(() => {
            $('#theme-toggle i').removeClass('bi-moon').addClass('bi-sun');
        }, 500);
    }
}

async function loadComponent(component, target) {
    try {
        const res = await fetch(`components/${component}.html`);
        if (!res.ok) throw new Error(`加载组件失败：${res.status}`);
        $(target).html(await res.text());
    } catch (error) {
        console.error('组件加载错误:', error);
        $(target).html(`<div class="alert alert-danger">组件加载失败</div>`);
    }
}

// 登录状态检查
async function checkLoginStatus() {
    try {
        showLoading(true);
        const res = await fetch('/chat', {
            method: 'GET',
            credentials: 'include'
        });

        if (res.ok) {
            const data = await res.json();
            currentUser = data.user;
            updateAuthUI();
            showChatInterface();
        } else {
            showModal('login');
        }
    } catch (error) {
        console.error('状态检查失败:', error);
        showError('无法连接到服务器，请检查网络连接');
    } finally {
        showLoading(false);
    }
}

// 更新界面显示
function updateAuthUI() {
    if (currentUser) {
        $('#auth-buttons').addClass('d-none');
        $('#user-info').removeClass('d-none');
        $('#username-display').text(currentUser);
    } else {
        $('#auth-buttons').removeClass('d-none');
        $('#user-info').addClass('d-none');
    }
}

// 显示错误信息
function showError(message) {
    const alert = $(`
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    $('#main-container').prepend(alert);
    
    // 5秒后自动关闭
    setTimeout(() => {
        alert.alert('close');
    }, 5000);
}

// 显示对话框
function showModal(type) {
    const isLogin = type === 'login';
    const switchText = isLogin ? '没有账号？立即注册' : '已有账号？立即登录';
    const switchType = isLogin ? 'register' : 'login';
    const title = isLogin ? '用户登录' : '用户注册';
    const buttonText = isLogin ? '登 录' : '注 册';
    const icon = isLogin ? 'box-arrow-in-right' : 'person-plus';

    const modal = $(`
        <div class="modal fade" id="auth-modal">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="bi bi-${icon} me-2"></i>${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="auth-form" onsubmit="event.preventDefault(); handleAuth(event, '${type}')">
                            ${!isLogin ? `
                            <div class="mb-3">
                                <label class="form-label">邮箱</label>
                                <div class="input-group">
                                    <span class="input-group-text rounded-start"><i class="bi bi-envelope"></i></span>
                                    <input type="email" class="form-control rounded-end" name="email" required>
                                </div>
                            </div>` : ''}
                            <div class="mb-3">
                                <label class="form-label">用户名</label>
                                <div class="input-group">
                                    <span class="input-group-text rounded-start"><i class="bi bi-person"></i></span>
                                    <input type="text" class="form-control rounded-end" name="username" required>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">密码</label>
                                <div class="input-group">
                                    <span class="input-group-text rounded-start"><i class="bi bi-key"></i></span>
                                    <input type="password" class="form-control" name="password" id="password-field" required>
                                    <button class="btn btn-outline-secondary rounded-end toggle-password" type="button">
                                        <i class="bi bi-eye"></i>
                                    </button>
                                </div>
                            </div>
                            ${!isLogin ? `
                            <div class="mb-3">
                                <label class="form-label">确认密码</label>
                                <div class="input-group">
                                    <span class="input-group-text rounded-start"><i class="bi bi-key-fill"></i></span>
                                    <input type="password" class="form-control" name="confirmPassword" id="confirm-password-field" required>
                                    <button class="btn btn-outline-secondary rounded-end toggle-password" type="button">
                                        <i class="bi bi-eye"></i>
                                    </button>
                                </div>
                                <div class="invalid-feedback" id="password-match-error">两次输入的密码不一致</div>
                            </div>
                            ` : ''}
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" name="remember" id="remember">
                                <label class="form-check-label" for="remember">记住我</label>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 mb-3">
                                ${buttonText}
                            </button>
                            <div class="text-center">
                                <a href="#" class="text-decoration-none" 
                                   onclick="switchAuthModal('${switchType}')">
                                    ${switchText}
                                </a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `);

    modal.modal('show');
    
    // 添加密码切换可见性功能
    modal.find('.toggle-password').on('click', function() {
        const passwordField = $(this).closest('.input-group').find('input');
        const icon = $(this).find('i');
        
        if (passwordField.attr('type') === 'password') {
            passwordField.attr('type', 'text');
            icon.removeClass('bi-eye').addClass('bi-eye-slash');
        } else {
            passwordField.attr('type', 'password');
            icon.removeClass('bi-eye-slash').addClass('bi-eye');
        }
    });

    // 添加密码确认验证
    if (!isLogin) {
        const passwordField = modal.find('#password-field');
        const confirmField = modal.find('#confirm-password-field');
        const errorFeedback = modal.find('#password-match-error');
        
        const validatePasswords = function() {
            if (passwordField.val() && confirmField.val()) {
                if (passwordField.val() !== confirmField.val()) {
                    confirmField.addClass('is-invalid');
                    errorFeedback.show();
                    return false;
                } else {
                    confirmField.removeClass('is-invalid');
                    errorFeedback.hide();
                    return true;
                }
            }
            return false;
        };
        
        passwordField.on('input', validatePasswords);
        confirmField.on('input', validatePasswords);
        
        // 表单提交前验证密码
        modal.find('#auth-form').on('submit', function(e) {
            if (!validatePasswords()) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }
}

// 切换主题
function toggleTheme() {
    $('body').toggleClass('dark-theme');
    const isDark = $('body').hasClass('dark-theme');
    localStorage.setItem('dark-theme', isDark);
    
    const icon = $('#theme-toggle i');
    if (isDark) {
        icon.removeClass('bi-moon').addClass('bi-sun');
    } else {
        icon.removeClass('bi-sun').addClass('bi-moon');
    }
}

// 新增切换函数
function switchAuthModal(newType) {
    $('.modal').modal('hide');  // 关闭当前模态框
    setTimeout(() => showModal(newType), 300); // 确保动画完成
}

// 显示通知弹窗
function showNotification(type, message) {
    let icon, bgClass;
    if (type === 'success') {
        icon = 'check-circle-fill';
        bgClass = 'bg-success';
    } else if (type === 'error') {
        icon = 'exclamation-circle-fill';
        bgClass = 'bg-danger';
    } else {
        icon = 'info-circle-fill';
        bgClass = 'bg-primary';
    }
    
    const toast = $(`
        <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 9999">
            <div class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-${icon} me-2"></i>${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        </div>
    `);
    
    $('body').append(toast);
    const toastElement = toast.find('.toast');
    const bsToast = new bootstrap.Toast(toastElement, {delay: 3000});
    bsToast.show();
    
    // 3秒后移除元素
    setTimeout(() => {
        toast.remove();
    }, 3500);
}

// 处理认证请求
async function handleAuth(event, type) {
    event.preventDefault();
    // 移除之前的错误信息
    $('#auth-form .alert').remove();
    
    const formData = new FormData(event.target);
    const payload = {
        username: formData.get('username'),
        password: formData.get('password'),
        remember: formData.get('remember') === 'on'
    };

    // 对注册表单先进行密码匹配验证
    if (type === 'register') {
        payload.email = formData.get('email');
        
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        
        if (password !== confirmPassword) {
            const errorMsg = $(`
                <div class="alert alert-danger mt-4">
                    <i class="bi bi-exclamation-circle me-2"></i>
                    两次输入的密码不一致
                </div>
            `);
            $('#auth-form').append(errorMsg);
            return;
        }
    }

    try {
        showLoading(true);
        const res = await fetch(`/${type}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
            credentials: 'include'
        });

        const data = await res.json();
        if (res.ok) {
            currentUser = data.user || payload.username;
            updateAuthUI();
            $('.modal').modal('hide');
            showChatInterface();
            showNotification('success', `${type === 'login' ? '登录' : '注册'}成功，欢迎${currentUser}！`);
        } else {
            // 显示后端返回的具体错误信息
            const errorMsg = $(`
                <div class="alert alert-danger mt-4">
                    <i class="bi bi-exclamation-circle me-2"></i>
                    ${data.error || `请求失败，状态码：${res.status}`}
                </div>
            `);
            $('#auth-form').append(errorMsg);
            
            // 添加登录失败通知
            showNotification('error', data.error || `${type === 'login' ? '登录' : '注册'}失败，请重试`);
        }
    } catch (error) {
        console.error('请求失败:', error);
        const errorMsg = $(`
            <div class="alert alert-danger mt-4">
                <i class="bi bi-exclamation-circle me-2"></i>
                网络错误，请检查网络连接
            </div>
        `);
        $('#auth-form').append(errorMsg);
        showNotification('error', '网络错误，请检查网络连接');
    } finally {
        showLoading(false);
    }
}

// 显示聊天界面
async function showChatInterface() {
    await loadComponent('chat', '#main-container');
    const input = $('#question-input');

    // 新增键盘事件处理
    input.on('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // 阻止默认换行行为
            submitQuestion();
        }
        // Shift+Enter 保持默认换行行为
    });

    // 快速问题选择
    $('.question-tag').on('click', function() {
        const question = $(this).text();
        input.val(question);
        input.focus();
    });

    // 加载历史记录
    loadChatHistory();
    
    input.focus();
}

// 选择常见问题
function selectQuestion(element) {
    const question = $(element).text();
    $('#question-input').val(question);
    $('#question-input').focus();
}

// 加载聊天历史
function loadChatHistory() {
    const savedHistory = localStorage.getItem(`chat_history_${currentUser}`);
    if (savedHistory) {
        chatHistory = JSON.parse(savedHistory);
        chatHistory.forEach(msg => {
            addMessage(msg.text, msg.type, false);
        });
    }
    
    // 滚动到底部
    scrollChatToBottom();
}

// 保存聊天历史
function saveChatHistory() {
    localStorage.setItem(`chat_history_${currentUser}`, JSON.stringify(chatHistory));
}

// 清空聊天历史
function clearChatHistory() {
    if (confirm('确定要清空所有对话记录吗？')) {
        $('#chat-history').empty();
        chatHistory = [];
        saveChatHistory();
    }
}

// 提交问题
async function submitQuestion() {
    const input = $('#question-input');
    const question = input.val().trim();
    if (!question) return;

    showLoading(true);
    try {
        addMessage(question, 'user');
        input.val('');

        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question}),
            credentials: 'include'
        });

        if (!res.ok) {
            throw new Error(`服务器错误: ${res.status}`);
        }

        const data = await res.json();
        addMessage(data.answer, 'bot');
    } catch (error) {
        console.error('请求失败:', error);
        addMessage('获取答案失败，请稍后重试', 'bot');
    } finally {
        showLoading(false);
    }
}

// 添加消息到历史记录
function addMessage(text, type, save = true) {
    const messageTime = new Date().toLocaleTimeString();
    let formattedText = text;
    
    // 处理链接和换行
    formattedText = formattedText
        .replace(/https?:\/\/[^\s]+/g, url => `<a href="${url}" target="_blank" class="text-primary">${url}</a>`)
        .replace(/\n/g, '<br>');
    
    const message = $(`
        <div class="chat-message ${type}-message">
            <div class="message-content">${formattedText}</div>
            <div class="message-time text-muted small mt-1">
                ${type === 'user' ? '<i class="bi bi-person-circle me-1"></i>' : '<i class="bi bi-robot me-1"></i>'}
                ${messageTime}
            </div>
        </div>
    `);
    
    $('#chat-history').append(message);
    
    // 保存到历史记录
    if (save) {
        chatHistory.push({ text, type, time: messageTime });
        saveChatHistory();
    }
    
    // 滚动到底部
    scrollChatToBottom();
}

// 滚动聊天区域到底部
function scrollChatToBottom() {
    const chatHistory = document.getElementById('chat-history');
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// 显示/隐藏加载动画
function showLoading(show) {
    $('#loading').css('display', show ? 'flex' : 'none');
}

// 登出功能
async function logout() {
    try {
        showLoading(true);
        await fetch('/logout', {
            method: 'POST',
            credentials: 'include'
        });
        currentUser = null;
        updateAuthUI();
        showNotification('success', '已成功退出登录');
        setTimeout(() => {
            location.reload();
        }, 1000);
    } catch (error) {
        console.error('登出失败:', error);
        showError('登出失败，请稍后重试');
        showNotification('error', '登出失败，请稍后重试');
    } finally {
        showLoading(false);
    }
}