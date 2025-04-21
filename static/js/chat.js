/**
 * 肝豆状核变性智能问答系统聊天界面交互
 */

// 全局暴露addMessage函数
window.addMessage = null;

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const typingIndicator = document.getElementById('typingIndicator');

    // 初始化
    messageInput.focus();
    
    // 检测输入变化来启用/禁用发送按钮
    messageInput.addEventListener('input', function() {
        sendButton.disabled = messageInput.value.trim() === '';
    });
    
    // 允许按Enter键发送消息（Shift+Enter换行）
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (!sendButton.disabled) {
                sendMessage();
            }
        }
    });
    
    // 点击发送按钮时发送消息
    sendButton.addEventListener('click', sendMessage);
    
    // 发送消息函数
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // 添加用户消息到聊天框
        addMessage(message, 'user');
        
        // 清空输入框并聚焦
        messageInput.value = '';
        messageInput.focus();
        sendButton.disabled = true;
        
        // 将加载指示器添加到消息列表末尾，确保它始终在最新消息后面
        if (typingIndicator.parentNode !== chatMessages) {
            chatMessages.appendChild(typingIndicator);
        }
        
        // 显示"正在输入"动画
        typingIndicator.style.display = 'block';
        
        // 滚动到底部
        scrollToBottom();
        
        // 发送请求到后端
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(data => {
            // 隐藏"正在输入"动画
            typingIndicator.style.display = 'none';
            
            // 添加机器人回复
            addMessage(data.reply, 'bot');
            
            // 滚动到底部
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            addMessage('抱歉，发生了错误，请稍后再试。', 'bot');
            scrollToBottom();
        });
    }
    
    // 添加消息到聊天框
    function addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // 对机器人消息进行格式化（支持换行）
        if (sender === 'bot') {
            content = content.replace(/\n/g, '<br>');
            
            // 对于长内容，添加滚动样式
            if (content.length > 300) {
                messageDiv.style.maxHeight = '350px';
                messageDiv.style.overflowY = 'auto';
            }
        }
        
        messageDiv.innerHTML = content;
        
        // 在加载指示器之前插入消息，确保加载指示器始终在最后
        if (typingIndicator.parentNode === chatMessages) {
            chatMessages.insertBefore(messageDiv, typingIndicator);
        } else {
            chatMessages.appendChild(messageDiv);
        }
    }
    
    // 暴露给全局
    window.addMessage = addMessage;
    
    // 滚动到聊天框底部
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 暴露函数给全局作用域，用于点击建议按钮
    window.askQuestion = function(question) {
        messageInput.value = question;
        sendButton.disabled = false;
        sendMessage();
    };
}); 