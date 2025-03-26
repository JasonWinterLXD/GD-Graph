// UI/app.js
let currentUser = null;

// 初始化页面
$(document).ready(() => {
    loadComponent('navbar', '#navbar');
    checkLoginStatus();
});

async function loadComponent(component, target) {
    const res = await fetch(`components/${component}.html`);
    $(target).html(await res.text());
}

// 登录状态检查
async function checkLoginStatus() {
    try {
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

// 显示对话框
function showModal(type) {
    const isLogin = type === 'login';
    const switchText = isLogin ? '没有账号？立即注册' : '已有账号？立即登录';
    const switchType = isLogin ? 'register' : 'login';

    const modal = $(`
        <div class="modal fade">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${isLogin ? '用户登录' : '用户注册'}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="auth-form" onsubmit="event.preventDefault(); handleAuth(event, '${type}')">
                            ${!isLogin ? `
                            <div class="mb-3">
                                <label class="form-label">邮箱</label>
                                <input type="email" class="form-control" name="email" required>
                            </div>` : ''}
                            <div class="mb-3">
                                <label class="form-label">用户名</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">密码</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" name="remember" id="remember">
                                <label class="form-check-label" for="remember">记住我</label>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 mb-3">
                                ${isLogin ? '登 录' : '注 册'}
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
}

// 新增切换函数
function switchAuthModal(newType) {
    $('.modal').modal('hide');  // 关闭当前模态框
    setTimeout(() => showModal(newType), 300); // 确保动画完成
}

// 处理认证请求
async function handleAuth(event, type) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const payload = {
        username: formData.get('username'),
        password: formData.get('password'),
        remember: formData.get('remember') === 'on'
    };

    if (type === 'register') {
        payload.email = formData.get('email');
    }

    try {
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
        } else {
            // 显示后端返回的具体错误信息
            alert(data.error || `注册失败，状态码：${res.status}`);
        }
    } catch (error) {
        console.error('请求失败:', error);
        alert('网络错误，请检查控制台日志');
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

    input.focus();
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

        const data = await res.json();
        addMessage(data.answer, 'bot');
    } catch (error) {
        addMessage('获取答案失败，请稍后重试', 'bot');
    } finally {
        showLoading(false);
    }
}

// 添加消息到历史记录
function addMessage(text, type) {
    const message = $(`
        <div class="chat-message ${type}-message">
            <div class="message-content">${text}</div>
            <div class="message-time text-muted small mt-1">${new Date().toLocaleTimeString()}</div>
        </div>
    `);
    $('#chat-history').append(message);
    message[0].scrollIntoView();
}

// 显示/隐藏加载动画
function showLoading(show) {
    $('#loading').css('display', show ? 'flex' : 'none');
}

// 登出功能
async function logout() {
    await fetch('/logout', {
        method: 'POST',
        credentials: 'include'
    });
    currentUser = null;
    updateAuthUI();
    location.reload();
}