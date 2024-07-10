# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# Imports 
import sqlite3   
from selenium import webdriver                                          
from selenium.webdriver.chrome.service import Service                   
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
from login import psw 
from login import email
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# 1.Initialisation
print("\n- - - - - - - - - - - - - - - - -")
print("    Initialisation")
Path_recherche = input("    Enter path link : ")
pays = input("    Enter country : ")
print("- - - - - - - - - - - - - - - - -")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# 2.Driver
options = webdriver.ChromeOptions()
options.add_argument("--new-window")
options.add_argument("--single-process")
#(if you dont want open a windows)
#options.add_argument("--headless")
#options.add_argument("--disable-gpu")
#options.add_argument("--no-sandbox")
options.add_experimental_option("detach", True)
s = Service("YOUR PATH") #the path of your chromedriver
driver = webdriver.Chrome(service=s, options=options)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# 3.Start search
driver.get(Path_recherche) #start the driver with our link
time.sleep(5) #wait 5s -> to be sure the page is downloaded
print("\n- - - - - - - - - - - - - - - - -")
print("Scrapping process : START")
print("    --> Open Window")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# 4.Auth / Scrapping
sign_in = driver.find_element(By.PARTIAL_LINK_TEXT, "Sign in")
sign_in.click()
time.sleep(2)

# -> input email
print("    Authentification")
email_login = driver.find_element(By.ID, "username")
email_login.send_keys(email) # send our email (login.py) with send_key method
time.sleep(2)

# -> input psw
password = driver.find_element(By.ID, "password")
password.send_keys(psw)
time.sleep(5)

# -> enter button
password.send_keys(Keys.ENTER) # use Enter method to login
print("    Connexion")
time.sleep(10)
print("    --> Scraping process : OK\n")


results_list = driver.find_element(By.CLASS_NAME, "jobs-search-results-list")
nb_page = 41
page_act = 1
n = 1
total_elements = 25 #number of offer in 1 page

# database creation (if not exist)

conn = sqlite3.connect('Scrap_Lkdn.db') #name your database as you want .db
c = conn.cursor() #open database
c.execute(f'''
    CREATE TABLE IF NOT EXISTS {pays} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pays TEXT,
        title TEXT,
        company TEXT,
        description TEXT
    );
''')
conn.commit() #execute the sql script
conn.close() #close the database

# now, we are créate the scrap loop (we are looping in the 25 offers of each page and scrap the title offer, 
#company's name, description...)

while page_act < nb_page: # while our actual page is < total page (they are 40 page possible in linkedin, but we want the 40th too, so we'll use 41 instead 40)
    print("- - - - - - - - - page : ", page_act)
    for i in range(total_elements): # i  is the ranking position of every title offer in linkedin on 25
        try:
            css_selector = f".jobs-search-two-pane__job-card-container--viewport-tracking-{i}"
            element_to_click = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
            try:
                element_to_click.click() # trying to click on the [i] offer link
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", element_to_click)
            time.sleep(5)

            css_selector_text = f".jobs-search__job-details--container" # 1.find the clickable offer
            element_to_click = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector_text)))
            title_element = driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title h1.t-24") # 2.find the title to scrap
            company_element = driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name a") #3.find the company name
            description_element = driver.find_element(By.CSS_SELECTOR, "#job-details") #4.find the job description

            title = title_element.text # put the title in a variable
            company = company_element.text # same for company
            description = description_element.text # same for description

            if title and company and description: #we want add only 100% completed data in our database, if it miss on of the 3 elements, we will not add it
                conn = sqlite3.connect('Scrap_Lkdn.db') #connect to the database
                c = conn.cursor() #take controle of the database
                c.execute(f"INSERT INTO {pays} (pays, title, company, description) VALUES (?,?,?,?)", (pays, title, company, description)) # create a table named with the country we choose and add it the data
                conn.commit()
                conn.close()
                print("Job -", n, " | ", title[:30])
                driver.execute_script("arguments[0].scrollBy(0,500);", results_list) # we need to scrool to download the next jobs offers on the page
                time.sleep(2)
                n += 1 #increment n (because we are going to scrap the next [i] job offer)
            else:
                print("    SKIP - - - - not complete")
        except NoSuchElementException:
            print("    SKIP - - - - downloading")
    
    try:
        xpath_expression = f'//li[@data-test-pagination-page-btn="{page_act + 1}"]' # we are going to change the page
        next_page = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath_expression)))

#'''they are just the 8 first page available for click action, so we need to click on ... after the 8th'''

        try:
            next_page.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", next_page)
        time.sleep(5)
    except (NoSuchElementException, TimeoutException):
        try:
            xpath_expression2 = f'//button[@aria-label="Page {page_act + 1}"]'
            next_page = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath_expression2)))
            try:
                next_page.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", next_page)
            time.sleep(5)
        except (NoSuchElementException, TimeoutException):
            print(f"The page {page_act + 1} is missing !!!")
            break
    page_act += 1


            
            









