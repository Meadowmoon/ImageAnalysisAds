import os

def find_top5err (all_obj_detected,keywordList):
    n = len(outcome)/5 #number of images
    isInkeywordList = []
    
    for i in range (int(n)):
        obj_det = all_obj_detected[i*5:i*5+5]
        isInkeywordList.append(any(kw in "".join(obj_det) for kw in keywordList))
    
    return sum(isInkeywordList)/len(isInkeywordList)

def characterize_hashtag(TAG, keywordList):
    img_dir = os.listdir(TAG)    
    all_obj_detected = ()
    img_dict={}
    
    for img in img_dir:
        img_path = os.path.join(TAG,img)
        
        obj_detected = get_obj_detected(img_path)
        try:
            img_dict[img].append(obj_detected)
        except:
            pass        

        all_obj_detected += obj_detected[0]
                
    top5err = find_top5err(all_obj_detected,keywordList)
    
    with open("{}_obj_det.json".format(TAG),"w") as f:
        json.dump(img_dict,f,indent=4)
        
    with open("{}_obj_counter.json".format(TAG),"w") as f:
        json.dump(Counter(all_obj_detected).most_common(),f,indent=4)
     
    return Counter(all_obj_detected).most_common(),all_obj_detected, top5err


keywordList={'glass','mug','basin'}
tag_distribution, top5err = characterize_hashtag(TAG,keywordList)


    