import os
import json
from neo4j import GraphDatabase

class MedicalGraph:
    def __init__(self):
        # 获取当前文件目录，确保跨平台兼容性
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(cur_dir, 'data_ready/data.json')
        # 初始化Neo4j数据库连接
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))

    def read_nodes(self):
        """读取JSON文件并提取节点和关系数据"""
        # 定义节点类型列表
        checks, departments, diseases, drugs = [], [], [], []
        foods, producers, symptoms, disease_infos, chinese = [], [], [], [], []
        # 定义关系类型列表
        rels_department, rels_noteat, rels_doeat = [], [], []
        rels_recommandeat, rels_commonddrug, rels_recommanddrug = [], [], []
        rels_check, rels_drug_producer, rels_symptom = [], [], []
        rels_acompany, rels_category, rels_chinese = [], [], []

        count = 0
        with open(self.data_path) as f:
            for data in f:
                count += 1
                print(f"处理第 {count} 条数据")
                data_json = json.loads(data)
                disease = data_json['name']
                diseases.append(disease)
                disease_dict = {
                    'name': disease, 'desc': '', 'prevent': '', 'cause': '',
                    'easy_get': '', 'cure_department': '', 'cure_way': '',
                    'cure_lasttime': '', 'symptom': '', 'cured_prob': ''
                }

                # 处理症状
                if 'symptom' in data_json:
                    symptoms.extend(data_json['symptom'])
                    rels_symptom.extend([[disease, s] for s in data_json['symptom']])

                # 处理中医治疗
                if 'chinese' in data_json:
                    chinese.append(data_json['chinese'])
                    # rels_chinese.append([[disease, t] for t in data_json['chinese']])
                    rels_chinese.append([disease, data_json['chinese']])

                # 处理并发症
                if 'acompany' in data_json:
                    rels_acompany.extend([[disease, a] for a in data_json['acompany']])

                # 更新疾病属性
                for key in ['desc', 'prevent', 'cause', 'get_prob', 'easy_get', 
                          'cure_lasttime', 'cured_prob', 'cure_way']:
                    if key in data_json:
                        disease_dict[key if key != 'get_prob' else 'cured_prob'] = data_json[key]

                # 处理科室
                if 'cure_department' in data_json:
                    cure_dept = data_json['cure_department']
                    if len(cure_dept) == 1:
                        rels_category.append([disease, cure_dept[0]])
                    elif len(cure_dept) == 2:
                        rels_department.append([cure_dept[1], cure_dept[0]])
                        rels_category.append([disease, cure_dept[1]])
                    disease_dict['cure_department'] = cure_dept
                    departments.extend(cure_dept)

                # 处理药物
                if 'common_drug' in data_json:
                    drugs.extend(data_json['common_drug'])
                    rels_commonddrug.extend([[disease, d] for d in data_json['common_drug']])
                if 'recommand_drug' in data_json:
                    drugs.extend(data_json['recommand_drug'])
                    rels_recommanddrug.extend([[disease, d] for d in data_json['recommand_drug']])

                # 处理食物
                for food_type, rel_list in [('not_eat', rels_noteat), ('do_eat', rels_doeat), 
                                          ('recommand_eat', rels_recommandeat)]:
                    if food_type in data_json:
                        foods.extend(data_json[food_type])
                        rel_list.extend([[disease, f] for f in data_json[food_type]])

                # 处理检查
                if 'check' in data_json:
                    checks.extend(data_json['check'])
                    rels_check.extend([[disease, c] for c in data_json['check']])

                # 处理药品生产商
                if 'drug_detail' in data_json:
                    for detail in data_json['drug_detail']:
                        producer, drug = detail.split('(')[0], detail.split('(')[-1].replace(')', '')
                        producers.append(producer)
                        rels_drug_producer.append([producer, drug])

                disease_infos.append(disease_dict)

        # 返回去重后的集合和关系列表
        return (set(drugs), set(foods), set(checks), set(departments), set(producers), 
                set(symptoms), set(diseases), set(chinese), disease_infos, rels_check, rels_recommandeat,
                rels_noteat, rels_doeat, rels_department, rels_commonddrug, rels_drug_producer, 
                rels_recommanddrug, rels_symptom, rels_acompany, rels_category, rels_chinese)

    def create_node(self, label, nodes):
        """批量创建节点"""
        with self.driver.session() as session:
            session.run(f"UNWIND $nodes AS node CREATE (n:{label} {{name: node}})", 
                       nodes=list(nodes))
        print(f"创建 {len(nodes)} 个 {label} 节点")

    def create_diseases_nodes(self, disease_infos):
        """创建疾病节点，包含属性"""
        with self.driver.session() as session:
            for i, d in enumerate(disease_infos, 1):
                session.run(
                    "CREATE (n:Disease {name: $name, desc: $desc, prevent: $prevent, cause: $cause, "
                    "easy_get: $easy_get, cure_lasttime: $cure_lasttime, cure_department: $cure_department, "
                    "cure_way: $cure_way, cured_prob: $cured_prob})",
                    **d)
                print(f"创建第 {i} 个疾病节点")

    def create_graphnodes(self):
        """创建所有类型的节点"""
        nodes_data = self.read_nodes()
        Drugs, Foods, Checks, Departments, Producers, Symptoms, Diseases, Chinese, disease_infos = nodes_data[:9]
        self.create_diseases_nodes(disease_infos)
        for label, nodes in [('Drug', Drugs), ('Food', Foods), ('Check', Checks), 
                           ('Department', Departments), ('Producer', Producers), ('Symptom', Symptoms), ('Chinese', Chinese)]:
            self.create_node(label, nodes)

    def create_relationship(self, start_label, end_label, edges, rel_type, rel_name):
        """批量创建关系"""
        with self.driver.session() as session:
            set_edges = set('###'.join(edge) for edge in edges)
            for i, edge in enumerate(set_edges, 1):
                p, q = edge.split('###')
                session.run(
                    f"MATCH (p:{start_label} {{name: $p_name}}), (q:{end_label} {{name: $q_name}}) "
                    f"CREATE (p)-[rel:{rel_type} {{name: $rel_name}}]->(q)",
                    p_name=p, q_name=q, rel_name=rel_name)
                print(f"创建关系 {rel_type}: {i}/{len(set_edges)}")

    def create_graphrels(self):
        """创建所有关系"""
        rels_data = self.read_nodes()[9:]
        rel_configs = [
            ('Disease', 'Food', rels_data[1], 'recommand_eat', '推荐食谱'),
            ('Disease', 'Food', rels_data[2], 'no_eat', '忌吃'),
            ('Disease', 'Food', rels_data[3], 'do_eat', '宜吃'),
            ('Department', 'Department', rels_data[4], 'belongs_to', '属于'),
            ('Disease', 'Drug', rels_data[5], 'common_drug', '常用药品'),
            ('Producer', 'Drug', rels_data[6], 'drugs_of', '生产药品'),
            ('Disease', 'Drug', rels_data[7], 'recommand_drug', '好评药品'),
            ('Disease', 'Check', rels_data[0], 'need_check', '诊断检查'),
            ('Disease', 'Symptom', rels_data[8], 'has_symptom', '症状'),
            ('Disease', 'Disease', rels_data[9], 'acompany_with', '并发症'),
            ('Disease', 'Department', rels_data[10], 'belongs_to', '所属科室'),
            ('Disease', 'Chinese', rels_data[11], 'chinese_cure', '中医治疗')
        ]
        for config in rel_configs:
            self.create_relationship(*config)

    def export_data(self):
        """导出数据到文件"""
        nodes = self.read_nodes()[:7]
        for name, data in zip(['drug', 'food', 'check', 'department', 'producer', 'symptoms', 'disease'], nodes):
            with open(f'{name}.txt', 'w') as f:
                f.write('\n'.join(data))

if __name__ == '__main__':
    handler = MedicalGraph()
    handler.create_graphnodes()
    handler.create_graphrels()
    # handler.export_data()  # 可选执行