from scrapex import *
import time
import config
import common_lib
from datetime import datetime
from datetime import date
from datetime import timedelta  
from time import sleep
import random, re, os
from time import gmtime, strftime
from selenium.common.exceptions import *
from agent import random_agent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions as EX
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from proxy_list import random_proxy
from scrapex.http import Proxy
import sys
import json
import csv
import threading
import pytz

reload(sys)  
sys.setdefaultencoding('utf8')

lock = threading.Lock()

class AnyEc:
    """ Use with WebDriverWait to combine expected_conditions
        in an OR.
    """

    def __init__(self, *args):
        self.ecs = args

    def __call__(self, driver):
        for fn in self.ecs:
            try:
                if fn(driver): return True
            except:
                pass

global_sc_obj = Scraper(
    use_cache=False, #enable cache globally
    retries=3, 
    timeout=60,
    use_default_logging = False
    )

class Airline:
    parent_url = ""
    try_date_count = 0

    def __init__(self, sc_obj, date_list, departure, arrival, currentdate, tz, 
        departure_abbr, arrival_abbr):
        self.class_type = ""
        self.currentdate = currentdate
        self.scrape_obj = sc_obj
        self.driver = None
        self.user_agent = None
        self.screen_resolution = None
        self.tz = tz
        # Errors
        self.page_error = config.ERROR_NONE
        self.start_date = None
        self.end_date = None
        self.date_list = date_list

        self.departure = departure
        self.arrival =  arrival
        self.departure_abbr = departure_abbr
        self.arrival_abbr = arrival_abbr

    # Note proxy problems
    def check_proxy_status(self, html):
        if html.response.code == 0:
            return config.ERROR_PROXY_PROVIDER

        if html.response.code == 403:
            return config.ERROR_403

        return config.ERROR_NONE

    def check_website_error(self):
        pass

    # Handle saving the card and the request
    def save_item(self, item_list):
        lock.acquire()

        # filename = "output/{}_{}_{}_{}.csv".format(self.class_type, self.departure_abbr, self.arrival_abbr, self.currentdate.strftime('%Y-%b-%d %H'))
        filename = "output/{}.csv".format(self.class_type)
        print filename, self.start_date["date"].strftime('%Y-%b-%d')

        for item in item_list:
            global_sc_obj.save(item, filename)

        lock.release()

    def parse_website(self, selenium_driver_type):
        pass

    # Wait a random amount of time before entering values
    def wait(self):
        sleep(random.randrange(2, config.DRIVER_SHORT_WAITING_SECONDS))

    def wait_medium(self):
        offset_time = random.randrange(config.DRIVER_SHORT_WAITING_SECONDS +1 ,
            config.DRIVER_MEDIUM_WAITING_SECONDS)

        #print("Sleep Time: {} ".format(offset_time))
        sleep(offset_time)

    def show_exception_detail(self, e):
        print (e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("{}, {}, {}".format(exc_type, fname, str(exc_tb.tb_lineno)))

class TropicAir(Airline):
    def select_date(self, driver, div_id, match_date):
        try:
            # print("Div Id -> {}".format(div_id))
            self.wait()
            date_div = driver.find_element_by_xpath("//div[@id='{}']/div[@class='datepicker']".format(div_id))       
            day_div = date_div.find_element_by_xpath("div[@class='datepicker-days']")
            month_div = date_div.find_element_by_xpath("div[@class='datepicker-months']")
            year_div = date_div.find_element_by_xpath("div[@class='datepicker-years']")

            header_div = day_div.find_elements_by_xpath("table/thead/tr/th")[1]
            header_div.click()
            self.wait()

            header_div = month_div.find_elements_by_xpath("table/thead/tr/th")[1]
            header_div.click()


            year_str = match_date.strftime('%Y')
            month_str = match_date.strftime('%b')
            day_str = "%02d" % (int(match_date.strftime('%d')))
            day_str1 = "%d" % (int(match_date.strftime('%d')))

            print("Select Year -> {}".format(year_str))
            select_year = year_div.find_element_by_xpath("table/tbody/tr/td/span[contains(text(), '{}')]".format(year_str))
            select_year.click()

            print("Select Month -> {}".format(month_str))
            select_month = month_div.find_element_by_xpath("table/tbody/tr/td/span[contains(text(), '{}')]".format(month_str))
            select_month.click()
            
            print("Select Day -> {}, {}".format(day_str, day_str1))
            # for div_item in day_div.find_elements_by_xpath("table/tbody/tr/td"):
            #     print div_item.get_attribute("class"), div_item.text

            select_day = day_div.find_element_by_xpath("table/tbody/tr/td[not(@class='day old') and not(@class='day new') and (text()='{}' or text()='{}')]".format(day_str, day_str1))
            select_day.click()
        except Exception as e:
            print e
            return False

        return True
  
    def select_departure_arrival(self, driver):
        try:
            print("*************************")
            print("Find departure div and click")
            departure_div = driver.find_element_by_xpath("//div[contains(@class, 'search-criterias-departure')]")
            departure_btn =  departure_div.find_element_by_xpath(".//button[contains(@class, 'search-criterias-airport')]")
            departure_btn.click()
            self.wait()

            print("Find Air port list and click in departure")
            air_port_div_list = departure_div.find_elements_by_xpath(".//div[@class='col-sm-6 col-xs-12 airport-list']/a")

            print(" Air port list len-> {}".format(len(air_port_div_list)))

            selected_departure = None

            for air_port in air_port_div_list:
                if air_port.get_attribute('text') == self.departure:
                    selected_departure = air_port

            print("Departure: {}".format(selected_departure.get_attribute('text')))
            if selected_departure != None:
                driver.execute_script('window.scrollTo(0, ' + str(selected_departure.location['y']) + ');')
                selected_departure.click()

            print("*************************")
            print("Find arrival div and click")
            arrival_div = driver.find_element_by_xpath("//div[contains(@class, 'search-criterias-arrival')]")
            arrival_btn =  arrival_div.find_element_by_xpath(".//button[contains(@class, 'search-criterias-airport')]")
            arrival_btn.click()
            self.wait()

            print("Find Air port list and click in arrival")
            air_port_div_list = arrival_div.find_elements_by_xpath(".//div[@class='col-sm-6 col-xs-12 airport-list']/a")
            print(" Air port list len-> {}".format(len(air_port_div_list)))
            
            selected_arrival = None
            for air_port in air_port_div_list:
                if air_port.get_attribute('text') == self.arrival:
                    selected_arrival = air_port

            print("Arrival: {}".format(selected_arrival.get_attribute('text')))

            if selected_arrival != None:
                driver.execute_script('window.scrollTo(0, ' + str(selected_arrival.location['y']) + ');')
                selected_arrival.click()
        except Exception as e:
            print e
            return False

        return True
    
    def parse_round_trip(self, driver):
        # print("Wait until right div is shown")
        # driver.save_screenshot('screenshot/6.png') 
        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
            AnyEc(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='selection-sumup-total-amount']")
                ),
            )
        )
        # driver.save_screenshot('screenshot/7.png') 
        saved_item_list = []

        html = Doc(html= driver.page_source)

        title = html.q("//div[@class='day-selection-segment anchored']//span/text()").join(",")
        # print(title)

        day_div = html.q("//a[contains(@class, 'day-selection-day-item btn-primary')]//div[@class='day-selection-header-dayname']")
        departure_day_str = day_div[0                              ].x("text()").strip()
        arrival_day_str = day_div[1].x("text()").strip()

        date_month_divs = html.q("//a[contains(@class, 'day-selection-day-item btn-primary')]//div[@class='day-selection-header-daymonth']/div")
        departure_date_str = date_month_divs[0].x("text()").strip() + " " + date_month_divs[1].x("text()").strip()
        arrival_date_str = date_month_divs[2].x("text()").strip() + " " + date_month_divs[3].x("text()").strip()
        # print( "Departure Selected day : {}, date: {}".format(departure_date_str, departure_day_str))
        # print( "Arrival Selected day : {}, date: {}".format(arrival_date_str, arrival_day_str))

        # get total fare

        total_block = html.q("//div[@id='sum-up-pax']")
        print( " Total Block Exist: {}".format(len(total_block)))

        total_fare = ""
        total_tax = ""
        total_price = ""
        currency = ""

        if len(total_block) > 0:
            total_price_str = total_block[0].x(".//div[contains(@class,'sum-up-val')]/span/text()").strip()
            
            total_price = re.search("([0-9.]+)", total_price_str, re.I|re.S|re.M).group(1)
            currency = re.search("([A-Z]+)", total_price_str, re.I|re.S|re.M).group(1)

            # print total_price
            # print currency
            # total_fare = total_block[0].x(".//div[contains(@class,'net-fare')]/span/text()").strip()
            # tax_blok = total_block[0].q(".//div[contains(@class,'taxes')]/span/span")
            #print("Tax related span count: {}".format(len(tax_blok)))
            # if len(tax_blok) > 0:
            #     total_tax = tax_blok[1].x("text()").strip()

        div_blocks = html.q("//div[@class='dayDetail']")
        #parse departure block
        departure_block = div_blocks[0]
        departure_schedule_infos = departure_block.q(".//ul/li[@class='list-group-item']")
        print( "Departure Detail info len-> {}".format(len(departure_schedule_infos)))

        #get departure information in the departure block
        departure_block_departure = ""
        departure_block_departure_time = ""
        departure_block_duration = ""
        departure_block_direction = ""
        departure_block_arrival = ""
        departure_block_arrival_time = ""
        departure_block_fare = ""
        
        saved_time = datetime.now(self.tz).strftime('%Y-%m-%d %H:%M')
        
        for schedule_info in departure_schedule_infos:
            
            trip_div = schedule_info.q(".//div[contains(@class,'day-detail-trip-cell')]")[0]
            time_div = schedule_info.q(".//div[contains(@class,'day-details-amount-block')]")[0]
            
            departure_block_departure = trip_div.x("div/div[contains(@class, 'day-detail-trip departure')]/div[contains(@class,'day-detail-trip-airport')]/span/text()").strip()
            departure_block_departure_time = trip_div.x("div/div[contains(@class, 'day-detail-trip departure')]/div[contains(@class,'day-detail-trip-time')]/span/text()").strip()

            departure_block_duration = trip_div.x(".//div[contains(@class, 'day-detail-trip-segments')]/span[@class='day-detail-trip-duration']/text()").strip()
            direction_div = trip_div.q(".//div[contains(@class, 'day-detail-trip-segments')]/button[contains(@class, 'direct-trip')]/span")
            
            try:
                departure_block_direction = direction_div[2].x("text()").strip()
                if departure_block_direction == "*":
                    departure_block_direction = direction_div[1].x("text()").strip()
            except:
                departure_block_direction = ""

            departure_block_arrival = trip_div.x("div/div[contains(@class, 'day-detail-trip arrival')]/div[contains(@class,'day-detail-trip-airport')]/span/text()").strip()
            departure_block_arrival_time = trip_div.x("div/div[contains(@class, 'day-detail-trip arrival')]/div[contains(@class,'day-detail-trip-time')]/span/text()").strip()

            departure_block_fare = schedule_info.x(".//button[contains(@class,'btn-amount')]/span/text()").strip()

            save_item = [
                "Search Start Date", self.start_date["date"].strftime('%Y-%b-%d'),
                "Search End Date", self.end_date["date"].strftime('%Y-%b-%d'),
                "Departure Date", departure_day_str + " " + departure_date_str,
                "Origin", departure_block_departure,
                "Destination", departure_block_arrival,
                "Leave Time", departure_block_departure_time,
                "Arrive Time", departure_block_arrival_time,
                "Duration", departure_block_duration,
                "Flight Number", departure_block_direction,
                "Fare", total_price,
                "Airline", self.class_type,
                "Currency", currency,
                "Capture Time", saved_time
            ]

            saved_item_list.append(save_item)
        

        #parse arrival block
        arrival_block = div_blocks[1]
        
        arrival_schedule_infos = arrival_block.q(".//ul/li[@class='list-group-item']")
        print( "Arrival Detail info len-> {}".format(len(arrival_schedule_infos)))

        #get departure information in the departure block
        arrival_block_departure = ""
        arrival_block_departure_time = ""
        arrival_block_duration = ""
        arrival_block_direction = ""
        arrival_block_arrival = ""
        arrival_block_arrival_time = ""
        arrival_block_fare = ""

        for schedule_info in arrival_schedule_infos:
            trip_div = schedule_info.q(".//div[contains(@class,'day-detail-trip-cell')]")[0]
            time_div = schedule_info.q(".//div[contains(@class,'day-details-amount-block')]")[0]
            arrival_block_departure = trip_div.x("div/div[contains(@class, 'day-detail-trip departure')]/div[contains(@class,'day-detail-trip-airport')]/span/text()").strip()
            arrival_block_departure_time = trip_div.x("div/div[contains(@class, 'day-detail-trip departure')]/div[contains(@class,'day-detail-trip-time')]/span/text()").strip()

            arrival_block_duration = trip_div.x(".//div[contains(@class, 'day-detail-trip-segments')]/span[@class='day-detail-trip-duration']/text()").strip()
            direction_div = trip_div.q(".//div[contains(@class, 'day-detail-trip-segments')]/button[contains(@class, 'direct-trip')]/span")
            try:
                arrival_block_direction = direction_div[2].x("text()").strip()
                if arrival_block_direction == "*":
                    arrival_block_direction = direction_div[1].x("text()").strip()
            except:
                arrival_block_direction = ""
                
            arrival_block_arrival = trip_div.x("div/div[contains(@class, 'day-detail-trip arrival')]/div[contains(@class,'day-detail-trip-airport')]/span/text()").strip()
            arrival_block_arrival_time = trip_div.x("div/div[contains(@class, 'day-detail-trip arrival')]/div[contains(@class,'day-detail-trip-time')]/span/text()").strip()

            arrival_block_fare = schedule_info.x(".//button[contains(@class,'btn-amount')]/span/text()").strip()

            save_item = [
                "Search Start Date", self.start_date["date"].strftime('%Y-%b-%d'),
                "Search End Date", self.end_date["date"].strftime('%Y-%b-%d'),
                "Departure Date", arrival_day_str + " " + arrival_date_str,
                "Origin", arrival_block_departure,
                "Destination", arrival_block_arrival,
                "Leave Time", arrival_block_departure_time,
                "Arrive Time", arrival_block_arrival_time,
                "Duration", arrival_block_duration,
                "Flight Number", arrival_block_direction,
                "Fare", total_price,
                "Airline", self.class_type,
                "Currency", currency,
                "Capture Time", saved_time
            ]

            saved_item_list.append(save_item)
        print ("*********Complete**********")
        print(self.start_date)
        self.save_item(saved_item_list)

    def parse_website(self, selenium_driver_type):
        self.class_type = config.CLASS_TYPE_TROPICAIR_STR

        self.parent_url = "https://www.tropicair.com/"

        driver = self.driver
        proxy = None
        try:
            # Use FF here
            is_ff = False

            # lock.acquire()

            # Get driver
            if selenium_driver_type == config.DRIVER_VALUE_CHROME:
                driver = common_lib.create_chrome_driver()  # GOOGLE CHROME PART
            elif is_ff:
                driver = common_lib.create_firefox_driver()  # FIREFOX PART
            elif selenium_driver_type == config.DRIVER_VALUE_PHANTOMJS:
                driver, self.user_agent, proxy, self.screen_resolution = common_lib.create_phantomjs_driver()  # PHANTOMJS PART

            # lock.release()
            if driver is None:
                return

            no_result = 0
            stop_day = ""

            for ind in range(0, len(self.date_list["date"])):
                date_item = self.date_list["date"][ind]
                print "Start Date", date_item
                print "No Result=", no_result

                self.start_date = {"date": date_item, "status":"none", "error_count":0}
                self.end_date = {'date': self.start_date["date"] + timedelta(days=1), 'status':'pending'}
                
                stop_day = date_item
                if no_result >= config.MAX_NO_RESULT_COUNT:
                    print ("--------------------------")
                    print ("No result any more")
                    print ("--------------------------")
                    break

                bStop = False
                while bStop == False:
                    
                    try:
                        # driver.get("http://lumtest.com/myip.json")
                        # self.wait()

                        # print driver.page_source
                        # self.wait()

                        print('loading parent page... TropicAir')

                        driver.get(self.parent_url)
                        self.wait_medium()
                        # with open("html/response1.html", 'w') as f:
                        #     f.write(driver.page_source.encode('utf-8'))
                        # driver.save_screenshot('screenshot/0.png') 
                        
                        print("find iframe in div")
                        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
                            AnyEc(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[@class='tab-content-bg']//iframe")
                                ),
                            )
                        )

                        print("iframe was founded")
                        iframe = driver.find_element_by_xpath("//div[@class='tab-content-bg']//iframe")
                        driver.switch_to_frame(iframe)
                        cookies = driver.get_cookies()
                        #doc = Doc(html=driver.page_source)
                        # with open("response.html", 'w') as f:
                        #     f.write(driver.page_source.encode('utf-8'))

                        print("Find round trip button")
                        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
                            AnyEc(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//button[contains(text(), 'Round trip')]")
                                ),
                            )
                        )
                        
                        # driver.save_screenshot('screenshot/1.png') 
                        # with open("html/response.html", 'w') as f:
                        #     f.write(driver.page_source.encode('utf-8'))

                        print("round trip tab click")
                        round_trip_btn = driver.find_element_by_xpath("//button[contains(text(), 'Round trip')]")
                        round_trip_btn.click()
                        self.wait()
                        # driver.save_screenshot('screenshot/2.png') 
                        #self.save_select_departure_arrival(driver)

                        success = False

                        # print("**************************")
                        # print(self.start_date)
                        # print(self.end_date)

                        print("Select start day -> {}".format(self.start_date["date"]))
                        start_date_div = driver.find_element_by_id("CalendarID0")
                        start_date_div.send_keys("")
                        success = self.select_date(driver, "DateTimePicker0", self.start_date["date"])
                        self.wait()

                        if success == False:
                            print "Error occurred in DateTimePicker0"
                            self.page_error = config.ERROR_WEBSITE_PROBLEM
                        else:
                            print("Select end day -> {}".format(self.end_date["date"]))
                            end_date_div = driver.find_element_by_id("CalendarID1")
                            end_date_div.send_keys("")
                            success = self.select_date(driver, "DateTimePicker1", self.end_date["date"])
                            self.wait()     

                            if success == False:
                                print "Error occurred in DateTimePicker1"
                                self.page_error = config.ERROR_WEBSITE_PROBLEM
                            else:
                                # driver.save_screenshot('screenshot/3.png') 
                                success = self.select_departure_arrival(driver)
                                if success == False:
                                    self.page_error = config.ERROR_WEBSITE_PROBLEM
                                else:
                                    # driver.save_screenshot('screenshot/4.png') 
                                    print("*************************")
                                    print("Click submit to get information")
                                    submit_btn = driver.find_element_by_xpath("//button[contains(@class, 'search-criterias-submit')]")
                                    submit_btn.click()
                                    self.wait()

                                    print("Wait until show date information")
                                    WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
                                        AnyEc(
                                            EC.presence_of_element_located(
                                                (By.XPATH, "//div[contains(@class, 'day-selection-bar-block dayResume')]")
                                            ),
                                            EC.presence_of_element_located(
                                                (By.XPATH, "//div[contains(@class, 'panel-body text-center')]/h2/span")
                                            ),

                                        )
                                    )
                                    # driver.save_screenshot('screenshot/5.png') 
                                    no_result_div = None
                                    try:
                                        no_result_div = driver.find_element_by_xpath("//div[contains(@class, 'panel-body text-center')]/h2/span")
                                    except Exception as e:
                                        pass
                                        #self.show_exception_detail(e)

                                    if no_result_div == None:
                                        print(" Call Parse Round Trip Function")
                                        # parse right div to get sum on round trip
                                        self.parse_round_trip(driver)
                                    else:
                                        print("////////////////No Result/////////////////")
                                        print(no_result_div)
                                        print(self.start_date)
                                        no_result += 1
                                        self.date_list["no_result"] += 1
                                        print("////////////////No Result/////////////////")
                                   
                                    self.page_error = config.ERROR_NONE
                    except TimeoutException as ex:
                        print ('***********E1*************')
                        self.show_exception_detail(ex)
                        self.page_error = config.ERROR_TIMEOUT_EXCEPTION
                    except Exception as e:
                        print ('***********E2*************')
                        self.show_exception_detail(e)
                        self.page_error = config.ERROR_WEBSITE_PROBLEM

                    if self.page_error == config.ERROR_NONE:
                        self.start_date["status"] = "complete"
                    else:
                        self.start_date["error_count"] += 1

                        if self.start_date["error_count"] >= config.TROPICAIR_SCRAPING_MAX_COUNT:
                            self.start_date["status"] = "complete"
                        else:
                            self.start_date["status"] = "none"

                    if self.start_date["status"] == "complete":
                        bStop = True


            start_day = self.date_list["date"][0]
            try:
                end_day = self.date_list["date"][-1]
            except:
                end_day = ""

            self.date_list["status"] = "complete"

            lock.acquire()
            global_sc_obj.save([
                "Departure", self.departure,
                "Arrival", self.arrival,
                "Start", start_day.strftime("%Y-%m-%d"),
                "End", end_day.strftime("%Y-%m-%d"),
                "Stop", stop_day.strftime("%Y-%m-%d"),
                "No Result", no_result,
                ], "output/export_{}.csv".format(self.class_type))                    

            common_lib.phantom_Quit(driver)
            lock.release()
            
        except Exception as e:
            print "++++++++++++++++++++"
            self.date_list["error_count"] += 1

            if self.date_list["error_count"] >= config.TROPICAIR_SCRAPING_MAX_COUNT:
                self.date_list["status"] = "complete"
            else:
                self.date_list["status"] = "none"

            self.show_exception_detail(e)
            common_lib.phantom_Quit(driver)