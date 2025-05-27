from neo4j import GraphDatabase
import requests
import json

class Answer:
    def __init__(self):
        """初始化数据库连接"""
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))
        self.num_limit = 20

    def search_main(self, sqls):
        """执行Cypher查询并返回答案"""
        final_answers = []
        with self.driver.session() as session:
            for sql_ in sqls:
                question_type = sql_['question_type']
                answers = [item for query in sql_['sql'] for item in session.run(query).data()]
                final_answer = self.answer_prettify(question_type, answers)
                if final_answer:
                    final_answers.append(final_answer)
        return final_answers

    # def __init__(self):
    #     """初始化数据库连接"""
    #     self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))
    #     self.num_limit = 20
    #     # DeepSeek配置
    #     self.ds_api_key = "sk-be6cdfdb47b94ba5b0a791ed2f207327"
    #     self.ds_api_url = "https://api.deepseek.com/v1/chat/completions"
    #
    # def _deepseek_process(self, text):
    #     """调用DeepSeek API优化回答"""
    #     headers = {
    #         "Authorization": f"Bearer {self.ds_api_key}",
    #         "Content-Type": "application/json"
    #     }
    #     payload = {
    #         "messages": [
    #             {"role": "system",
    #              "content": "你是一个医疗问答优化助手，请将以下关于肝豆状核变性的回答转化为更人性化的表达，保持信息准确性"},
    #             {"role": "user", "content": text}
    #         ],
    #         "model": "deepseek-chat",
    #         "temperature": 0.3
    #     }
    #
    #     # 增加重试机制和超时时间
    #     for attempt in range(3):  # 最多重试3次
    #         try:
    #             response = requests.post(
    #                 self.ds_api_url,
    #                 headers=headers,
    #                 json=payload,
    #                 timeout=15  # 延长超时到15秒
    #             )
    #             if response.status_code == 200:
    #                 return response.json()['choices'][0]['message']['content']
    #             elif response.status_code >= 500:
    #                 print(f"服务器错误，正在重试... ({attempt + 1}/3)")
    #                 continue
    #             return text
    #         except requests.exceptions.Timeout:
    #             print(f"请求超时，正在重试... ({attempt + 1}/3)")
    #         except Exception as e:
    #             print(f"API错误: {str(e)}")
    #             break
    #     return f"[优化失败] {text}"  # 明确标注失败状态
    #
    #     # try:
    #     #     response = requests.post(self.ds_api_url, headers=headers, json=payload, timeout=10)
    #     #     if response.status_code == 200:
    #     #         return response.json()['choices'][0]['message']['content']
    #     #     return text  # API调用失败时返回原答案
    #     # except Exception as e:
    #     #     print(f"DeepSeek API Error: {e}")
    #     #     return text
    #
    # def search_main(self, sqls):
    #     """执行Cypher查询并返回答案"""
    #     final_answers = []
    #     with self.driver.session() as session:
    #         for sql_ in sqls:
    #             question_type = sql_['question_type']
    #             answers = [item for query in sql_['sql'] for item in session.run(query).data()]
    #             raw_answer = self.answer_prettify(question_type, answers)
    #             if raw_answer:
    #                 # 调用DeepSeek优化回答
    #                 final_answer = self._deepseek_process(raw_answer)
    #                 final_answers.append(final_answer)
    #     return final_answers

    def answer_prettify(self, question_type, answers):
        """根据问题类型格式化答案"""
        if not answers:
            return ''

        formatters = {
            'disease_symptom': lambda
                a: f"{a[0]['m.name']}的症状包括：{';'.join(list(set(i['n.name'] for i in a))[:self.num_limit])}",
            'symptom_disease': lambda
                a: f"症状{a[0]['n.name']}可能染上的疾病有：{';'.join(list(set(i['m.name'] for i in a))[:self.num_limit])}",
            'disease_cause': lambda
                a: f"{a[0]['m.name']}可能的成因有：{';'.join(list(set(i['m.cause'] for i in a))[:self.num_limit])}",
            'disease_prevent': lambda
                a: f"{a[0]['m.name']}的预防措施包括：{';'.join(list(set(i['m.prevent'] for i in a))[:self.num_limit])}",
            'disease_lasttime': lambda
                a: f"{a[0]['m.name']}治疗可能持续的周期为：{';'.join(list(set(i['m.cure_lasttime'] for i in a))[:self.num_limit])}",
            'disease_cureway': lambda
                a: f"{a[0]['m.name']}可以尝试如下治疗：{';'.join(list(set(';'.join(i['m.cure_way']) for i in a))[:self.num_limit])}",
            'disease_cureprob': lambda
                a: f"{a[0]['m.name']}治愈的概率为（仅供参考）：{';'.join(list(set(i['m.cured_prob'] for i in a))[:self.num_limit])}",
            'disease_easyget': lambda
                a: f"{a[0]['m.name']}的易感人群包括：{';'.join(list(set(i['m.easy_get'] for i in a))[:self.num_limit])}",
            'disease_desc': lambda
                a: f"{a[0]['m.name']}，熟悉一下：{';'.join(list(set(i['m.desc'] for i in a))[:self.num_limit])}",
            'disease_acompany': lambda
                a: f"{a[0]['m.name']}的并发症包括：{';'.join(list(set(i['n.name'] for i in a if i['n.name'] != a[0]['m.name']) | set(i['m.name'] for i in a if i['m.name'] != a[0]['m.name']))[:self.num_limit])}",
            'disease_not_food': lambda
                a: f"{a[0]['m.name']}忌食的食物包括有：{';'.join(list(set(i['n.name'] for i in a))[:self.num_limit])}",
            'disease_do_food': lambda
                a: f"{a[0]['m.name']}宜食的食物包括有：{';'.join(list(set(i['n.name'] for i in a if i['r.name'] == '宜吃'))[:self.num_limit])}\n推荐食谱包括有：{';'.join(list(set(i['n.name'] for i in a if i['r.name'] == '推荐食谱'))[:self.num_limit])}",
            'food_not_disease': lambda
                a: f"患有{';'.join(list(set(i['m.name'] for i in a))[:self.num_limit])}的人最好不要吃{a[0]['n.name']}",
            'food_do_disease': lambda
                a: f"患有{';'.join(list(set(i['m.name'] for i in a))[:self.num_limit])}的人建议多试试{a[0]['n.name']}",
            'disease_drug': lambda
                a: f"{a[0]['m.name']}通常的使用的药品包括：{';'.join(list(set(i['n.name'] for i in a))[:self.num_limit])}",
            'drug_disease': lambda
                a: f"{a[0]['n.name']}主治的疾病有{';'.join(list(set(i['m.name'] for i in a))[:self.num_limit])}，可以试试",
            'drug_producer': lambda
                a: f"{a[0]['n.name']}主要有{';'.join(list(set(i['m.name'] for i in a))[:self.num_limit])}",
            'disease_check': lambda
                a: f"{a[0]['m.name']}通常可以通过以下方式检查出来：{';'.join(list(set(i['n.name'] for i in a))[:self.num_limit])}",
            'check_disease': lambda
                a: f"通常可以通过{a[0]['n.name']}检查出来的疾病有{';'.join(list(set(i['m.name'] for i in a))[:self.num_limit])}",
            'disease_department': lambda
                a: f"{a[0]['m.name']}属于{';'.join(list(set(i['n.name'] for i in a))[:self.num_limit])}",
            'disease_chinese_medicine': lambda
                a: f"{'; '.join(filter(None, {i.get('n.name', '') or i.get('m.chinese_medicine', '') for i in a}))}"
        }

        formatter = formatters.get(question_type)
        return formatter(answers) if formatter else ''


if __name__ == '__main__':
    answer = Answer()