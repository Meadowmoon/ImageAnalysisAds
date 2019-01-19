import json
import os
import requests
import re

os.chdir('C:\\myProj\\ImageAnalysisAds\\ImageAnalysisAds.Crawler')

def get_raw (URL):
    request = requests.get(URL)
    request = json.loads(request.text)
    jsonDump = request['graphql']['hashtag']['edge_hashtag_to_media']
    return jsonDump


def get_nextpage_url(jsonDump,BASE_URL):
    nextpage_id = jsonDump['page_info']['end_cursor']
    url = BASE_URL + '&max_id=' + nextpage_id
    return url


def get_post_info(jsonDump,flag_size=1): #flag_size {0-4} = 150,240,320,480,640 
    posts = jsonDump['edges'] 
    infoDict = {} #use dict to avoid storing duplicate post
    
    for post in posts:
        shortcode = post['node']['shortcode']
        try:
            caption = post['node']['edge_media_to_caption']['edges'][0]['node']['text']
        except:
            caption = 'None'
        thumbnail_url = post['node']['thumbnail_resources'][flag_size]['src'] #0-4 = 150,240,320,480,640
        
        infoDict[shortcode]=[caption,thumbnail_url]
    
    return infoDict

#equivalent to main function
def scrap_insta_info (TAG='cups', num=100, size_flag=1): #output a dict
    
    BASE_URL = 'https://www.instagram.com/explore/tags/{0}/?__a=1'.format(TAG)
    url = BASE_URL
    scrappedDict = {}
    scrappedDict_size = 0
    count=1
    
    while scrappedDict_size < num:            
    
        jsonDump = get_raw (url)
        url = get_nextpage_url (jsonDump,BASE_URL)
        postDict = get_post_info (jsonDump, size_flag)
        scrappedDict.update(postDict)
        
        postDict_size = len(postDict.keys())
        scrappedDict_size = len(scrappedDict.keys())        
        
        print ('Page: ' + str(count)); count+=1
        print ('next_url: ' + str(url))
        print ('scrapped_size: ' + str(postDict_size))
        print ('total_size: ' + str(scrappedDict_size))
        
    return scrappedDict


def download_img (scrapped_dict, TAG):
    #os.makedirs(f"{TAG}",exist_ok = True)
    os.makedirs(TAG, exist_ok = True)
    for item in scrapped_dict:
        filename = item
        url = scrapped_dict[item][1]
        
        request = requests.get(url)
        with open("{0}/{1}.jpg".format(TAG,filename), 'wb') as f:
            f.write(request.content)
    
    
TAG='cups'

dict_with_img_urls = scrap_insta_info (TAG=TAG, num=1500, size_flag=1)
with open("{}.json".format(TAG),"w") as f:
    json.dump(dict_with_img_urls,f,indent=4)
    
download_img(dict_with_img_urls, TAG=TAG)

    
#with open("dict.json", "r") as content:
#  y=json.load(content)

'''
##for debug
url='https://scontent-sin6-2.cdninstagram.com/vp/272be6c90955035236426399d80a4977/5C095FBC/t51.2885-15/e35/c135.0.810.810/s150x150/37619265_1316790741788110_7507083606221651968_n.jpg'
request = HTMLSession().get(url)
TAG='cups'
filename='BdOrhzSBD0G'
os.makedirs(f"{TAG}")
with open("{0}/{1}.jpg".format(TAG,filename), 'wb') as f:
    f.write(request.content)



##for debug
url2 = 'https://www.instagram.com/explore/tags/puppies/?__a=1&max_id=AQD65GI7s2Tjayf4_qP6KYaHHVf15F57gWnZPQGOrd2Yu5jUmvIr46Il3V5u_SVIOyp6MXszKqMSw_ii2kXSMRLEOwi33_Ij4TgoQY-zu5tOYg'
request2 = HTMLSession().get(url2)
raw2 = get_raw(url2)
post2 = get_post_info(raw2)

for post in post2:
    print (post)
    print (post2[post][0])
    print (post2[post][1])
    print ()
    
len(post2.keys())
'''