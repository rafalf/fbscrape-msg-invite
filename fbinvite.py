from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time
import os
import logging
import sys


cfg = {}
with open('creds.conf') as hlr:
    for line in hlr:
        split_line = line.split('::')
        cfg[split_line[0]] = split_line[1].strip()


chrome_path = os.path.join(os.path.dirname(__file__), 'drivers','chromedriver.exe')
prefs = {"profile.default_content_setting_values.notifications" : 2}
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=chrome_options)
driver.maximize_window()


logger = logging.getLogger('fb')
logger.setLevel(logging.DEBUG)
log_file = os.path.join(os.path.dirname(__file__), "invite.log")
file_hlr = logging.FileHandler(log_file)
logger.addHandler(file_hlr)
console = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(console)
ch = logging.Formatter('[%(levelname)s] %(message)s')
console.setFormatter(ch)
file_hlr.setFormatter(ch)


def main():

    invitees = _read_user_unique_id()
    id_used = _read_ip_used()

    driver.get('https://www.facebook.com/login.php')

    # login
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(cfg['user_email'])
    driver.find_element_by_css_selector('#pass').send_keys(cfg['user_pass'])
    time.sleep(1)
    driver.find_element_by_css_selector('#loginbutton').click()

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.fbxWelcomeBoxBlock')))

    event_url = 'https://www.facebook.com/events/upcoming'
    driver.get(event_url)

    selector = '#dashboard_item_{} ._42ft:nth-of-type(2)'.format(cfg['event_id'])
    el = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR, selector)))
    el.click()

    el = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '._59s7 [role="button"]')))
    el.click()

    el = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '._42z0 a')))
    el.click()

    count = 0
    predictive_failed = 0
    for invite in invitees:

        el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#audience_message')))

        # if invite[-3:].isdigit():
        #     logger.debug('digits at the end. skip: {}'.format(invite))
        #     continue
        if invite in id_used:
            logger.debug('id used. skip: {}'.format(invite))
            continue
        else:
            logger.info('invitee OK: {}'.format(invite))

        el.send_keys("@" + invite)
        time.sleep(2)
        if _check_security():
            raw_input('You need to resolve captcha. Please enter ENTER continue ...')
            el.send_keys(Keys.ENTER)
            el.clear()
            el.clear()
            break
        el.send_keys(Keys.ENTER)

        time.sleep(1)
        count += 1
        if _get_selected_count() == count:
            logger.info('added to invite: {} --> ({})'.format(invite, count))
            _append_id_used(invite)
            if count == int(cfg['max_out']):
                logger.info('{} people added. Ready to send a message'.format(count))
                raw_input('Please ENTER to continue ...')
                raw_input('Please ENTER close the program ...')
        else:
            count -= 1
            predictive_failed += 1
            logger.info('predictive text did not appear for: {}, total so far: {}'.format(invite, predictive_failed))
            el.clear()
            # _clear(el)
            el.clear()

    logger.info('{} people added. Ready to send a message'.format(count))
    raw_input('Please ENTER to continue ...')
    raw_input('Please ENTER to close the program ...')


def _read_user_unique_id():
    with open('unique_id.txt') as hlr:
        return [l.strip() for l in hlr]


def _append_id_used(id):
    with open('used_id.txt', 'a') as hlr:
        hlr.write(id + '\n')

def _read_ip_used():
    with open('used_id.txt') as hlr:
        return [l.strip() for l in hlr]


def _get_selected_count():
    try:
        els = WebDriverWait(driver, 2).until(lambda x: driver.find_elements_by_css_selector('._2ei6'))
        return len(els)
    except:
        return None

def _clear(el):
    for i in range(20):
        el.send_keys(Keys.ESCAPE)


def _check_security():

    try:
        WebDriverWait(driver, 1).until_not(lambda x: driver.find_element_by_css_selector('.pvs'))
    except:
        return True

if __name__ == '__main__':
    main()
    driver.quit()