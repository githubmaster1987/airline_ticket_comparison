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

    date_list = []
    for step in range(start_step, start_step + config.DAYS_TO_BE_SCRAPED):
        date_list.append(datetime.now(tz) + timedelta(days=step))

    result_list = []
    lists = []
    total_result = len(date_list)

    for temp_date in date_list:
        lists.append(temp_date)
        if len(lists) == int(total_result / thread_number):
            obj = {}
            obj["no_result"] =0 
            obj["status"] = "none"
            obj["date"] = lists
            obj["error_count"] = 0
            result_list.append(obj)
            lists = []

    if len(lists) > 0:
        obj = {}
        obj["no_result"] =0 
        obj["status"] = "none"
        obj["date"] = lists
        obj["error_count"] = 0
        result_list.append(obj)

    return result_list

def start_scraping(threads_number, website_type):
    global config

    global_sc_obj = Scraper(
        use_cache=False, #enable cache globally
        retries=3, 
        use_default_logging = False
    )

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
            timeout=60,
            use_default_logging = False
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

    
    for i, depart_arrival_info in enumerate(depart_arrival_list):
        threads = []

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
        
        
        # for step in range(start_step, start_step + config.DAYS_TO_BE_SCRAPED):
        #     date_list.append({"date":datetime.now(tz) + timedelta(days=step), "status":"none", "error_count":0})

        date_list = date_thread_list(threads_number)

        while len(date_list) > 0:
            if len(threads) < threads_number:
                start_date = None
                
                bStop = True
                for date in date_list:
                    if date["status"] != "complete":
                        bStop = False

                    if date["status"] == "none":
                        start_date = date
                        start_date["status"] = "pending"
                        break

                if bStop == True:
                    break

                if start_date == None:
                    continue

                print ("++++++++++++++++++++++++++++++")
                print ("Depart List = " + str(len(depart_arrival_list)) + " Index =" + str(i))
                # print (depart_arrival_info)
                print (departure_abbr + "," + arrival_abbr)
                print ("++++++++++++++++++++++++++++++")

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
                        departure_abbr, arrival_abbr)
                else:
                    class_obj = TropicAir(s, start_date, departure, arrival, currentdate, tz, 
                        departure_abbr, arrival_abbr)
                
                thread_obj = threading.Thread(target=class_obj.parse_website,
                                              args=(config.DRIVER_VALUE_PHANTOMJS,))
                                            # args=(config.DRIVER_VALUE_CHROME,))

                threads.append(thread_obj)
                thread_obj.start()
            
            for thread in threads:
                if not thread.is_alive():
                    
                    thread.join()
                    threads.remove(thread)

            
        # filename = "{}_{}_{}_{}.csv".format(common_lib.get_webiste_str(website_type), departure_abbr, arrival_abbr, currentdate.strftime('%Y-%b-%d %H'))
        filename = "{}.csv".format(common_lib.get_webiste_str(website_type))
        try:
            #common_lib.upload_file(filename, "output/")
            print "Upload"
        except:
            print ( "Error while upload :" + filename)

        no_result = 0
        for item in date_list:
            no_result += item["no_result"] 
        
        stopdate = datetime.now(tz)
        print ("Finish Date & Time: {} , {}".format(stopdate.strftime('%Y-%m-%d'), stopdate.strftime('%H:%M')))

        global_sc_obj.save([
            "Departure", departure,
            "Arrival", arrival,
            "No Result", no_result,
            "File Name", filename,
            "Start", currentdate.strftime('%Y-%m-%d %H:%M'),
            "Finish", stopdate.strftime('%Y-%m-%d %H:%M')
            ], "output_{}.csv".format(website_type))

        print ( "*************************")
        # break
 
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
