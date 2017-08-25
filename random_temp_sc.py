from classes import *
import config
import sys
from scrapex import *
from scrapex import common
from scrapex.node import Node
from scrapex.excellib import *
from scrapex.http import Proxy
from proxy_list import random_proxy
# DB
from datetime import datetime
from datetime import timedelta  
import argparse
import pytz
import thread
import sys

reload(sys)  
sys.setdefaultencoding('utf8')

def date_thread_list(thread_number):
    tz = pytz.timezone('America/Los_Angeles')
    currentdate = datetime.now(tz)

    start_step = 0

    config.DAYS_TO_BE_SCRAPED = 3
    date_list = []
    for step in range(start_step, start_step + config.DAYS_TO_BE_SCRAPED):
        date_list.append(datetime.now(tz) + timedelta(days=step))

    result_list = []
    lists = []
    total_result = len(date_list)

    while len(date_list) > 0:
        temp_date = date_list.pop()
        lists.append(temp_date)
        if len(lists) == int(total_result / thread_number):
            result_list.append(lists)
            
            lists = []


    if len(lists) > 0:
        result_list.append(lists)

    return result_list

def start_scraping(threads_number, website_type):
    global config

    global_sc_obj = Scraper(
        use_cache=False, #enable cache globally
        retries=3, 
    )

    logger = global_sc_obj.logger

    tropicair_depart_arrival_list = []
    mayaislandair_depart_arrival_list = []

    try:
        with open(config.AIRPORT_RELATIONSHIP_FILE) as csvfile:
            reader = csv.reader(csvfile)
            
            for i, item in enumerate(reader):
                if i > 0 and item[0] != "" and item[1] != "":
                    obj = {}
                    obj["Departure"] = item[0]
                    obj["Arrival"] = item[1]
                    obj["Type"] = item[2]

                    if obj["Type"] == config.CLASS_TYPE_MAYAISLANDAIR_STR:
                        mayaislandair_depart_arrival_list.append(obj)
                    elif obj["Type"] == config.CLASS_TYPE_TROPICAIR_STR:
                        tropicair_depart_arrival_list.append(obj)
                    else:
                        raise Exception("Invalid content in relatin csv file")

    except Exception as e:
        print (e)
        return

    sc_obj_list = []

    for i in range(0, threads_number):
        sc_obj = Scraper(
            use_cache=False, #enable cache globally
            retries=3, 
            timeout=300,
            #log_file='logs/{}_log_{}.txt'.format(website_type, i)
            )
        sc_obj_list.append(sc_obj)

    tz = pytz.timezone('America/Los_Angeles')

    depart_arrival_list = []
    if website_type == config.CLASS_TYPE_MAYAISLANDAIR:
        depart_arrival_list = mayaislandair_depart_arrival_list
    elif website_type == config.CLASS_TYPE_TROPICAIR:
        depart_arrival_list = tropicair_depart_arrival_list

    if len(depart_arrival_list) == 0:
        print ('None depart arrival info')
        return

    #depart_arrival_list = [depart_arrival_list[0]]
    threads = []

    for i, depart_arrival_info in enumerate(depart_arrival_list):
        
        currentdate = datetime.now(tz)
        print ("Current Date & Time: {} , {}".format(currentdate.strftime('%Y-%m-%d'), currentdate.strftime('%H:%M')))

        departure =  depart_arrival_info["Departure"]
        arrival =  depart_arrival_info["Arrival"]

        departure_abbr = ""
        arrival_abbr = ""

        start_step = 0
        if website_type == config.CLASS_TYPE_MAYAISLANDAIR:
            departure_abbr =  re.search("\((.*?)\)", departure, re.I|re.S|re.M).group(1).strip()
            arrival_abbr = re.search("\((.*?)\)", arrival, re.I|re.S|re.M).group(1).strip()
            start_step = 1  ## This website not scraping today data, so start with +1
        elif website_type == config.CLASS_TYPE_TROPICAIR:
            departure_abbr =  departure.split("-")[1].strip()
            arrival_abbr = arrival.split("-")[1].strip()
        
        date_list = []

        no_result_info = {"Count": 0}

        for step in range(start_step, start_step + config.DAYS_TO_BE_SCRAPED):
            date_list.append({"date":datetime.now(tz) + timedelta(days=step), "status":"none", "error_count":0})

        start_date_str = ""
        while len(date_list) > 0:
            if len(threads) < threads_number:
                start_date = None
                
                if no_result_info["Count"] > config.MAX_NO_RESULT_COUNT:
                    print ("--------------------------")
                    print ("No result any more")
                    print ("--------------------------")
                    break

                for date in date_list:
                    if date["status"] == "complete":
                        # print ("Remove Date")
                        # print (date)
                        
                        date_list.remove(date)
                    elif date["status"] == "none":
                        start_date = date
                        start_date["status"] = "pending"
                        break

                if len(date_list) == 0:
                    break

                if start_date == None:
                    continue

                print ("++++++++++++++++++++++++++++++")
                print ("Depart List = " + str(len(depart_arrival_list)) + " Index =" + str(i))
                # print (depart_arrival_info)
                print (departure_abbr + "," + arrival_abbr)
                print (start_date)
                print ("++++++++++++++++++++++++++++++")

                start_date_str = start_date["date"].strftime('%Y-%m-%d')

                sleep(config.DRIVER_SHORT_WAITING_SECONDS)
                proxy_ip, proxy_port, proxy_user, proxy_pass = random_proxy()
                
                if proxy_user != None:
                    auth_str = "{}:{}".format(proxy_user, proxy_pass)
                    proxy = Proxy(proxy_ip, proxy_port, auth_str)
                else:
                    proxy = Proxy(proxy_ip, proxy_port)

                s = sc_obj_list[len(date_list) % threads_number]
                s.proxy_manager.session_proxy = proxy

                class_obj = None
                if website_type == config.WEBSITE_TYPE_MAYAISLANDAIR:
                    class_obj = MayaislandAir(s, start_date, departure, arrival, currentdate, tz, 
                        departure_abbr, arrival_abbr, no_result_info)
                else:
                    class_obj = TropicAir(s, start_date, departure, arrival, currentdate, tz, 
                        departure_abbr, arrival_abbr, no_result_info)
                
                thread_obj = threading.Thread(target=class_obj.parse_website,
                                              args=(config.DRIVER_VALUE_PHANTOMJS,))
                                            # args=(config.DRIVER_VALUE_CHROME,))

                threads.append(thread_obj)
                thread_obj.start()

            
            for thread in threads:
                if not thread.is_alive():
                    
                    thread.join()
                    threads.remove(thread)

        print ("*************************")
        print (len(date_list))
        print (no_result_info)
        filename = "{}_{}_{}_{}.csv".format(common_lib.get_webiste_str(website_type), departure_abbr, arrival_abbr, currentdate.strftime('%Y-%b-%d %H'))
        try:
            #common_lib.upload_file(filename, "output/")
            print "Upload"
        except:
            print ( "Error while upload :" + filename)

        global_sc_obj.save([
            "Departure", departure,
            "Arrival", arrival,
            "Date Len", len(date_list),
            "No Result", no_result_info["Count"],
            "File Name", filename,
            "Start Date", start_date_str
            ], "export_{}.csv".format(website_type))

        print ( "*************************")

 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-t', '--threads', type=int, required=False, default=1, help='Number of threads, defaults to 5')
    parser.add_argument('-w', '--website', type=int, required=False, default=0, help='Website type: 1-> Mayaislandair, 0-> tropicair')
    #parser.add_argument('-p', '--proxy', type=int, required=False, default=0, help='Proxy type: 0(standard), 1(Micro leave), 2(Rotating)')
    
    args = parser.parse_args()
    # Set config
    threads_number = args.threads
    website_type = args.website
    start_scraping(threads_number, website_type)
