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

    def __init__(self, sc_obj, start_date, departure, arrival, currentdate, tz, 
        departure_abbr, arrival_abbr, no_result_info, filename):
        self.class_type = ""
        self.save_filename = filename
        self.currentdate = currentdate
        self.scrape_obj = sc_obj
        self.driver = None
        self.user_agent = None
        self.screen_resolution = None
        self.tz = tz
        # Errors
        self.page_error = config.ERROR_NONE
        self.start_date = start_date
        self.end_date = {'date': self.start_date["date"] + timedelta(days=1), 'status':'pending'}
        self.departure = departure
        self.arrival =  arrival
        self.departure_abbr = departure_abbr
        self.arrival_abbr = arrival_abbr
        self.no_result_info = no_result_info

    # Note proxy problems
    def check_proxy_status(self, html):
        if html.response.code != 200:
            return config.ERROR_403

        return config.ERROR_NONE

    def check_website_error(self):
        pass

    # Handle saving the card and the request
    def save_item(self, item_list):
        lock.acquire()

        # filename = "output/{}_{}_{}_{}.csv".format(self.class_type, self.departure_abbr, self.arrival_abbr, self.currentdate.strftime('%Y-%b-%d %H'))
        filename = "output/{}".format(self.save_filename)
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

class MayaislandAir(Airline):
    def parse_round_trip(self, html):
        saved_item_list = []
        try:
            #parse departure block
            departure_block = html.q("//div[@id='divAvailabilityPanel0_0_0']")[0]

            departure_header = departure_block.q(".//div[@class='FlightAvailabilityDateHeader']")[0]
            departure_header_str = departure_header.x(".//div[@class='FlightAvailabilityDateHeaderFlightDate']/h4/text()").strip()
            departure_day_str = departure_header_str.split(",")[0][:3].upper().strip()
            departure_date_str = departure_header_str.split(",")[1].replace(self.start_date["date"].strftime('%Y'), "").strip()

            departure_schedule_infos = departure_block.q(".//table[@class='FlightAvailabilityTable']//tr[@class='AvailabilityTableFlightDivider FltRequestedDate']")
            print( "Departure Detail info len-> {}".format(len(departure_schedule_infos)))
            
            #parse arrival block
            arrival_block = html.q("//div[@id='divAvailabilityPanel0_1_0']")[0]
            
            arrival_header = arrival_block.q(".//div[@class='FlightAvailabilityDateHeader']")[0]
            arrival_header_str = arrival_header.x(".//div[@class='FlightAvailabilityDateHeaderFlightDate']/h4/text()").strip()
            arrival_day_str = arrival_header_str.split(",")[0][:3].upper().strip()
            arrival_date_str = arrival_header_str.split(",")[1].replace(self.end_date["date"].strftime('%Y'), "").strip()

            arrival_schedule_infos = arrival_block.q(".//table[@class='FlightAvailabilityTable']//tr[@class='AvailabilityTableFlightDivider FltRequestedDate']")
            print( "Arrival Detail info len-> {}".format(len(arrival_schedule_infos)))

            if len(arrival_schedule_infos) == 0 or len(departure_schedule_infos) == 0:
                return "", "", None

            #get departure information in the departure block
            departure_block_departure = ""
            departure_block_departure_time = ""
            departure_block_duration = ""
            departure_block_direction = ""
            departure_block_arrival = ""
            departure_block_arrival_time = ""
            departure_block_fare1 = ""
            departure_block_fare2 = ""
            departure_block_fare3 = ""
            departure_block_fare = ""

            departure_fare_id1 = ""
            departure_fare_id2 = ""
            departure_fare_id3 = ""
            departure_fare_id = ""

            for schedule_info in departure_schedule_infos:
                departure_block_departure = schedule_info.x("td[@class='DepartureCityColumn']/text()").strip()
                departure_block_departure_time = schedule_info.x("td[@class='DepartureDateTimeColumn']/span[@class='time']/text()").strip()

                departure_block_duration = schedule_info.x("td[@class='FlightDurationColumn']/text()").strip()
                departure_block_direction = schedule_info.x("td[@class='FlightColumn']/text()").strip()

                departure_block_arrival = schedule_info.x("td[@class='ArrivalCityColumn']/text()").strip()
                departure_block_arrival_time = schedule_info.x("td[@class='ArrivalDateTimeColumn']/span[@class='time']/text()").strip()

                departure_block_fare_str1 = schedule_info.x("td[@class='FareColumn FareClassBand1']/span[@class='fare']/text()").strip()
                try:
                    departure_block_fare1 = re.search("([0-9.]+)", departure_block_fare_str1, re.I|re.S|re.M).group(1)
                except:
                    departure_block_fare1 = ""

                if departure_fare_id1 == "":
                    departure_fare_id1 = schedule_info.x("td[@class='FareColumn FareClassBand2']/input/@value").strip()

                departure_block_fare_str2 = schedule_info.x("td[@class='FareColumn FareClassBand1']/span[@class='fare']/text()").strip()
                try:
                    departure_block_fare2 = re.search("([0-9.]+)", departure_block_fare_str2, re.I|re.S|re.M).group(1)
                except:
                    departure_block_fare2 = ""
                if departure_fare_id2 == "":
                    departure_fare_id2 = schedule_info.x("td[@class='FareColumn FareClassBand2']/input/@value").strip()

                departure_block_fare_str3 = schedule_info.x("td[@class='FareColumn FareClassBand3']/span[@class='fare']/text()").strip()
                try:
                    departure_block_fare3 = re.search("([0-9.]+)", departure_block_fare_str3, re.I|re.S|re.M).group(1)
                except:
                    departure_block_fare3 = ""
                if departure_fare_id3 == "":
                    departure_fare_id3 = schedule_info.x("td[@class='FareColumn FareClassBand3']/input/@value").strip()

                if departure_block_fare1 != "":
                    departure_block_fare = departure_block_fare1
                    departure_fare_id = departure_fare_id1

                if departure_block_fare2 != "":
                    if departure_block_fare == "":
                        departure_block_fare = departure_block_fare2
                        departure_fare_id = departure_fare_id2
                    else:
                        if float(departure_block_fare2) < float(departure_block_fare):
                            departure_block_fare = departure_block_fare2
                            departure_fare_id = departure_fare_id2

                if departure_block_fare3 != "":
                    if departure_block_fare == "":
                        departure_block_fare = departure_block_fare3
                        departure_fare_id = departure_fare_id3
                    else:
                        if float(departure_block_fare3) < float(departure_block_fare):
                            departure_block_fare = departure_block_fare3
                            departure_fare_id = departure_fare_id3

                save_item = {}
                save_item["Search_Start_Date"] = self.start_date["date"].strftime('%Y-%b-%d')
                save_item["Search_End_Date"] = self.end_date["date"].strftime('%Y-%b-%d')
                save_item["Departure_Date"] = departure_day_str + " " + departure_date_str
                save_item["Origin"] = departure_block_departure
                save_item["Destination"] = departure_block_arrival
                save_item["Leave_Time"] = departure_block_departure_time
                save_item["Arrive_Time"] = departure_block_arrival_time
                save_item["Duration"] = departure_block_duration
                save_item["Flight_Number"] = departure_block_direction
                save_item["Fare"] = departure_block_fare
     
                saved_item_list.append(save_item)

            #get departure information in the departure block
            arrival_block_departure = ""
            arrival_block_departure_time = ""
            arrival_block_duration = ""
            arrival_block_direction = ""
            arrival_block_arrival = ""
            arrival_block_arrival_time = ""
            arrival_block_fare1 = ""
            arrival_block_fare2 = ""
            arrival_block_fare3 = ""
            arrival_block_fare = ""

            arrival_fare_id1 = ""
            arrival_fare_id2 = ""
            arrival_fare_id3 = ""
            arrival_fare_id = ""

            for schedule_info in arrival_schedule_infos:
                arrival_block_departure = schedule_info.x("td[@class='DepartureCityColumn']/text()").strip()
                arrival_block_departure_time = schedule_info.x("td[@class='DepartureDateTimeColumn']/span[@class='time']/text()").strip()

                arrival_block_duration = schedule_info.x("td[@class='FlightDurationColumn']/text()").strip()
                arrival_block_direction = schedule_info.x("td[@class='FlightColumn']/text()").strip()

                arrival_block_arrival = schedule_info.x("td[@class='ArrivalCityColumn']/text()").strip()
                arrival_block_arrival_time = schedule_info.x("td[@class='ArrivalDateTimeColumn']/span[@class='time']/text()").strip()

                arrival_block_fare_str1 = schedule_info.x("td[@class='FareColumn FareClassBand1']/span[@class='fare']/text()").strip()
                try:
                    arrival_block_fare1 = re.search("([0-9.]+)", arrival_block_fare_str1, re.I|re.S|re.M).group(1)
                except:
                    arrival_block_fare1 = ""

                if arrival_fare_id1 == "":
                    arrival_fare_id1 = schedule_info.x("td[@class='FareColumn FareClassBand2']/input/@value").strip()

                arrival_block_fare_str2 = schedule_info.x("td[@class='FareColumn FareClassBand1']/span[@class='fare']/text()").strip()
                try:
                    arrival_block_fare2 = re.search("([0-9.]+)", arrival_block_fare_str2, re.I|re.S|re.M).group(1)
                except:
                    arrival_block_fare2 = ""
                if arrival_fare_id2 == "":
                    arrival_fare_id2 = schedule_info.x("td[@class='FareColumn FareClassBand2']/input/@value").strip()

                arrival_block_fare_str3 = schedule_info.x("td[@class='FareColumn FareClassBand3']/span[@class='fare']/text()").strip()
                try:
                    arrival_block_fare3 = re.search("([0-9.]+)", arrival_block_fare_str3, re.I|re.S|re.M).group(1)
                except:
                    arrival_block_fare3 = ""
                if arrival_fare_id3 == "":
                    arrival_fare_id3 = schedule_info.x("td[@class='FareColumn FareClassBand3']/input/@value").strip()

                if arrival_block_fare1 != "":
                    arrival_block_fare = arrival_block_fare1
                    arrival_fare_id = arrival_fare_id1

                if arrival_block_fare2 != "":
                    if arrival_block_fare == "":
                        arrival_block_fare = arrival_block_fare2
                        arrival_fare_id = arrival_fare_id2
                    else:
                        if float(arrival_block_fare2) < float(arrival_block_fare):
                            arrival_block_fare = arrival_block_fare2
                            arrival_fare_id = arrival_fare_id2

                if arrival_block_fare3 != "":
                    if arrival_block_fare == "":
                        arrival_block_fare = arrival_block_fare3
                        arrival_fare_id = arrival_fare_id3
                    else:
                        if float(arrival_block_fare3) < float(arrival_block_fare):
                            arrival_block_fare = arrival_block_fare3
                            arrival_fare_id = arrival_fare_id3

                save_item = {}
                save_item["Search_Start_Date"] =  self.start_date["date"].strftime('%Y-%b-%d')
                save_item["Search_End_Date"] =  self.end_date["date"].strftime('%Y-%b-%d')
                save_item["Departure_Date"] =  arrival_day_str + " " + arrival_date_str
                save_item["Origin"] =  arrival_block_departure
                save_item["Destination"] =  arrival_block_arrival
                save_item["Leave_Time"] =  arrival_block_departure_time
                save_item["Arrive_Time"] =  arrival_block_arrival_time
                save_item["Duration"] =  arrival_block_duration
                save_item["Flight_Number"] =  arrival_block_direction
                save_item["Fare"] = arrival_block_fare

                saved_item_list.append(save_item)

            return departure_fare_id, arrival_fare_id, saved_item_list
        except Exception as e:
            self.show_exception_detail(e)
            return "", "", None

    def process_error(self):
        self.start_date["error_count"] += 1
        if self.start_date["error_count"] >= config.MAYAISLAND_SCRAPING_MAX_COUNT:
            self.start_date["status"] = "complete"
            self.no_result_info["Count"] += 1
        else:
            self.start_date["status"] = "none"

    def parse_website(self, selenium_driver_type):
        self.class_type = config.CLASS_TYPE_MAYAISLANDAIR_STR
        self.scrape_obj.clear_cookies()

        self.parent_url = "https://booking.mayaislandair.com/VARS/Public/CustomerPanels/Requirements.aspx"

        print('loading parent page... MayaislandAir', self.departure, self.arrival)
        html = self.scrape_obj.load(self.parent_url, use_cache=False)
        if self.check_proxy_status(html) != config.ERROR_NONE:
            self.process_error()
            return False

        session_id = html.x("//input[@id='VarsSessionID']/@value").encode('utf8').strip()

        start_date_str = self.start_date["date"].strftime('%d-%b-%Y')
        end_date_str = self.end_date["date"].strftime('%d-%b-%Y')

        print("++++++++++++++++++++++")
        print("Start Date = {}".format(start_date_str), self.departure, self.arrival)
        print("End Date = {}".format(end_date_str), self.departure, self.arrival)
        print("++++++++++++++++++++++")

        payload = {}
        form_data = {}
        form_data["Origin"] = [self.departure_abbr]
        form_data["VarsSessionID"] = session_id
        form_data["Destination"] = [self.arrival_abbr]
        form_data["DepartureDate"] = [start_date_str]
        form_data["ReturnDate"] = [end_date_str]
        form_data["Adults"] = "1"
        form_data["Children"] = "0"
        form_data["SmallChildren"] = 0
        form_data["Seniors"] = "0"
        form_data["Students"] = "0"
        form_data["Infants"] = "0"
        form_data["Youths"] = "0"
        form_data["Teachers"] = "0"
        form_data["SeatedInfants"] = "0"
        form_data["EVoucher"] = ""
        form_data["SearchUser"] = "PUBLIC"
        form_data["SearchSource"] = "refine"
        
        payload["FormData"] = form_data
        payload["IsMMBChangeFlightMode"] = False

        
        url = "https://booking.mayaislandair.com/VARS/Public/WebServices/AvailabilityWS.asmx/GetFlightAvailability?VarsSessionID={}".format(session_id)

        headers = {
            "Content-Type": "application/json",
            #"accept-encoding": "gzip, deflate",
            #"accept-language": "en-US,en;q=0.8",
            #"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
        }
        
        payload = json.dumps(payload)

        # print url
        # print payload
        
        print('loading get availability page... MayaislandAir')
        html = self.scrape_obj.load(url, post=payload, headers=headers, use_cache=False)
        if self.check_proxy_status(html) != config.ERROR_NONE:
            self.process_error()
            return False

        url = "https://booking.mayaislandair.com/VARS/Public/FlightSelect.aspx"
        payload = {}
        payload["VarsSessionID"] = session_id

        print('loading get info page... MayaislandAir')
        html =  self.scrape_obj.load(url, post=payload, use_cache=False)
        if self.check_proxy_status(html) != config.ERROR_NONE:
            self.process_error()
            return False

        # with open("response.html", 'w') as f:
        #     f.write(html.encode('utf-8'))
        print("Call Parse Round Trip Function")

        departure_fare_id = ""
        arrival_fare_id = ""
        saved_item_list = []

        self.wait()
        departure_fare_id, arrival_fare_id, saved_item_list = self.parse_round_trip(html)

        print( "Departure ID= {}".format(departure_fare_id))
        print( "Arrival ID= {}".format(arrival_fare_id))

        if departure_fare_id != "" and arrival_fare_id != "":
            url = "https://booking.mayaislandair.com/vars/public/WebServices/AvailabilityWS.asmx/AddFlightToBasket?VarsSessionID={}".format(session_id)

            payload = {}
            form_data = {}

            form_data["VarsSessionID"] = session_id
            form_data["fareData"] = [departure_fare_id, arrival_fare_id]
            form_data["Zone"] = "PUBLIC"
            payload["addFlightRequest"] = form_data
            payload = json.dumps(payload)

            headers = {
                "Content-Type": "application/json",
            }

            self.wait()
            json_value =  self.scrape_obj.load_json(url, post=payload, use_cache=False, headers = headers)
            html_content = Doc(html=json_value["d"]["Data"])
            total_price_str = html_content.x("//td[@class='BasketGrandTotalPrice']").strip()

            try:
                total_fare = re.search("([0-9.]+)", total_price_str, re.I|re.S|re.M).group(1)
                currency = re.search("([A-Z]+)", total_price_str, re.I|re.S|re.M).group(1)
            except:
                self.process_error()
                return False

            item_list = []
            saved_time = datetime.now(self.tz).strftime('%Y-%m-%d %H:%M')
            for save_item in saved_item_list:
                
                item = [
                    "Search Start Date", save_item["Search_Start_Date"],
                    "Search End Date", save_item["Search_End_Date"],
                    "Departure Date", save_item["Departure_Date"],
                    "Origin", save_item["Origin"],
                    "Destination", save_item["Destination"],
                    "Leave Time", save_item["Leave_Time"],
                    "Arrive Time", save_item["Arrive_Time"],
                    "Duration", save_item["Duration"],
                    "Flight Number", save_item["Flight_Number"],
                    "Airline Fare", save_item["Fare"],
                    "Fare", total_fare,
                    "Airline", self.class_type,
                    "Currency", currency,
                    "Capture Time", saved_time
                ]

                item_list.append(item)

            self.save_item(item_list)

            self.start_date["status"] = "complete"
            return True
        else:
            print("************************")
            print(self.start_date)
            print("************************")
            
            self.process_error()
            return False
