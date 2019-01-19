import os
import time
import pandas as pd
import subprocess
from collections import Counter
from statistics import mean

os.chdir('C:\\myProj\\ImageAnalysisAds\\ImageAnalysisAds.Crawler')

def get_obj_detected (TAG='cups_12pic'):
    '''call classify_image.py and return csv of classification results'''
    st=time.time()
    STD = ["python", "classify_image.py", "--model_dir", "model_dir"]
    process = subprocess.Popen(
            STD + ["--tag",TAG],
            shell=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    
    _stdout,_ = process.communicate()
    print (time.time()-st)
    return _stdout
    
#    result = os.popen('python classify_image.py --image_file {}'.format(img_path)).read()
#    result = re.split("\n",result)[0:5]
#    result = [re.split("[()]|= ",res)[0:3:2] for res in result]
#    result = list(zip(*result))
    
def top5_errorRate (clf_result,keywordList):
    '''
    clf_result: list of image classification results in sets of 5 predictions
    keywordList: list of positive classifications
    '''
    n = int (len(clf_result)/5) #number of images
    isInkeywordList = []
    
    for i in range (n):
        obj_det = clf_result[i*5:i*5+5]
        print (obj_det)
        
        kw_isFound = [kw in "".join(obj_det) for kw in keywordList]
        isInkeywordList.append(any(kw_isFound))
        print (list(zip(kw_isFound,keywordList)))
    
    return mean(isInkeywordList)


def round2 (float):
    '''convert float to 2dp percentage'''
    return round(float*100,2)
    

def count_classification(clf_result):
    '''    clf_result: list of image classification results    '''
    n = len(clf_result)
    counter = Counter(clf_result).most_common()
    res = [(item,round2(c/n)) for item,c in counter]
     
    return res

TAG='cups_12pic'
get_obj_detected(TAG='cups')

count_classification(clf_result)

clf_result = pd.read_csv('{}_result.csv'.format(TAG), header=None)[0]
clf_result = list(clf_result)
keywordList={'glass','mug','cup'}
top5_errorRate(clf_result,keywordList)



    