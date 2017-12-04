import time
import os
import json
import urllib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

with open('config.json', 'r') as f:
    config = json.load(f)

chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory": os.getcwd() + "/webcasts"}
chromeOptions.add_experimental_option("prefs", prefs)
chromedriver = 'drivers/chromedriver'
driver = webdriver.Chrome(executable_path=chromedriver,
                          chrome_options=chromeOptions)

modules_page = "https://ivle.nus.edu.sg/v1/module/Default_stu.aspx"

driver.get(modules_page)

downloads = []
try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "login-wrapper"))
    )
    userElement = driver.find_element_by_css_selector("input[type=text]")
    userElement.send_keys(config["user"])
    passwordElement = driver.find_element_by_css_selector(
        "input[type=password]")
    passwordElement.send_keys(config["password"])

    driver.find_element_by_css_selector("button[type=submit]").click()

    module_links = driver.find_elements_by_css_selector(
        ".panel-body table tr td:first-child a")

    print "Enter module indexes to download: (eg, '1 4 3')"
    prompt = "\n".join(["{} :\t{}".format(str(i + 1), link.text)
                        for i, link in enumerate(module_links)]) + "\n"

    module_indexes = [int(i) - 1 for i in raw_input(prompt).split(" ")]

    for module_index in module_indexes:
        driver.get(modules_page)
        module_links = driver.find_elements_by_css_selector(
            ".panel-body table tr td:first-child a")
        module_link = module_links[module_index].get_attribute('href')
        module_title = module_links[module_index].text
        driver.get(module_link)
        try:
            driver.find_element_by_link_text('Web Lecture').click()
        except Exception:
            print "ERROR: {} has no webcasts"

        lecture_rows = driver.find_elements_by_css_selector(
            "body div .panel table tr")

        lecture_links = []
        for row in lecture_rows:
            try:
                lecture_link = {}
                lecture_link["link_element"] = row.find_element_by_css_selector(
                    "td:nth-child(2) a:nth-child(3)")
                lecture_link["lecture_title"] = row.find_element_by_css_selector(
                    "td:nth-child(3)").text

                lecture_links.append(lecture_link)
            except Exception:
                pass

        print "Enter lecture indexes to download: (eg, '1 4 3')"
        prompt = "\n".join(["{} :\t{}".format(str(i + 1), link["lecture_title"])
                            for i, link in enumerate(lecture_links)]) + "\n"

        lecture_indexes = [int(i) - 1 for i in raw_input(prompt).split(" ")]

        for lecture_index in lecture_indexes:
            lecture_title = lecture_links[lecture_index]["lecture_title"]
            link_element = lecture_links[lecture_index]["link_element"]
            link_element.click()

            popup = driver.window_handles[1]
            driver.switch_to_window(popup)
            try:
                splashScreen = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#splashScreen img"))
                )
                driver.find_element_by_css_selector("body").click()
                video = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".fp-player video"))
                )
                video_page_url = video.get_attribute('src')
                driver.get(video_page_url)
                video_url = driver.current_url

                path_to_file = 'webcasts/{} - {}.mp4'.format(
                    module_title, lecture_title)

                downloads.append({
                    "url": video_url,
                    "output_file": path_to_file
                })
            except Exception as e:
                print e
            finally:
                pass
            driver.close()
            driver.switch_to_window(driver.window_handles[0])
finally:
    driver.quit()

for download_info in downloads:
    output_file = download_info["output_file"]
    url = download_info["url"]
    try:
        os.remove(output_file)
        print "removed old file {}".format(output_file)
    except OSError:
        pass

    print "Downloading '{}' to '{}'".format(url, output_file)

    urllib.urlretrieve(url, output_file)
