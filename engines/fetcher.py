from engines.engine import job_engine, Fetcher
from models.symbol import Symbol
from models.zhangting import ZhangTing
from datetime import datetime
from candles.finance import clean_data, fetch_and_save
import efinance as ef
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from models.review import Review
import time
import re


@job_engine
class Candles(Fetcher):

    def fetch(self):
        now = datetime.now()
        freq = [101, 120, 60, 30]
        clean = False
        if now.weekday() == 5:
            freq.append(102)
        if now.day == 1:
            clean = True
            freq.append(103)

        sbs = Symbol.actives()
        count = 0
        for sb in sbs:
            try:
                print('[{}] {} fetch candles [{}] start!'.format(datetime.now(), count, sb.code))
                if clean:
                    clean_data(sb.code)
                for fr in freq:
                    fetch_and_save(sb.code, fr)
                print('[{}] {} fetch candles [{}] done!'.format(datetime.now(), count, sb.code))
                count = count + 1
            except Exception as ex:
                print('fetch candles [{}] error!'.format(sb.code), ex)
        print('[{}] fetch all done! elapsed time:{}'.format(datetime.now(), datetime.now() - now))


@job_engine
class Symbols(Fetcher):

    def fetch(self):
        df = ef.stock.get_realtime_quotes(['沪A', '深A'])
        df = df.iloc[:, 0:2]
        df.columns = ['code', 'name']
        for i, row in df.iterrows():
            code = row['code']
            name = row['name']
            if 'ST' in row['name'] or str(code).startswith('688'):
                continue
            else:
                series = ef.stock.get_base_info(row['code'])
                print('upset symbol code =', row['code'], ',name =', row['name'], i)
                if Symbol.select().where(Symbol.code == code).exists():
                    symbol = Symbol.get(Symbol.code == code)
                else:
                    symbol = Symbol()
                    symbol.code = code
                    symbol.updated = datetime.now()
                symbol.name = name
                for k in series.keys():
                    val = series[k]
                    if str(k).startswith('净利润'):
                        symbol.profit = val if isinstance(val, float) else 0.0
                    elif str(k).startswith('总市值'):
                        symbol.total = val if isinstance(val, float) else 0.0
                    elif str(k).startswith('流通市值'):
                        symbol.circulating = val if isinstance(val, float) else 0.0
                    elif str(k).startswith('所处行业'):
                        symbol.industry = val
                    elif str(k).startswith('市盈率'):
                        symbol.pe = val if isinstance(val, float) else 0.0
                    elif k == '市净率':
                        symbol.pb = val if isinstance(val, float) else 0.0
                    elif k == 'ROE':
                        symbol.roe = val if isinstance(val, float) else 0.0
                    elif k == '毛利率':
                        symbol.gross = val if isinstance(val, float) else 0.0
                    elif k == '净利率':
                        symbol.net = val if isinstance(val, float) else 0.0
                    elif k == '板块编号':
                        symbol.sector = val
                if symbol.industry in ['银行', '房地产开发', '房地产服务', '装修建材']:
                    symbol.status = 0
                    symbol.comment = '剔除行业'
                # elif symbol.total < 5000000000 or symbol.circulating < 3000000000:
                #     symbol.status = 0
                #     symbol.comment = '小市值'
                else:
                    symbol.status = 1
                symbol.is_watch = 0
                symbol.created = datetime.now()
                symbol.save()


