import os
import subprocess
import re
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-t', '--threads', type=int, required=False, default=1, help='Number of threads, defaults to 5')
    
    args = parser.parse_args()
    threads_number = args.threads

    processname = 'python sc_mayaislandair_onebyone.py -t {}'.format(threads_number)
    tmp = os.popen("ps -Af").read()

    proccount = tmp.count(processname)

    if proccount > 0:
      print(proccount, ' processes running of ', processname, 'type')
    else:
      os.system(processname)