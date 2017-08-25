import config
import random
import agent
from agent import random_agent
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import requests
from time import sleep
from proxy_list import random_proxy
import os
import smtplib
import ftplib
import paramiko

def get_webiste_str(website_type):
    if website_type == config.CLASS_TYPE_MAYAISLANDAIR:
        return config.CLASS_TYPE_MAYAISLANDAIR_STR
    elif website_type == config.CLASS_TYPE_TROPICAIR:
        return config.CLASS_TYPE_TROPICAIR_STR

def upload_file(upload_file_name, upload_dir):
    # Init
    totalSize = os.path.getsize(upload_dir + upload_file_name)
    print('Total file size : ' + str(round(totalSize / 1024 ,1)) + ' KB')

    # Open FTP connection
    print "Create"
    transport = paramiko.Transport((config.FTP_SERVER_ADDR, config.FTP_SERVER_PORT))

    print "Connect"
    transport.connect(username = config.FTP_USER, password = config.FTP_PWD)

    sftp = paramiko.SFTPClient.from_transport(transport)

    dirlist = sftp.listdir('.')
    print("Dirlist: %s" % dirlist)

    try:
        sftp.put(upload_dir + upload_file_name, config.FTP_UPLOAD_FOLDER + upload_file_name)
    except Exception:
        print e        

    sftp.close()
    transport.close()

    print "==========================="
    print "Upload Success"

def create_proxyauth_extension(proxy_host, proxy_port,
                               proxy_username, proxy_password,
                               scheme='http', plugin_path=None):
    """Proxy Auth Extension

    args:
        proxy_host (str): domain or ip address, ie proxy.domain.com
        proxy_port (int): port
        proxy_username (str): auth username
        proxy_password (str): auth password
    kwargs:
        scheme (str): proxy scheme, default http
        plugin_path (str): absolute path of the extension       

    return str -> plugin_path
    """
    import string
    import zipfile

    if plugin_path is None:
        plugin_path = 'proxy_auth_plugin.zip'

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },

        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
    """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "${scheme}",
                host: "${host}",
                port: parseInt(${port})
              },
              bypassList: ["foobar.com"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "${username}",
                password: "${password}"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )

    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path

def create_firefox_driver():
    try:
        binary = FirefoxBinary("/usr/bin/firefox")
        driver = webdriver.Firefox(firefox_binary=binary)
    except WebDriverException as e:
        print(" WebDriverException -> %s" % str(e))
        return None

    return driver

def create_chrome_driver():
    driver = None
    proxy_ip, proxy_port, proxy_user, proxy_pass = random_proxy()

    try:
        proxyauth_plugin_path = create_proxyauth_extension(
          proxy_host=proxy_ip,
          proxy_port=proxy_port,
          proxy_username=proxy_user,
          proxy_password=proxy_pass
        )

        co = Options()
        co.add_argument("--start-maximized")
        co.add_argument('disable-infobars')
        #co.add_argument('headless')
        #co.add_extension(proxyauth_plugin_path)

        driver = webdriver.Chrome(chrome_options=co)
    except Exception as e:
        print(" WebDriverException -> %s" % str(e))

        try:
            if driver is not None:
                phantom_Quit(driver)
        except Exception as e:
            print "*****************************"
            print "Error occurred when create driver"
            print e

        return None

    return driver

def create_phantomjs_driver():
    ua = ["D", "W", agent.firefox]
    # if ua == None:
    #     ua = random_agent()
    #     # e.g. ["M", "A", "Mozilla/5.0 (Android; Mobile; rv:40.0) Gecko/40.0 Firefox/40.0"],
    #     if ua[0] == "M": # Mobile
    #         screen_resolution = random.choice(config.MOBILE_SC)
    #     elif ua[0] == "T": # Tablet
    #         screen_resolution = random.choice(config.TABLET_SC)
    #     else: # elif ua[0] == "D": # Desktop
    #         screen_resolution = random.choice(config.DESKTOP_SC)

    screen_resolution = [1366, 768] 
    # proxy = random_proxy()
    proxy_ip, proxy_port, proxy_user, proxy_pass = random_proxy()

    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0"
    dcap['phantomjs.page.settings.loadImages'] = True
    dcap['phantomjs.page.settings.resourceTimeout'] = 60000

    dcap['phantomjs.page.customHeaders.User-Agent'] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0"
    dcap['phantomjs.page.customHeaders.Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    #dcap['phantomjs.page.customHeaders.Accept-Encoding'] = "gzip, deflate, *"
    dcap['phantomjs.page.customHeaders.Host'] = "www.tropicair.com"
    
    accept_language = "en-US,en;q=0.5"

    # if accept_language != "":
    #    dcap['phantomjs.page.customHeaders.Accept-Language'] = accept_language
    proxy_str = "{}:{}".format(proxy_ip, proxy_port)
    auth_str = "{}:{}".format(proxy_user, proxy_pass)
    c_type='http'

    service_args = ['--proxy=%s' % proxy_str, '--proxy-type=%s' % c_type,'--proxy-auth=%s' % auth_str , '--ignore-ssl-errors=true', '--ssl-protocol=any', '--web-security=false']
    print service_args
    driver = None
    try:
        driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=service_args)
        # driver = webdriver.PhantomJS(desired_capabilities=dcap)
        #driver = webdriver.PhantomJS()
    except WebDriverException as e:
        print("webdriver.PhantomJS WebDriverException -> %s" % str(e))
        try:
            if driver:
                phantom_Quit(driver)
        except Exception as e:
            pass

        return None, ua, proxy, screen_resolution

    driver.set_window_size(screen_resolution[0], screen_resolution[1])
    driver.implicitly_wait(config.DRIVER_WAITING_SECONDS)
    driver.set_page_load_timeout(config.DRIVER_WAITING_SECONDS)

    # print driver, ua, proxy_ip, screen_resolution
    return driver, ua, proxy_ip, screen_resolution
    #return driver, ua, proxy, screen_resolution

def phantom_Quit(driver):
    # try:
    #     if driver is not None:
    #         driver.close()
    # except Exception as e:
    #     pass
        #print "************* Driver Close ***************"
        #print e
        
    try:
        if driver is not None:
            driver.service.process.send_signal(signal.SIGTERM)
    except Exception as e:
        pass
        #print "************* Driver Close Signal ***************"
        #print e
    
    try:
        if driver is not None:
            driver.quit()
            del driver
    except Exception as e:
        pass
        #print "************* Driver Quite ***************"
        #print e