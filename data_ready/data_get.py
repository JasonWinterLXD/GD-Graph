import urllib.request
import urllib.parse
from lxml import etree
import pymongo

class CrimeSpider:
    def __init__(self):
        # 初始化MongoDB连接
        self.conn = pymongo.MongoClient()
        self.db = self.conn['medical']
        self.col = self.db['data']

    def get_html(self, url):
        # 获取网页HTML内容
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/51.0.2704.63 Safari/537.36'
        }
        req = urllib.request.Request(url=url, headers=headers)
        res = urllib.request.urlopen(req)
        html = res.read().decode('gbk')
        return html

    def basicinfo_spider(self, url):
        # 爬取疾病基本信息
        html = self.get_html(url)
        selector = etree.HTML(html)
        title = selector.xpath('//title/text()')[0]
        category = selector.xpath('//div[@class="wrap mt10 nav-bar"]/a/text()')
        desc = selector.xpath('//div[@class="jib-articl-con jib-lh-articl"]/p/text()')
        ps = selector.xpath('//div[@class="mt20 articl-know"]/p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
            infobox.append(info)
        basic_data = {}
        basic_data['category'] = category
        basic_data['name'] = title.split('的简介')[0]
        basic_data['desc'] = desc
        basic_data['attributes'] = infobox
        return basic_data

    def common_spider(self, url):
        # 爬取通用信息（如病因、预防）
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath('//p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
            if info:
                infobox.append(info)
        return '\n'.join(infobox)

    def symptom_spider(self, url):
        # 爬取症状信息
        html = self.get_html(url)
        selector = etree.HTML(html)
        symptoms = selector.xpath('//a[@class="gre"]/text()')
        ps = selector.xpath('//p')
        detail = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
            detail.append(info)
        return symptoms, detail

    def inspect_spider(self, url):
        # 爬取检查信息
        html = self.get_html(url)
        selector = etree.HTML(html)
        inspects = selector.xpath('//li[@class="check-item"]/a/@href')
        return inspects

    def treat_spider(self, url):
        # 爬取治疗信息
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath('//div[starts-with(@class,"mt20 articl-know")]/p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace('\n', '').replace('\xa0', '').replace('   ', '').replace('\t', '')
            infobox.append(info)
        return infobox

    def food_spider(self, url):
        # 爬取饮食信息
        html = self.get_html(url)
        selector = etree.HTML(html)
        divs = selector.xpath('//div[@class="diet-img clearfix mt20"]')
        try:
            food_data = {}
            food_data['good'] = divs[0].xpath('./div/p/text()')
            food_data['bad'] = divs[1].xpath('./div/p/text()')
            food_data['recommand'] = divs[2].xpath('./div/p/text()')
        except:
            return {}
        return food_data

    def drug_spider(self, url):
        # 爬取药物信息
        html = self.get_html(url)
        selector = etree.HTML(html)
        drugs = [i.replace('\n', '').replace('\t', '').replace(' ', '')
                 for i in selector.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/text()')]
        return drugs

    def spider_main(self, disease_name="肝豆状核变性"):
        # 主爬取方法，只爬取肝豆状核变性数据
        for page in range(1, 11000):
            try:
                basic_url = f'http://jib.xywy.com/il_sii/gaishu/{page}.htm'
                basic_data = self.basicinfo_spider(basic_url)
                if basic_data['name'] == disease_name:
                    print(f"找到{disease_name}的页面: {page}")
                    data = {}
                    data['url'] = basic_url
                    data['basic_info'] = basic_data
                    data['cause_info'] = self.common_spider(f'http://jib.xywy.com/il_sii/cause/{page}.htm')
                    data['prevent_info'] = self.common_spider(f'http://jib.xywy.com/il_sii/prevent/{page}.htm')
                    data['symptom_info'] = self.symptom_spider(f'http://jib.xywy.com/il_sii/symptom/{page}.htm')
                    data['inspect_info'] = self.inspect_spider(f'http://jib.xywy.com/il_sii/inspect/{page}.htm')
                    data['treat_info'] = self.treat_spider(f'http://jib.xywy.com/il_sii/treat/{page}.htm')
                    data['food_info'] = self.food_spider(f'http://jib.xywy.com/il_sii/food/{page}.htm')
                    data['drug_info'] = self.drug_spider(f'http://jib.xywy.com/il_sii/drug/{page}.htm')
                    self.col.insert_one(data)
                    # self.col.insert(data)
                    print(f"已爬取并存储{disease_name}的数据")
                    return  # 找到并爬取后退出
            except Exception as e:
                print(f"页面 {page} 出错: {e}")
        print(f"未找到{disease_name}的页面")

# 运行爬虫
if __name__ == "__main__":
    handler = CrimeSpider()
    handler.spider_main()