import cv2
import numpy as np
from math import sqrt

class CORNER:
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4

class OverlayOp:
    def __init__(self, display=False):        
        self.posx = 0  
        self.posy = 0          
        self.S = (0.1, 0.1, 0.1)  
        self.D = (0.9, 0.9, 0.9)      
        self.display = display      

    def RmoveBackground(self, image):
        if(self.display):
            cv2.imshow('Original', image)
            cv2.waitKey(0)
        copy = image.copy()
         
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        if(self.display):
            cv2.imshow('Gray', gray)
            cv2.waitKey(0)
        

        edged = cv2.Canny(gray, 10, 250)
        if(self.display):
            cv2.imshow('Edged', edged)
            cv2.waitKey(0)
         
        kernel = np.ones((3, 3), np.uint8)
         
        dilation = cv2.dilate(edged, kernel, iterations=1)
        if(self.display):
            cv2.imshow('open', dilation)
            cv2.waitKey(0)
         
        closing = cv2.morphologyEx(dilation, cv2.MORPH_CLOSE, kernel)
        if(self.display):
            cv2.imshow('Closing', closing)
            cv2.waitKey(0)
         
        (image, cnts, hiers) = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
         
        cont = cv2.drawContours(copy, cnts, -1, (0, 0, 0), 2, cv2.LINE_AA)
        if(self.display):
            cv2.imshow('Contours', cont)
            cv2.waitKey(0)
         
        mask = np.zeros(cont.shape[:2], dtype="uint8") * 255         
        
        cv2.drawContours(mask, cnts, -1, (255, 255, 255), -1)
        
        # remove the contours from the image and show the resulting images
        img = cv2.bitwise_and(cont, cont, mask=mask)
        if(self.display):
            cv2.imshow("Mask", img)
            cv2.waitKey(0)
         
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            if w > 50 and h > 50:
                new_img = img[y:y + h, x:x + w]                     
                if(self.display):
                    pass
                    #cv2.imshow("Cropped", new_img)
                    #cv2.waitKey(0)
        
        return img
    
    def OverlayImage(self, src, overlay, result_file):
        src_height, src_width = src.shape[:2]
        overlay_height, overlay_width = overlay.shape[:2]
        
        for x in range(overlay_width):
            if x + self.posx < src_width:
                for y in range(overlay_height):    
                    if y + self.posy < src_width:
                        source = src[y + self.posy, x + self.posx]
                        over = overlay[y, x]
                        merger = source
                        if(over[0] != 0 and over[1] != 0 and over[2] != 0):
                            merger = (self.S * source + self.D * over)                                 
                        src[y + self.posy, x + self.posx] = merger
                        
        if(self.display): 
            cv2.imshow('image', src) 
            cv2.waitKey(0) 
        cv2.imwrite(result_file, src)  # Saves the image
        
        return src
    
    def Operator(self, src_file, overlay_file, result_file="result.png", percentage = 0.10, corner = CORNER.BOTTOM_LEFT):
        # Load a source image
        src = cv2.imread(src_file)  
        # Load an image to overlay 
        overlay = cv2.imread(overlay_file)  
        src_height, src_width = src.shape[:2]
        overlay_height, overlay_width = overlay.shape[:2]
        src_size = src_height * src_width
        overlay_size = overlay_height * overlay_width
        ratio = percentage * src_size / overlay_size
        ratio = sqrt(ratio)
        if ratio > 1.0 :
            ratio = 1.0
        # Resize overlay image.
        overlay = cv2.resize(overlay, (0, 0), fx=ratio, fy=ratio) 
        overlay_height, overlay_width = overlay.shape[:2]
        overlay = self.RmoveBackground(overlay)        

        if corner == CORNER.TOP_LEFT :
            self.posx = 0
            self.posy = 0
        elif corner == CORNER.TOP_RIGHT :
            self.posx = src_width - overlay_width
            self.posy = 0
        elif corner == CORNER.BOTTOM_LEFT :
            self.posx = 0
            self.posy = src_height - overlay_height
        elif corner == CORNER.BOTTOM_RIGHT :
            self.posx = src_width - overlay_width
            self.posy = src_height - overlay_height
            
        return self.OverlayImage(src, overlay, result_file)
