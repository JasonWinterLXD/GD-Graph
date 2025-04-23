import urllib.request
import urllib.parse
from lxml import etree
import pymongo
from fake_useragent import UserAgent

class CrimeSpider:
    def __init__(self):
        """初始化爬虫，设置MongoDB连接和随机用户代理"""
        # 初始化MongoDB连接
        self.conn = pymongo.MongoClient()
        self.db = self.conn['medical']
        self.col = self.db['data']
        # 初始化随机用户代理以减少被识别为爬虫的风险
        self.ua = UserAgent()

    def get_html(self, url):
        """获取网页HTML内容，直接使用GBK编码并忽略解码错误"""
        # 设置随机用户代理（假设 self.ua 是随机 User-Agent 生成器）
        headers = {
            'User-Agent': self.ua.random
        }
        req = urllib.request.Request(url=url, headers=headers)
        try:
            res = urllib.request.urlopen(req)
            html = res.read()  # 获取字节内容
            # 直接使用GBK编码解码，忽略无法解码的字符
            return html.decode('gbk', errors='ignore')
        except urllib.error.URLError as e:
            print(f"网络请求失败: {e}")
            return None
        except Exception as e:
            print(f"处理URL {url} 时发生错误: {e}")
            return None

    def basicinfo_spider(self, url):
        """爬取疾病基本信息，包含错误处理"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            title = selector.xpath('//title/text()')[0]
            category = selector.xpath('//div[@class="wrap mt10 nav-bar"]/a/text()')
            desc = selector.xpath('//div[@class="jib-articl-con jib-lh-articl"]/p/text()')
            ps = selector.xpath('//div[@class="mt20 articl-know"]/p')
            infobox = [p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
                       for p in ps]
            return {
                'category': category,
                'name': title.split('的简介')[0],
                'desc': desc,
                'attributes': infobox
            }
        except (IndexError, AttributeError) as e:
            print(f"基本信息解析错误: {e}")
            return None

    def cause_spider(self, url):
        """爬取病因信息，独立方法以适应特定页面结构"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            ps = selector.xpath('//p')
            infobox = [p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
                       for p in ps if p.xpath('string(.)')]
            return '\n'.join(infobox)
        except Exception as e:
            print(f"病因信息解析错误: {e}")
            return None

    def prevent_spider(self, url):
        """爬取预防信息，独立方法以适应特定页面结构"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            ps = selector.xpath('//p')
            infobox = [p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
                       for p in ps if p.xpath('string(.)')]
            return '\n'.join(infobox)
        except Exception as e:
            print(f"预防信息解析错误: {e}")
            return None

    def symptom_spider(self, url):
        """爬取症状信息，包含错误处理"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            symptoms = selector.xpath('//a[@class="gre"]/text()')
            ps = selector.xpath('//p')
            detail = [p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
                      for p in ps]
            return symptoms, detail
        except Exception as e:
            print(f"症状信息解析错误: {e}")
            return None

    def inspect_spider(self, url):
        """爬取检查信息，包含错误处理"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            inspects = selector.xpath('//li[@class="check-item"]/a/@href')
            return inspects
        except Exception as e:
            print(f"检查信息解析错误: {e}")
            return None

    def treat_spider(self, url):
        """爬取治疗信息，包含错误处理"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            ps = selector.xpath('//div[starts-with(@class,"mt20 articl-know")]/p')
            infobox = [p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
                       for p in ps]
            return infobox
        except Exception as e:
            print(f"治疗信息解析错误: {e}")
            return None

    def food_spider(self, url):
        """爬取饮食信息，包含错误处理"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            divs = selector.xpath('//div[@class="diet-img clearfix mt20"]')
            return {
                'good': divs[0].xpath('./div/p/text()') if len(divs) > 0 else [],
                'bad': divs[1].xpath('./div/p/text()') if len(divs) > 1 else [],
                'recommand': divs[2].xpath('./div/p/text()') if len(divs) > 2 else []
            }
        except Exception as e:
            print(f"饮食信息解析错误: {e}")
            return {}

    def drug_spider(self, url):
        """爬取药物信息，包含错误处理"""
        html = self.get_html(url)
        if not html:
            return None
        selector = etree.HTML(html)
        try:
            drugs = [i.replace('\n', '').replace('\t', '').replace(' ', '')
                     for i in selector.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/text()')]
            return drugs
        except Exception as e:
            print(f"药物信息解析错误: {e}")
            return None

    def spider_main(self, disease_name="肝豆状核变性"):
        """
        主爬取方法，协调各模块爬取指定疾病数据并存储到MongoDB
        """
        for page in range(1, 11000):
            try:
                basic_url = f'http://jib.xywy.com/il_sii/gaishu/{page}.htm'
                basic_data = self.basicinfo_spider(basic_url)
                if basic_data and basic_data['name'] == disease_name:
                    print(f"找到{disease_name}的页面: {page}")
                    data = {
                        'url': basic_url,
                        'basic_info': basic_data,
                        'cause_info': self.cause_spider(f'http://jib.xywy.com/il_sii/cause/{page}.htm'),
                        'prevent_info': self.prevent_spider(f'http://jib.xywy.com/il_sii/prevent/{page}.htm'),
                        'symptom_info': self.symptom_spider(f'http://jib.xywy.com/il_sii/symptom/{page}.htm'),
                        'inspect_info': self.inspect_spider(f'http://jib.xywy.com/il_sii/inspect/{page}.htm'),
                        'treat_info': self.treat_spider(f'http://jib.xywy.com/il_sii/treat/{page}.htm'),
                        'food_info': self.food_spider(f'http://jib.xywy.com/il_sii/food/{page}.htm'),
                        'drug_info': self.drug_spider(f'http://jib.xywy.com/il_sii/drug/{page}.htm')
                    }
                    self.col.insert_one(data)
                    print(f"已爬取并存储{disease_name}的数据")
                    return  # 找到目标后退出
            except Exception as e:
                print(f"页面 {page} 出错: {e}")
        print(f"未找到{disease_name}的页面")

if __name__ == "__main__":
    """运行爬虫"""
    handler = CrimeSpider()
    handler.spider_main()