import os
import time
import pandas as pd
import subprocess
from collections import Counter
from statistics import mean
import glob

os.chdir('C:\\myProj\\ImageAnalysisAds\\ImageAnalysisAds.Crawler')

def get_obj_detected (TAG='cups'):
    '''call classify_image.py and return csv of classification results'''
    st=time.time()
    STD = ["python", "classify_image.py", "--model_dir", "model_dir"]
    process = subprocess.Popen(
            STD + ["--tag",TAG],
            shell=1
			#,stdout=subprocess.PIPE,
            #stderr=subprocess.PIPE
			)
    
    #_stdout,_ = process.communicate()
    print (time.time()-st)
   

def combine_result (TAG='cups'):
    result = pd.DataFrame([])
    for csv in glob.glob('{}_result_*'.format(TAG)):
        res = pd.read_csv(csv,header=None)
        result = result.append(res)
    
    result.to_csv('{}_result.csv'.format(TAG), index=False, header=False)
    
    return list(result[0])

#def remove_checkpoints (TAG='cups'):
#    for csv in glob.glob('{}_result_*'.format(TAG)):
#        os.remove(csv)


def count_classification(clf_result,num_to_show=30):
    '''    
        clf_result: list of image classification results    
    '''    
    def round2 (float):
    #convert float to 2dp percentage
        return round(float*100,2)

    n = len(clf_result)
    counter = Counter(clf_result).most_common(num_to_show)
    res = [(item,round2(c/n)) for item,c in counter]
     
    return res

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


if __name__ == '__main__':
	TAG='cups'
	get_obj_detected(TAG='cups')
    
    #clf_result = list(pd.read_csv('{}_result.csv'.format(TAG), header=None)[0])
    clf_result = combine_result (TAG='cups')
    
    sorted_result = count_classification(clf_result)
	
	keywordList={'glass','mug','cup','coffee'}
	top5_errorRate(clf_result,keywordList) # 0.3918918918918919



    