class ChromeDriver:

    def __init__(self):
        print("=====chrome driver start=====")
        options = webdriver.ChromeOptions()
        options.binary_location = r"D:\Huangsy\chrome\chrome\chrome.exe"
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        service = Service('D:\\Huangsy\\chrome\\chromedriver\\chromedriver.exe')
        self.driver = webdriver.Chrome(service=service, options=options)

    def access(self, url, wait=2):
        self.driver.get(url)
        time.sleep(wait)

    def element(self, xpath, timeout=20, parent=None):
        try:
            if parent is not None:
                xpath = self._xpath(parent) + xpath[1:] if xpath.startswith('.') else xpath

            el = WebDriverWait(self.driver, timeout).until(expected_conditions.presence_of_element_located(
                (By.XPATH, xpath)))
            return el
        except Exception as e:
            print('[Error]', str(e))
            return None

    def _xpath(self, element):
        return self.driver.execute_script("""
            function generateXPath(elt) {
                let path = '';
                for (; elt && elt.nodeType === 1; elt = elt.parentNode) {
                    let idx = 1;
                    let sib = elt.previousSibling;
                    while (sib) {
                        if (sib.nodeType === 1 && sib.tagName === elt.tagName) idx++;
                        sib = sib.previousSibling;
                    }
                    path = '/' + elt.tagName.toLowerCase() + (idx > 1 ? `[${idx}]` : '') + path;
                }
                return path;
            }
            return generateXPath(arguments[0]);
        """, element)

    def text(self, xpath, timeout=20, wait=1, parent=None):
        el = self.element(xpath, timeout, parent=parent)
        if el is not None:
            time.sleep(wait)
            return el.text

    def click(self, xpath, timeout=20, wait=1, parent=None):
        el = self.element(xpath, timeout, parent=parent)
        if el is not None:
            time.sleep(wait)
            el.click()

    def input(self, xpath, value, timeout=20, wait=1, parent=None):
        el = self.element(xpath, timeout, parent=parent)
        if el is not None:
            time.sleep(wait)
            el.clear()
            el.send_keys(value)

    def is_present(self, xpath, parent=None):
        if parent is not None:
            xpath = self._xpath(parent) + xpath[1:] if xpath.startswith('.') else xpath
        ele = self.element(xpath, timeout=1)
        return ele is not None

    def quit(self):
        print("=====chrome driver quit=====")
        self.driver.quit()


