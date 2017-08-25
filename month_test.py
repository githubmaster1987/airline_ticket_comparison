from datetime import datetime
from datetime import timedelta  
import argparse
import pytz
import thread
import sys
import config

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

print date_thread_list(15)