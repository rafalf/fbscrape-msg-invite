from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


cfg = {}
with open('creds.conf') as hlr:
    for line in hlr:
        split_line = line.split('::')
        cfg[split_line[0]] = split_line[1].strip()


prefs = {"profile.default_content_setting_values.notifications" : 2}
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(chrome_options=chrome_options)
driver.maximize_window()


def main():

    invitees = ['andrew.andrew.12576', 'ovidiu.marius.79']

    driver.get('https://www.facebook.com')

    # login
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(cfg['user_email'])
    driver.find_element_by_css_selector('#pass').send_keys(cfg['user_pass'])
    time.sleep(1)
    driver.find_element_by_css_selector('#loginbutton').click()

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'pagelet_bluebar')))

    event_url = 'https://www.facebook.com/events/1736841879967628/'
    driver.get(event_url)

    driver.execute_script("window.scrollTo(0, 200)")

    el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fbEventClassicButton ._42ft')))
    actions = ActionChains(driver)
    actions.move_to_element(el)
    actions.perform()

    el = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '._54nf li:nth-of-type(2)')))
    actions = ActionChains(driver)
    actions.move_to_element(el)
    actions.click(el)
    actions.perform()

    # event = 'click'  # or 'hover' or any other
    # script = "$('._54nf li:nth-of-type(3) ._54nc').trigger('" + event + "')"
    # print script
    # driver.execute_script(script)

    time.sleep(1)

if __name__ == '__main__':
    main()
    driver.quit()