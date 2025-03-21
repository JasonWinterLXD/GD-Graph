from question_classify import QuestionClassify
from question_analyse import QuestionAnalyse
from answer import Answer

class ChatGDGraph:
    def __init__(self):
        """初始化问答机器人"""
        self.classify = QuestionClassify()
        self.analyse = QuestionAnalyse()
        self.answer = Answer()

    def chat_main(self, sent):
        """处理用户输入并返回答案"""
        try:
            res_classify = self.classify.classify(sent)
            if not res_classify:
                return '没能理解您的问题，我的词汇量有限，请输入更加标准的词语'

            # 新增：检测其他疾病
            if res_classify.get('has_other_disease', False):
                return '本系统专门解答肝豆状核变性相关问题，请勿输入其他疾病名称'

            # 新增：如果没有疾病实体，自动注入默认疾病
            args = res_classify.get('args', {})
            if not any('disease' in types for types in args.values()):
                res_classify['args']['肝豆状核变性'] = ['disease']

            res_sql = self.analyse.analyse_main(res_classify)
            final_answers = self.answer.search_main(res_sql)
            return '\n'.join(final_answers) if final_answers else '没能找到答案'
        except Exception as e:
            print(f"错误: {e}")
            return '抱歉，系统出现错误'

if __name__ == '__main__':
    handler = ChatGDGraph()
    while True:
        question = input('咨询：')
        # question = input('咨询（输入"exit"退出）：')
        # if question.lower() == 'exit':
        #     break
        answer = handler.chat_main(question)
        print('客服机器人:', answer)