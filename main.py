import requests
import time
import math
import csv


USERNAME =""
PASSWORD = ""
COOKIES = ""
HEADERS  = {
        'Host': 'app.apollo.io',
        'Sec-Ch-Ua': '"Chromium";v="117", "Not;A=Brand";v="8"',
        'Content-Type': 'application/json',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.63 Safari/537.36',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Accept': '*/*',
        'Origin': 'https://app.apollo.io',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://app.apollo.io/',
        'Accept-Language': 'en-US,en;q=0.9',
    }
PER_PAGE_LIMIT = 100
RAW_LEADS = []
CSV_HEADERS = ["name","company","email","designation","industry"]
ORG_DICT = {}


def genCacheKey():
    return int(time.time())

def reqCreds():
    global USERNAME
    global PASSWORD

    USERNAME = input("Enter Email: ")
    PASSWORD = input("Enter Password: ")

def loginToApollo():

    global USERNAME
    global PASSWORD
    global COOKIES
    global HEADERS

    loginJson = {
        'email': USERNAME,
        'password': PASSWORD,
        'timezone_offset': -330,
        'cacheKey': genCacheKey(),
    }

    loginResponse = requests.post('https://app.apollo.io/api/v1/auth/login', headers=HEADERS, json=loginJson)

    if loginResponse.status_code == 200:
        COOKIES = loginResponse.cookies
        return True
    else:
        return False

def findLeadList():
    global COOKIES
    global HEADERS

    leadJson = {
        'label_modality': 'contacts',
        'team_lists_only': [
            'no',
        ],
        'page': 1,
        'display_mode': 'explorer_mode',
        'open_factor_names': [],
        'num_fetch_result': 2,
        'show_suggestions': False,
        'ui_finder_random_seed': '',
        'cacheKey': genCacheKey(),
    }

    leadListResponse = requests.post(
        'https://app.apollo.io/api/v1/labels/search',
        cookies=COOKIES,
        headers=HEADERS,
        json=leadJson)
    
    if leadListResponse.status_code==200:
        leadData=leadListResponse.json()
        return leadData['labels']
    else:
        return False

def fetchLeadList(lid:str,count:int):
    global COOKIES, HEADERS
    
    total_pages = math.ceil(count / 100)

    for page in range(0,total_pages):
        print(f"fetching page:{page+1}")
        json_data = {
        'finder_table_layout_id': '',
        'contact_label_ids': [
            lid,
        ],
        'prospected_by_current_team': [
            'yes',
        ],
        'page': page+1,
        'display_mode': 'explorer_mode',
        'per_page': 100,
        'open_factor_names': [],
        'num_fetch_result': 1,
        'context': 'people-index-page',
        'show_suggestions': False,
        'ui_finder_random_seed': '',
        'cacheKey': genCacheKey(),
        }

        leadResponse = requests.post(
            'https://app.apollo.io/api/v1/mixed_people/search',
            cookies=COOKIES,
            headers=HEADERS,
            json=json_data
        )

        if leadResponse.status_code == 200:
            RAW_LEADS.extend(leadResponse.json()["contacts"])

def processOrgIds(ids:list):
    global COOKIES,HEADERS,ORG_DICT
    
    json_data = {
    'ids': ids,
    'cacheKey': genCacheKey(),
    }

    orgResponse = requests.post(
        'https://app.apollo.io/api/v1/organizations/load_snippets',
        cookies=COOKIES,
        headers=HEADERS,
        json=json_data,
    )
    if orgResponse.status_code == 200:
        for items in orgResponse.json()["organizations"]:
            ORG_DICT[items['id']] = items['industry']

def processRawLeadData():
    orgIds = []
    global RAW_LEADS,ORG_DICT
    for items in RAW_LEADS:
        orgIds.append(items["organization_id"])
    processOrgIds(list(set(orgIds)))
    csvDataRaw= []
    for items in RAW_LEADS:
        if items["organization_id"] == None:
            industry = "N/A"
        else:
            industry = ORG_DICT.get(items["organization_id"])
        
        
        csvDataRaw.append([items["name"], items["organization_name"], items["email"], items["title"],industry])

    return csvDataRaw

reqCreds()
lr = loginToApollo()
if lr:
    print("login success!")
else:
    print("login failed")
    exit()

ll = findLeadList()
if ll:
    for index,items in enumerate(ll,start=1):
        print(index, items['id'] , items['name'], f"count ({items['cached_count']})")
    print("Select an list:")

    while True:
        try:
            linput= int(input("> "))
            break
        except:
            print("invalid choice")

    index = linput-1

    target =ll[index]

    fetchLeadList(target["id"],target["cached_count"])

    CSV_DATA= processRawLeadData()   
    CSV_DATA = [[str(item) for item in row] for row in CSV_DATA]
    csv_file = "output.csv"
    with open(csv_file, mode='w', newline='',encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADERS)
        writer.writerows(CSV_DATA)

else:
    print("unable to find lead lists")
    exit()
