class QuestionAnalyse:
    def build_entitydict(self, args):
        """构建实体字典，使用集合去重"""
        entity_dict = {}
        for arg, types in args.items():
            if arg == '肝豆状核变性' and 'disease' in types:
                types = ['disease']  # 强制标记为疾病类型
            for t in types:
                entity_dict.setdefault(t, set()).add(arg)
        return {k: list(v) for k, v in entity_dict.items()}

    def analyse_main(self, res_classify):
        """解析主函数，生成SQL查询语句"""
        args = res_classify['args']
        entity_dict = self.build_entitydict(args)
        question_types = res_classify['question_types']
        return [sql for sql in (self.get_sql(qt, entity_dict) for qt in question_types) if sql]

    def get_sql(self, question_type, entity_dict):
        """根据问题类型生成SQL"""
        entities = entity_dict.get(question_type.split('_')[0], [])
        if not entities:
            return None
        sql = self.sql_transfer(question_type, entities)
        return {'question_type': question_type, 'sql': sql}

    def sql_transfer(self, question_type, entities):
        """针对不同问题类型生成Cypher查询语句"""
        if not entities:
            return []

        sql_map = {
            'disease_cause': "MATCH (m:Disease) WHERE m.name = '{0}' RETURN m.name, m.cause",
            'disease_prevent': "MATCH (m:Disease) WHERE m.name = '{0}' RETURN m.name, m.prevent",
            'disease_lasttime': "MATCH (m:Disease) WHERE m.name = '{0}' RETURN m.name, m.cure_lasttime",
            'disease_cureprob': "MATCH (m:Disease) WHERE m.name = '{0}' RETURN m.name, m.cured_prob",
            'disease_cureway': "MATCH (m:Disease) WHERE m.name = '{0}' RETURN m.name, m.cure_way",
            'disease_easyget': "MATCH (m:Disease) WHERE m.name = '{0}' RETURN m.name, m.easy_get",
            'disease_desc': "MATCH (m:Disease) WHERE m.name = '{0}' RETURN m.name, m.desc",
            'disease_symptom': "MATCH (m:Disease)-[r:has_symptom]->(n:Symptom) WHERE m.name = '{0}' RETURN m.name, r.name, n.name",
            'symptom_disease': "MATCH (m:Disease)-[r:has_symptom]->(n:Symptom) WHERE n.name = '{0}' RETURN m.name, r.name, n.name",
            'disease_not_food': "MATCH (m:Disease)-[r:no_eat]->(n:Food) WHERE m.name = '{0}' RETURN m.name, r.name, n.name",
            'disease_check': "MATCH (m:Disease)-[r:need_check]->(n:Check) WHERE m.name = '{0}' RETURN m.name, r.name, n.name",
            'check_disease': "MATCH (m:Disease)-[r:need_check]->(n:Check) WHERE n.name = '{0}' RETURN m.name, r.name, n.name",
            'disease_department': "MATCH (m:Disease)-[r:belongs_to]->(n:Department) WHERE m.name = '{0}' RETURN m.name, n.name",
            'disease_chinese': lambda e: [
                f"MATCH (m:Disease)-[r:chinese_cure]->(n:Chinese) WHERE m.name = '{e}' RETURN m.name, r.name, n.name",
                f"MATCH (m:Disease) WHERE m.name = '{e}' RETURN m.name, m.chinese"
            ],
            'drug_disease': lambda e: [
                f"MATCH (m:Disease)-[r:common_drug]->(n:Drug) WHERE n.name = '{e}' RETURN m.name, r.name, n.name",
                f"MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) WHERE n.name = '{e}' RETURN m.name, r.name, n.name"
            ],
            'disease_drug': lambda e: [
                f"MATCH (m:Disease)-[r:common_drug]->(n:Drug) WHERE m.name = '{e}' RETURN m.name, r.name, n.name",
                f"MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) WHERE m.name = '{e}' RETURN m.name, r.name, n.name"
            ],
            'disease_do_food': lambda e: [
                f"MATCH (m:Disease)-[r:do_eat]->(n:Food) WHERE m.name = '{e}' RETURN m.name, r.name, n.name",
                f"MATCH (m:Disease)-[r:recommand_eat]->(n:Food) WHERE m.name = '{e}' RETURN m.name, r.name, n.name"
            ],
            'food_do_disease': lambda e: [
                f"MATCH (m:Disease)-[r:do_eat]->(n:Food) WHERE n.name = '{e}' RETURN m.name, r.name, n.name",
                f"MATCH (m:Disease)-[r:recommand_eat]->(n:Food) WHERE n.name = '{e}' RETURN m.name, r.name, n.name"
            ],
            'food_not_disease': "MATCH (m:Disease)-[r:no_eat]->(n:Food) WHERE n.name = '{0}' RETURN m.name, r.name, n.name",
            'disease_acompany': lambda e: [
                f"MATCH (m:Disease)-[r:acompany_with]->(n:Disease) WHERE m.name = '{e}' RETURN m.name, r.name, n.name",
                f"MATCH (m:Disease)-[r:acompany_with]->(n:Disease) WHERE n.name = '{e}' RETURN m.name, r.name, n.name"
            ]
        }

        formatter = sql_map.get(question_type)
        if callable(formatter):
            return sum([formatter(e) for e in entities], [])
        elif formatter:
            return [formatter.format(e) for e in entities]
        return []

if __name__ == '__main__':
    handler = QuestionAnalyse()