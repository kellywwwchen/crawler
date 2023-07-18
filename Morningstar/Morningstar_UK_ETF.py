from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import numpy as np
import random
import time
import warnings
warnings.filterwarnings('ignore')

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
etf_overview_df = pd.DataFrame(columns = ['Name', 'Symbol', 'Last Close Price', 'Yield (%)', 'Ongoing Charge (%)', 'Morningstar Category', 
                                          'Morningstar Medalist Rating™', 'Morningstar Rating™', 'Morningstar Sustainability Rating™', 'url'])
# input url
url = 'https://www.morningstar.co.uk/uk/screener/etf.aspx#?filtersSelectedValue=%7B%22brandingCompanyId%22:%7B%22id%22:%22BN00000AEO%22%7D%7D&sortField=legalName&sortOrder=asc'
driver.get(url)
time.sleep(random.randint(5, 7))

# click the cookie button
driver.find_element(By.ID,"onetrust-accept-btn-handler") 
time.sleep(random.randint(3, 6))

# click the "I’m an individual investor" button
driver.find_element(By.ID,'btn_individual')
time.sleep(random.randint(5, 7))

# select the drop-down menu: 50
select_row = Select(driver.find_element(By.ID,'ec-screener-input-page-size-select'))
select_row.select_by_visible_text('50')
time.sleep(random.randint(7, 10))

# each page, i = the number of pages
for i in range(2):
    if i!=0:
       # click the "Next" button
       element = driver.find_element(By.LINK_TEXT, "Next")
       driver.execute_script("arguments[0].click();", element)
       # WebDriverWait(driver,60).until(EC.element_to_be_clickable((By.LINK_TEXT, "Next")))
       time.sleep(random.randint(3,5))
       
    tmp = crawl_table(driver)
    # concat to init df 
    etf_overview_df = pd.concat([etf_overview_df, tmp], 0, ignore_index=True)
    print('======= page', i+1,'Done ========', len(etf_overview_df))
    time.sleep(random.randint(3, 5))

driver.quit()