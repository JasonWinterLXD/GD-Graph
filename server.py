from flask import Flask, request, jsonify
from chat_GD import ChatGDGraph

app = Flask(__name__, static_url_path='', static_folder='UI')
chat_bot = ChatGDGraph()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': '未提供问题'}), 400
    question = data['question']
    answer = chat_bot.chat_main(question)
    return jsonify({'answer': answer})

# 如果需要直接访问首页（前端页面）
@app.route('/')
def index():
    return app.send_static_file('app.html')

if __name__ == '__main__':
    # 建议调试时设置 debug=True，发布时请关闭
    app.run(debug=True, host='0.0.0.0', port=5000)
