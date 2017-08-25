proxy_username = "silicons"
proxy_password = "1pRnQcg87F"

proxies = [
	'38.141.0.2:60000',
	'38.141.0.5:60000',
	'38.141.0.8:60000',
	'38.141.0.11:60000',
	'38.141.0.14:60000',
	'38.141.0.16:60000',
	'38.141.0.19:60000',
	'38.141.0.22:60000',
	'38.141.0.25:60000',
	'38.141.0.28:60000',
	'38.141.0.30:60000',
	'38.141.0.33:60000',
	'38.141.0.36:60000',
	'38.141.0.39:60000',
	'38.141.0.42:60000',
	'38.141.0.44:60000',
	'38.141.0.47:60000',
	'38.141.0.50:60000',
	'38.141.0.53:60000',
	'38.141.0.56:60000',
	'38.141.0.58:60000',
	'38.141.0.61:60000',
	'38.141.0.64:60000',
	'38.141.0.67:60000',
	'38.141.0.70:60000',
	'38.141.0.72:60000',
	'38.141.0.75:60000',
	'38.141.0.78:60000',
	'38.141.0.81:60000',
	'38.141.0.84:60000',
	'38.141.0.86:60000',
	'38.141.0.89:60000',
	'38.141.0.92:60000',
	'38.141.0.95:60000',
	'38.141.0.98:60000',
	'38.141.0.100:60000',
	'38.141.0.103:60000',
	'38.141.0.106:60000',
	'38.141.0.109:60000',
	'38.141.0.112:60000',
	'38.141.0.114:60000',
	'38.141.0.117:60000',
	'38.141.0.120:60000',
	'38.141.0.123:60000',
	'38.141.0.126:60000',
	'38.141.0.128:60000',
	'38.141.0.131:60000',
	'38.141.0.134:60000',
	'38.141.0.137:60000',
	'38.141.0.140:60000',
]

WEBSITE_TYPE_TROPICAIR 			= 0
WEBSITE_TYPE_MAYAISLANDAIR 		= 1

ERROR_NONE = 0
ERROR_TIMEOUT_EXCEPTION = 1
ERROR_WEBSITE_PROBLEM = 2
ERROR_PROXY_PROVIDER = 3
ERROR_403 = 4

# selenium driver type constant
DRIVER_VALUE_FIREFOX 					= 1
DRIVER_VALUE_CHROME 					= 2
DRIVER_VALUE_PHANTOMJS 					= 3

# screen size of selenium & phantomjs
MOBILE_SC = [[480,800], [240,320], [800,480], [800,1280], [720,1280], [1920,1080], [2560,1440], [1440,2560], [1280,720], [960,540], [480,360], [1334,750], [640,1136], [960,640], [480,320]]
TABLET_SC = [[1280,800], [1024,600], [1024,768], [2048,1536], [2732,2048], [768,1024], [768,1280]]
DESKTOP_SC = [[1920,1080], [1600,900], [1280,1024], [1152,864], [1024,768], [800,600]]

# waiting time for phantom js & other functions
DRIVER_WAITING_SECONDS 					= 60
DRIVER_MEDIUM_WAITING_SECONDS 			= 15
DRIVER_SHORT_WAITING_SECONDS 			= 5

DAYS_TO_BE_SCRAPED 	= 3
# DAYS_TO_BE_SCRAPED 	= 10

CLASS_TYPE_MAYAISLANDAIR 	= 1 	
CLASS_TYPE_TROPICAIR 		= 0 	

CLASS_TYPE_MAYAISLANDAIR_STR = "MayaislandAir"
CLASS_TYPE_TROPICAIR_STR = "TropicAir"

AIRPORT_RELATIONSHIP_FILE = "relationship/airport_relation.csv"

TROPICAIR_SCRAPING_MAX_COUNT			= 5
MAYAISLAND_SCRAPING_MAX_COUNT			= 1

MAX_NO_RESULT_COUNT			= 10

#FTP Information
FTP_UPLOAD_FOLDER  			= "uploads/FareScrape/"
FTP_SERVER_ADDR				= "212.147.141.5"
FTP_SERVER_PORT				= 221
FTP_USER					= "2m-ftp-ssh"
FTP_PWD						= "plmnkoQAZXSW&$"