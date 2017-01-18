from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import logging
import sys
import csv
import random

cfg = {}
with open('creds.conf') as hlr:
    for line in hlr:
        split_line = line.split('::')
        cfg[split_line[0]] = split_line[1].strip()

logger = logging.getLogger('fb')
logger.setLevel(logging.DEBUG)
log_file = os.path.join(os.path.dirname(__file__), "likes.log")
file_hlr = logging.FileHandler(log_file)
logger.addHandler(file_hlr)
console = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(console)
ch = logging.Formatter('[%(levelname)s] %(message)s')
console.setFormatter(ch)
file_hlr.setFormatter(ch)


chrome_path = os.path.join(os.path.dirname(__file__), 'drivers','chromedriver.exe')
chrome_options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications" : 2}
chrome_options.add_experimental_option("prefs", prefs)

if cfg['proxy'] != '':
    server = '--proxy-server={}'.format(cfg['proxy'])
    chrome_options.add_argument(server)
    logger.info('Proxy: {}'.format(server))
driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=chrome_options)

#
# binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe')
# driver = webdriver.Firefox(firefox_binary=binary)

driver.maximize_window()


def main():

    likes_hrefs = []
    people_hrfs = []

    scr_pages = _read_scrape_pages()
    msged_urls = _read_msged_urls()
    unigue_ids = _read_user_unique_id()
    msg_content = _read_msg_content()

    if cfg['send_messages'].lower() == 'false':
        send_message = False
    else:
        send_message = True

    max_count = int(cfg['max_out'])
    split_set_sleep = cfg['set_sleep'].split(',')
    min_sleep = int(split_set_sleep[0])
    max_sleep = int(split_set_sleep[1])
    maxed_out = False
    blocked = False

    driver.get('https://www.facebook.com/')

    # login
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(cfg['user_email'])
    driver.find_element_by_css_selector('#pass').send_keys(cfg['user_pass'])
    time.sleep(1)
    driver.find_element_by_css_selector('#loginbutton').click()

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'pagelet_bluebar')))
    logger.info('User logged in. Message to be sent out: {}'.format(max_count))
    logger.info('Sleep between messages set to between: {} and {}'.format(min_sleep, max_sleep))
    logger.info('Send messages set to: {}.'.format(cfg['send_messages']))

    for line_ctr, pg_line in enumerate(scr_pages):

        if maxed_out:
            logger.info('Max. messages sent. Stop program')
            raw_input('Please any key to exit...')
            break
        if blocked:
            logger.info('You are blocked on sending messages')
            raw_input('Please any key to exit...')
            break
        elif pg_line[0].count('# End of file'):
            logger.debug('All pages scraped')
            break

        if pg_line[0].startswith('#') or pg_line[1].lower() == 'scraped':
            logger.debug('Line skipped: {}'.format(pg_line))
        else:
            logger.info('Scraping page: {}'.format(pg_line[0]))
            driver.get(pg_line[0])

            time.sleep(1)

            # every scroll down a new container with new posts displays
            # locator of the container: ._1xnd
            els = driver.find_elements_by_css_selector('._1xnd')
            count_els = len(els)

            # scroll down pages to bring up more posts
            for i in range(int(cfg['scrolls_down'])):

                # scroll down
                # wait for new posts
                driver.find_element_by_tag_name('body').send_keys(Keys.END)
                count_els += 1
                _wait_for_page_load_posts(count_els)

            # all liked posts on the page
            # collect hrefs
            liked_posts = driver.find_elements_by_css_selector('._2x4v')
            logger.debug('Liked posts: {}'.format(len(liked_posts)))
            for lbt in liked_posts:
                likes_hrefs.append(lbt.get_attribute('href'))

            # Open people who reacted pages
            # Collect people hrefs
            for i, href in enumerate(likes_hrefs):
                driver.get(href)
                logger.debug('People who reacted ({}): {}'.format(i , href))

                for _ in range(100):
                    see_more = _is_see_more()
                    people = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, '._5i_q a')))
                    logger.info('People on this post collected: {}'.format(len(people)))
                    if see_more:
                        see_more.click()
                        time.sleep(3)
                    else:
                        break

                # if not _get_angry():
                for person in people:
                    people_hrfs.append(person.get_attribute('href'))

            logger.debug('Total people harvested count: {}'.format(len(people_hrfs)))
            logger.debug('Remove duplicates')
            people_hrfs = list(set(people_hrfs))
            logger.info('Distinct people harvested: {}'.format(len(people_hrfs)))

            msg_ctr = 0
            id_ctr = 0
            if send_message:
                # Send messages
                page_ctr = 0
                for url in people_hrfs:
                    url = _extract_profile(url)
                    if url not in msged_urls:
                        driver.get(url)
                        page_ctr += 1

                        # _clear_alert()
                        _clear_any_chats()

                        logger.debug('Open page url({}): {}'.format(page_ctr, url))

                        if _send_message(msg_content):
                            msg_ctr += 1
                            logger.info('Message no ({}) sent to: {}'.format(msg_ctr, url))
                            time.sleep(random.randint(min_sleep, max_sleep))
                            _append_msged_url(url)
                            _clear_any_chats()
                            if msg_ctr == max_count:
                                maxed_out = True
                                break
                        else:
                            logger.debug('Did not send msg to: {}'.format(url))
                            # check if user is blocked
                            if _is_blocked():
                                blocked = True
                                break
                            _append_msged_url(url)
                    else:
                        logger.debug('Skip page url: {}. Message already sent'.format(url))

                if maxed_out or blocked:
                    scr_pages[line_ctr][1] = 'IN PROGRESS'
                else:
                    scr_pages[line_ctr][1] = 'SCRAPED'

            else:
                for url in people_hrfs:
                    url = _extract_profile(url)
                    if not url.count('profile.php?id') and not url.count('ufi/reaction') and not url.count('-'):
                        url = url[url.find('com/') + 4:]
                        if url not in unigue_ids:
                            _append_user_unique_id(url)
                            id_ctr += 1
                            logger.debug('ID {} added ({}).'.format(url, id_ctr))
                        else:
                            logger.debug('ID already in file: {}.'.format(url))

                scr_pages[line_ctr][1] = 'SCRAPED'

            # add count
            if scr_pages[line_ctr][2] == '':
                existent_count = 0
            else:
                existent_count = int(scr_pages[line_ctr][2])
            scr_pages[line_ctr][2] = str(msg_ctr + existent_count)
            _write_scrape_pages(scr_pages)


