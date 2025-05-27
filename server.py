from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from chat_GD import ChatGDGraph
import pymysql
from mysql_db import get_db, User
from neo4j import GraphDatabase

app = Flask(__name__, static_url_path='', static_folder='UI')
app.secret_key = 'sk-be6cdfdb47b94ba5b0a791ed2f207327'

# 初始化登录管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.remember_cookie_duration = timedelta(days=30)  # 设置记住我 cookie 有效期为 30 天
app.config.update(
    SESSION_COOKIE_NAME='sk-be6cdfdb47b94ba5b0a791ed2f207327',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=30*86400  # 30天过期时间
)
# 初始化问答机器人
chat_bot = ChatGDGraph()
CORS(app,
     supports_credentials=True,
     resources = {r"/*": {"origins": "*"}},  # 允许所有来源
     allow_headers = ["Content-Type", "Authorization"],
     methods = ["GET", "POST", "PUT", "DELETE"]
)

# Neo4j连接
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))

# 用户会话管理
@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:  # # 使用数据库连接池
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(user_data['id'], user_data['username'])
    return None


# 认证路由
@app.route('/register', methods=['POST'])
def register():
    """用户注册接口"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not all([username, password, email]):
        return jsonify({'error': '缺少必要参数'}), 400

    # 密码哈希处理
    password_hash = generate_password_hash(password)

    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash)
                )
                # 获取新插入用户的ID
                user_id = cursor.lastrowid
            conn.commit()
        
        # 创建用户对象并登录
        user_obj = User(user_id, username)
        login_user(user_obj)
        
        return jsonify({'message': '注册成功', 'user': username}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'error': '用户名或邮箱已存在'}), 400


@app.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)  # 获取记住状态

    if not username or not password:
        return jsonify({'error': '用户名和密码为必填项'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

    if not user:
        return jsonify({'error': '用户不存在'}), 401
    
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': '密码错误'}), 401
        
    user_obj = User(user['id'], user['username'])
    login_user(user_obj, remember=remember)
    return jsonify({'message': '登录成功', 'user': user['username']})


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出接口"""
    logout_user()
    return jsonify({'message': '登出成功'})


# 问答路由
@app.route('/chat', methods=['GET', 'POST'])
@login_required  # 要求登录
def chat():
    if request.method == 'GET':
        return jsonify({'user': current_user.username})
    """处理用户问答请求"""
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': '未提供问题'}), 400

    # 调用问答系统
    answer = chat_bot.chat_main(data['question'])
    return jsonify({'answer': answer, 'user': current_user.username})


# 图谱可视化API
@app.route('/api/graph', methods=['GET'])
@login_required
def get_graph_data():
    """获取Neo4j图谱数据用于可视化"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', default=100, type=int)
        node_type = request.args.get('type', default=None)
        
        with neo4j_driver.session() as session:
            # 基础查询
            if node_type:
                # 针对Disease类型特殊处理，只返回并发症关系
                if node_type == 'Disease':
                    result = session.run(
                        f"MATCH (node:Disease)-[r:acompany_with]->(other:Disease) "
                        f"RETURN node as n, r, other as m "
                        f"UNION "
                        f"MATCH (other:Disease)-[r:acompany_with]->(node:Disease) "
                        f"RETURN other as n, r, node as m "
                        f"LIMIT {limit}"
                    )
                else:
                    # 其他类型节点的查询，返回该类型节点的所有关系（包括入边和出边）
                    result = session.run(
                        f"MATCH (node:{node_type})-[r]->(other) "
                        f"RETURN node as n, r, other as m "
                        f"UNION "
                        f"MATCH (other)-[r]->(node:{node_type}) "
                        f"RETURN other as n, r, node as m "
                        f"LIMIT {limit}"
                    )
            else:
                # 默认查询所有关系，使用有向关系
                result = session.run(
                    f"MATCH (n)-[r]->(m) "
                    f"RETURN n, r, m LIMIT {limit}"
                )
            
            # 处理结果
            nodes = []
            links = []
            node_ids = set()
            # 用于去重关系
            relation_keys = set()
            
            for record in result:
                source = record["n"]
                target = record["m"]
                relationship = record["r"]
                
                # 添加节点
                if source.id not in node_ids:
                    node_ids.add(source.id)
                    nodes.append({
                        "id": source.id,
                        "labels": list(source.labels),
                        "properties": dict(source),
                        "name": source.get("name", "未命名")
                    })
                
                if target.id not in node_ids:
                    node_ids.add(target.id)
                    nodes.append({
                        "id": target.id,
                        "labels": list(target.labels),
                        "properties": dict(target),
                        "name": target.get("name", "未命名")
                    })
                
                # 添加关系，确保方向与Neo4j一致并去重
                # 创建唯一关系键：源节点ID-关系类型-目标节点ID
                relation_key = f"{source.id}-{relationship.type}-{target.id}"
                
                # 只有当这个关系还没有添加过时才添加
                if relation_key not in relation_keys:
                    relation_keys.add(relation_key)
                    links.append({
                        "source": source.id,
                        "target": target.id,
                        "type": relationship.type,
                        "properties": dict(relationship)
                    })
            
            return jsonify({
                "nodes": nodes,
                "links": links
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取所有节点类型
@app.route('/api/graph/types', methods=['GET'])
@login_required
def get_node_types():
    """获取Neo4j中的所有节点类型"""
    try:
        with neo4j_driver.session() as session:
            result = session.run("CALL db.labels()")
            types = [record["label"] for record in result]
            return jsonify({"types": types})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """返回前端页面"""
    return app.send_static_file('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)