@job_engine
class DailyReview(Fetcher):
    def fetch(self):
        chrome = ChromeDriver()
        try:
            review = Review()
            pan_data = ''
            chrome.access('https://www.cls.cn/finance')

            # 成交量、涨停数、上证指數
            pan_data = pan_data + '成交量：{} \n 涨停：{} \n 上证：{}({})\n'.format(
                chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div/div[1]/div[2]/div/div/div/div[2]/div[1]/div[2]'),
                chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div/div[1]/div[2]/div/div/div/div[1]/div[2]/span[1]'),
                chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div/div[1]/div[1]/div/div[1]/a[1]/div'),
                chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div/div[1]/div[1]/div/div[1]/a[2]/div')
            )

            # 上涨数
            chrome.access('https://www.cls.cn/quotation')
            pan_data = pan_data + '上涨：{} \n'.format(
                chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div[2]/div[3]/div[1]/span[2]'))
            pan_data = pan_data
            review.pan_data = pan_data

            # 今日总结
            chrome.access('https://www.cls.cn/subject/1139')
            review.pan_summary = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/a')

            # 今日焦点
            chrome.access('https://www.cls.cn/subject/1135')
            review.pan_focus = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/a')

            # 板块，流入流出
            chrome.access('https://www.cls.cn/hotPlate')
            bk_in, bk_out = '', ''
            for i in range(1, 7):
                bk_info = '{}({} {})，'.format(
                    chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[1]/div[2]/a[{}]/div[2]'.format(i)),
                    chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[1]/div[2]/a[{}]/div[3]/div[1]/span[2]'.format(i)),
                    chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[1]/div[2]/a[{}]/div[3]/div[2]/span[2]'.format(i))
                )
                if i < 4:
                    bk_in = bk_in + bk_info
                else:
                    bk_out = bk_out + bk_info
            review.bk_in, review.bk_out = bk_in, bk_out

            # 板块，潜力
            bk_ql = ''
            for i in range(2, 5):
                el_bk_ql_name = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div/div[1]/div[{}]/div[1]/div[2]/div[1]/a'.format(i))
                el_bk_ql_comment = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div/div[1]/div[{}]/div[2]/ul/li/a'.format(i))
                el_bk_ql_gp1 = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div/div[1]/div[{}]/div[3]/div[1]/a'.format(i))
                el_bk_ql_gp2 = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div/div[1]/div[{}]/div[3]/div[2]/a'.format(i))
                bk_ql = bk_ql + '{}。{}, {}、{} \n'.format(el_bk_ql_name, el_bk_ql_comment, el_bk_ql_gp1, el_bk_ql_gp2)
            review.bk_ql = bk_ql

            # 板块 风口
            bk_fk = ''
            for i in range(2, 5):
                el_bk_fk_name = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div/div[2]/div[{}]/div[1]/div[2]/div[1]/a'.format(i))
                el_bk_fk_comment = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div/div[2]/div[{}]/div[2]/div'.format(i))
                el_bk_fk_gp = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[2]/div/div[2]/div[{}]/div[3]/div/a'.format(i))
                bk_fk = bk_fk + '{}。{}, {} \n'.format(el_bk_fk_name, el_bk_fk_comment,el_bk_fk_gp)
            review.bk_fk = bk_fk

            # 热股
            gp_hot1 = ''
            chrome.access('https://api3.cls.cn/quote/toplist')
            hot_list = chrome.driver.find_elements(By.CLASS_NAME, 'hot-list-right-box')
            j = 1
            for el in hot_list:
                els = el.find_elements(By.CLASS_NAME, 'openapp')
                flag = False
                # print('No.', j)
                for el2 in els:
                    final_str = re.sub(r"^\s+|\s+$", "", el2.text)
                    txt = final_str.split('\n')
                    if txt != '':
                        i = 0
                        for t in txt:
                            if t != '\n':
                                gp_hot1 = gp_hot1 + t
                                flag = True
                                # print(i, t)
                                i = i + 1
                if flag:
                    gp_hot1 = gp_hot1 + '\n'
                j = j + 1
            review.gp_hot1 = gp_hot1
            review.created = datetime.now()
            review.save()
        finally:
            chrome.quit()


@job_engine
class DailyHot(Fetcher):
    def fetch(self):
        pass


@job_engine
class DailyZhangTing(Fetcher):
    def fetch(self):
        chrome = ChromeDriver()
        chrome.access('https://www.jiuyangongshe.com/action')
        chrome.click('//div[@class="active"]')
        chrome.click('//div[@id="tab-accounts"]')
        chrome.input('//div[@id="pane-accounts"]//input[@name="phone"]', '13631367271')
        chrome.input('//div[@id="pane-accounts"]//input[@name="password"]', 'hsy841121')
        chrome.click('//div[@id="pane-accounts"]//button[@type="button"]')
        time.sleep(3)
        chrome.driver.refresh()
        time.sleep(5)
        modules = chrome.driver.find_elements(By.CLASS_NAME, "module")

        for i in range(1, len(modules)):
            module = chrome.element('//*[@id="__layout"]/div/div[2]/div/div/section/ul/li[{}]'.format(i+1))
            parent = module.find_element(By.XPATH, ".//div[contains(@class, 'parent')]/div[1]")
            lis = module.find_elements(By.TAG_NAME, 'li')
            for li in lis:
                bk = parent.text
                shrinks = li.find_elements(By.XPATH, ".//div[contains(@class, 'shrink')]")
                name = shrinks[0].get_attribute("innerText")
                code = shrinks[1].get_attribute("innerText")
                price = shrinks[2].get_attribute("innerText")
                zf = shrinks[3].get_attribute("innerText")
                ztt = shrinks[4].get_attribute("innerText")
                comment = li.find_element(By.XPATH, ".//pre[contains(@class, 'pre')]/a").get_attribute("innerText")
                comment = comment.split('\n')[0]
                # for shrink in shrinks:
                #     print(shrink.get_attribute("innerText"))
                ZhangTing.add(code, name, bk, price, zf, ztt, comment)
        chrome.quit()


