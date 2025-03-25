import os
import ahocorasick

class QuestionClassify:
    def __init__(self):
        """初始化分类器，加载特征词和构建ACTree"""
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        paths = {
            'disease': 'dict/disease.txt', 'department': 'dict/department.txt',
            'check': 'dict/check.txt', 'drug': 'dict/drug.txt', 'food': 'dict/food.txt',
            'producer': 'dict/producer.txt', 'symptom': 'dict/symptom.txt', 'deny': 'dict/deny.txt'
        }
        # 加载特征词为集合，提高查找效率
        self.wds = {k: set(self.load_words(os.path.join(cur_dir, v))) for k, v in paths.items()}
        self.region_words = set().union(*self.wds.values()) - self.wds['deny']
        self.region_tree = self.build_actree(list(self.region_words))
        self.wdtype_dict = self.build_wdtype_dict()
        # 定义疑问词
        self.qwds = {
            'symptom': ['症状', '表征', '现象', '症候', '表现'],
            'cause': ['原因', '成因', '为什么', '怎么会', '怎样才', '咋样才', '怎样会', '如何会', '为啥', '为何', '病因'],
            'acompany': ['并发症', '并发', '一起发生', '一并发生', '一起出现', '一并出现'],
            'food': ['饮食', '饮用', '吃', '食', '伙食', '膳食', '喝', '菜', '忌口', '补品'],
            'drug': ['药', '药品', '用药', '胶囊', '口服液', '炎片'],
            'prevent': ['预防', '防范', '抵制', '抵御', '防止', '躲避', '逃避', '避开'],
            'lasttime': ['周期', '多久', '多长时间', '多少时间', '几天', '几年'],
            'cureway': ['怎么治疗', '如何医治', '怎么医治', '怎么治', '怎么办', '治疗方式', '治疗', '医疗方式', '医治方式', '如何治疗'],
            'cureprob': ['多大概率能治好', '治好希望大么', '几率', '比例', '可能性', '治愈率'],
            'easyget': ['易感人群', '容易感染', '易发人群', '什么人', '哪些人'],
            'check': ['检查', '检查项目', '查出', '测出', '试出'],
            'cure': ['治疗什么', '治啥', '有什么用', '有何用', '用途'],
            'department': ['科室', '哪个科室', '什么科室', '哪个科', '什么科'],
            'chinese':['中医', '中医怎么治', '中医如何治', '中医如何治疗', '中医如何治愈', '中医如何医治', '中医怎么医治']
        }
        # print('分类器初始化完成')

    def load_words(self, path):
        """加载词典文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def classify(self, question):
        """对问题进行分类"""
        data = {}
        medical_dict = self.check_medical(question)

        # 新增：如果没有检测到疾病实体，则默认注入“肝豆状核变性”
        if not any('disease' in types for types in medical_dict.values()):
            medical_dict['肝豆状核变性'] = ['disease']

        # 修复：提取所有疾病实体
        disease_entities = []
        for wd, types in medical_dict.items():
            if 'disease' in types:
                disease_entities.append(wd)

        # 检测非目标疾病
        non_target = [d for d in disease_entities if d != '肝豆状核变性']
        data['has_other_disease'] = bool(non_target)  # 标记存在其他疾病

        data['args'] = medical_dict
        types = set(sum(medical_dict.values(), []))
        question_types = []

        # 定义分类规则
        rules = [
            (self.qwds['symptom'], 'disease', 'disease_symptom'),
            (self.qwds['symptom'], 'symptom', 'symptom_disease'),
            (self.qwds['cause'], 'disease', 'disease_cause'),
            (self.qwds['acompany'], 'disease', 'disease_acompany'),
            (self.qwds['food'], 'disease', lambda q: 'disease_not_food' if self.check_words(self.wds['deny'], q) else 'disease_do_food'),
            (self.qwds['food'] + self.qwds['cure'], 'food', lambda q: 'food_not_disease' if self.check_words(self.wds['deny'], q) else 'food_do_disease'),
            (self.qwds['drug'], 'disease', 'disease_drug'),
            (self.qwds['cure'], 'drug', 'drug_disease'),
            (self.qwds['check'], 'disease', 'disease_check'),
            (self.qwds['check'] + self.qwds['cure'], 'check', 'check_disease'),
            (self.qwds['prevent'], 'disease', 'disease_prevent'),
            (self.qwds['lasttime'], 'disease', 'disease_lasttime'),
            (self.qwds['cureway'], 'disease', 'disease_cureway'),
            (self.qwds['cureprob'], 'disease', 'disease_cureprob'),
            (self.qwds['easyget'], 'disease', 'disease_easyget'),
            (self.qwds['department'], 'disease', 'disease_department'),
            (self.qwds['chinese'], 'disease', 'disease_chinese')
        ]

        for qwds, type_, qt in rules:
            if self.check_words(qwds, question) and type_ in types:
                question_types.append(qt(question) if callable(qt) else qt)

        # 默认分类
        if not question_types:
            question_types = ['disease_desc'] if 'disease' in types else ['symptom_disease']

        data['question_types'] = question_types
        return data

    def build_wdtype_dict(self):
        """构造词类型字典"""
        wd_dict = {}
        for wd in self.region_words:
            wd_dict[wd] = [k for k, wds in self.wds.items() if wd in wds and k != 'deny']
        return wd_dict

    def build_actree(self, wordlist):
        """构建ACTree加速匹配"""
        actree = ahocorasick.Automaton()
        for i, word in enumerate(wordlist):
            actree.add_word(word, (i, word))
        actree.make_automaton()
        return actree

    def check_medical(self, question):
        """过滤问句中的医疗相关词"""
        region_wds = [i[1][1] for i in self.region_tree.iter(question)]
        stop_wds = {wd1 for wd1 in region_wds for wd2 in region_wds if wd1 in wd2 and wd1 != wd2}
        final_wds = [wd for wd in region_wds if wd not in stop_wds]
        return {wd: self.wdtype_dict[wd] for wd in final_wds}

    def check_words(self, wds, sent):
        """检查特征词是否在句子中"""
        return any(wd in sent for wd in wds)

if __name__ == '__main__':
    handler = QuestionClassify()
    while True:
        question = input('请输入问题：')
        data = handler.classify(question)
        print(data)