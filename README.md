# 肝豆状核变性智能问答系统

基于知识图谱的肝豆状核变性医疗辅助决策系统，提供智能问答服务。

## 系统功能

- 基于知识图谱的肝豆状核变性问答
- 支持多种问题类型（症状、治疗、饮食、药物等）
- 用户账户管理系统
- 对话历史保存与查询
- 答案自动优化（使用DeepSeek API）

## 技术栈

- 后端：Python Flask
- 数据库：Neo4j (知识图谱), MySQL (用户管理)
- 前端：HTML, CSS, JavaScript, Bootstrap 5
- NLP处理：自定义实体提取和意图识别

## 项目结构

```
project/
├── answer.py          # 答案生成和格式化处理
├── app.py             # Flask应用主入口
├── chat_GD.py         # 问答系统主控制器
├── dict/              # 词典文件夹
├── mysql_db.py        # MySQL数据库连接管理
├── question_analyse.py # 问题解析
├── question_classify.py # 问题分类
├── static/            # 静态资源
│   ├── css/           # 样式文件
│   ├── js/            # JavaScript文件
│   └── img/           # 图片资源
└── templates/         # HTML模板
    ├── base.html      # 基础模板
    ├── chat.html      # 聊天界面
    ├── history.html   # 历史记录页面
    ├── login.html     # 登录页面
    └── register.html  # 注册页面
```

## 环境要求

- Python 3.8+
- Neo4j数据库
- MySQL数据库
- Flask及相关依赖

## 安装与配置

1. 安装Python依赖：
   ```
   pip install Flask Flask-Login pymysql neo4j requests
   ```

2. 配置Neo4j数据库：
   - 默认连接地址: `bolt://localhost:7687`
   - 用户名: `neo4j`
   - 密码: `12345678`

3. 配置MySQL数据库：
   - 主机: `localhost`
   - 端口: `3306`
   - 用户名: `admin`
   - 密码: `12345678`
   - 数据库名: `medical_qa`

## 运行方法

```bash
python app.py
```

默认将在 http://127.0.0.1:5000 启动应用。

## 医疗免责声明

本系统仅为医疗辅助工具，提供的信息不应替代专业医疗建议。用户在做出健康相关决定前，请咨询专业医疗人员。 