def _wait_for_page_load_posts(act):
    for i in range(60):
        els = driver.find_elements_by_class_name('_1xnd')
        if len(els) == act:
            logger.debug('Page updated: Containers: {}'.format(len(els)))
            break
        else:
            logger.debug('Page being updated: Containers: {}'.format(len(els)))
            time.sleep(1)


def _read_config():
    cf = {}
    with open('creds.conf') as hlr:
        for line in hlr:
            split_line = line.split('::')
            cf[split_line[0]] = split_line[1].strip()
    return cf


# http://stackoverflow.com/questions/6726953/open-the-file-in-universal-newline-mode-using-the-csv-django-module
def _read_scrape_pages():
    with open('scrape_pages.csv', 'rU') as f:
        reader = csv.reader(f)
        return [row for row in reader]


# http://stackoverflow.com/questions/3348460/csv-file-written-with-python-has-blank-lines-between-each-row
def _write_scrape_pages(data):
    with open('scrape_pages.csv', 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(data)


def _extract_profile(url):
    return url[:url.find('?fref')]


def _append_msged_url(url):
    with open('collect_profiles.txt', 'a') as hlr:
        hlr.write(url + '\n')


def _append_user_unique_id(url):
    with open('unique_id.txt', 'a') as hlr:
        hlr.write(url + '\n')


def _read_user_unique_id():
    with open('unique_id.txt') as hlr:
        return [l.strip() for l in hlr]


def _read_msged_urls():
    with open('collect_profiles.txt') as hlr:
        return [l.strip() for l in hlr]


def _read_msg_content():
    with open('message_content.txt') as hlr:
        return hlr.read()


def _clear_alert():
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except:
        logger.debug('no allert')


def _get_angry():
    try:
        WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, '._3j7q')))
        return True
    except TimeoutException:
        logger.debug('Reacted angry. Skip')


def _clear_any_chats():

    try:
        header_tabs = WebDriverWait(driver, 2).until(lambda x: driver.find_elements_by_css_selector('.fbChatTab'))
        close_button = driver.find_element_by_css_selector('.close')

        for header in header_tabs:
            actions = ActionChains(driver)
            actions.move_to_element(header).click(close_button)
            actions.perform()
    except:
        # logger.debug('no chats open',  exc_info=True)
        logger.debug('No chats to close')


def _is_blocked():

    try:
        el = WebDriverWait(driver, 1).until(lambda x: driver.find_element_by_css_selector('.fbNubFlyoutHeader ._4qba'))
        logger.debug(el.text)
        return True
    except:
        pass


def _is_see_more():

    try:
        el = WebDriverWait(driver, 2).until(lambda x: driver.find_element_by_css_selector('.uiMorePagerPrimary'))
        return el
    except:
        pass


def _send_message(msg):
    try:
        el = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                            '._51xa a[href*="/messages/"]')))
        el.click()
        el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.optionMenu a')))
        el.click()
        el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li:nth-of-type(1) ._54nc')))
        el.click()
        el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[name="message_body"]')))
        el.send_keys(msg)

        el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[value="Send"]')))
        el.click()
        return True
    except TimeoutException:
        logger.debug('No send message button!')


if __name__ == '__main__':
    main()
    driver.quit()