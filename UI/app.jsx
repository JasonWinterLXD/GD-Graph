import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const sendMessage = async () => {
        if (input.trim() === '') return;

        // 添加用户消息
        const userMessage = { text: input, sender: 'user' };
        setMessages([...messages, userMessage]);
        setInput('');
        setLoading(true);

        try {
            // 发送请求到后端
            const response = await axios.post('http://localhost:5000/api/chat', { question: input });
            const answer = response.data.answer;

            // 添加系统回复
            setMessages((prev) => [...prev, { text: answer, sender: 'system' }]);
        } catch (error) {
            console.error('Error:', error);
            setMessages((prev) => [...prev, { text: '抱歉，系统出现错误', sender: 'system' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app">
            <header className="navbar">
                <h1>肝豆问答系统</h1>
            </header>
            <div className="chat-window">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
                {loading && <div className="message system">正在思考...</div>}
            </div>
            <div className="input-area">
        <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
            placeholder="请输入您的问题..."
        />
                <button onClick={sendMessage} disabled={loading}>
                    发送
                </button>
            </div>
        </div>
    );
}

export default App;