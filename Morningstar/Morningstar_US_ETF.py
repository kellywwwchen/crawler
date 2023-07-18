from selenium import webdriver
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

import time
import random
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')


# 抓取網頁原始碼 & 找表格的 function
def get_html_code_table(driver, tag_name, class_name):
    data = bs(driver.page_source, 'lxml')
    element = data.find(tag_name, class_ = class_name)
    table = pd.read_html(str(element))[0]
    return data, table

# 找欄位 MorningstarRating™ 星等 的 function
def get_star(bs_data, tag_name, class_name):
    value = []
    for i in bs_data.find_all(tag_name, class_ = class_name):
        if i.find('img'):
            value.append(i.find('img')['src'][5])
        else:
            value.append(np.nan)
    return value

# 找 isincode 的 function
def get_isin_code(bs_data, tag_name, class_name):
    value = []
    for i in bs_data.find_all(tag_name, class_ = class_name):
        value.append(i.find('input')['onclick'].split(',')[6].split('\\"')[3])
    return value

# 找每個列網址的 function
def get_each_row_url(bs_data, tag_name, class_name):
    value = []
    for i in bs_data.find_all(tag_name, class_ = class_name):
        value.append(i.find('a')['href'])
    return value

# 將值為 '-' 改為空值的 function
def convert_to_nan(df, column):
    for i in df[df[column].isin(['-'])].index:
        df[column][i] = np.nan
    df[column] = df[column].astype(float)

# processing each page table
def crawl_table(driver):
    # read the table
    data = bs(driver.page_source, 'html.parser')
    table = pd.read_html(str(data.find_all('div', 'ms-neat-row')[17]))[0]
    # drop unnecessary columns: "Check-box at table header"
    table.drop(['Check-box at table header'], 1, inplace = True)
    # find each item url and insert to the table)
    each_url = data.find_all('a', class_ = 'mds-link mds-link--no-underline ec-table__investment-link ng-binding')
    url_value = ['https://www.morningstar.co.uk' + u['href'] for u in each_url]
    table['url'] = url_value
    # Rating string to int
    table['Morningstar Rating™'] = table['Morningstar Rating™'].apply(lambda x:x[-1])
    table['Morningstar Sustainability Rating™'] = table['Morningstar Sustainability Rating™'].apply(lambda x:x[-1])

    # value: '-' to NaN
    table.replace('–', np.nan, inplace=True)
    return table

ua = UserAgent(verify_ssl=False)
user_agent = ua.Chrome
service = Service(executable_path='../chromedriver')
options = webdriver.ChromeOptions() 
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('user-agent={}'.format(user_agent))
options.add_argument('--disable-blink-features=AutomationControlled')
# open driver
driver = webdriver.Chrome(service=service, options=options)

# inital ETF overview df
start = time.time()
etf_df = pd.DataFrame(columns = ['ISINCode', 'Name', 'Morningstar Category', 'MorningstarRating', 'YTDReturn%', 
                                 'Total Expense Ratio %', 'LastClose', 'Currency'])
page1_url = 'https://lt.morningstar.com/89gyf3nuef/etfquickrank/default.aspx'
# 抓取第一頁的網頁原始碼 & 表格
driver.get(page1_url)
time.sleep(3)

# 利用迴圈抓取換頁表格
for i in range(2):
    
    # 除了第一頁外，其他頁要自動點選下一頁按鈕
    if i != 0:
        WebDriverWait(driver, 40).until(ec.element_to_be_clickable((By.XPATH, "//a[text()='Next']")))
        driver.find_element("xpath", "//a[text()='Next']").click()

    # 獲取下一頁表格
    etf_data, etf_table = get_html_code_table(driver, 'table', 'gridView tabSnapshot')
    # 找排名星等
    etf_table['MorningstarRating™'] = get_star(etf_data, 'td', 'msDataText gridStarRating')
    # 找isin code
    etf_table.insert(0, 'ISINCode', get_isin_code(etf_data, 'td', 'gridCheckbox'))
    # 找每列的網址
    etf_table.insert(len(etf_table.columns), 'url', get_each_row_url(etf_data, 'td', 'msDataText gridFundName Shrink'))

    # ===== 整理表格 =====
    # index從1開始
    etf_table.index = etf_table.index + 1
    # 刪除空欄
    etf_table.drop(['Unnamed: 0', 'Unnamed: 1'], 1, inplace = True)
    # 更換欄位名稱
    etf_table.rename(columns={'Morningstar® Category': 'Morningstar Category', 'MorningstarRating™': 'MorningstarRating',
                            'Unnamed: 8':'Currency'}, inplace=True)
    
    # 將下一頁表格合併至第一頁表格
    etf_df = pd.concat([etf_df, etf_table], 0, ignore_index=True)
driver.quit()

end = time.time()
print(f'時間：{end - start} 秒')