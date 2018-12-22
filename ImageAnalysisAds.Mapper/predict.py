import tensorflow as tf
import numpy as np
import os, glob, cv2
import sys, argparse


class Prediction:    
    
    def __init__(self, model_name, check_point, image_size):
        # # Let us restore the saved model 
        self.sess = tf.Session()
        # Recreate the network graph. At this step only graph is created.
        self.saver = tf.train.import_meta_graph(model_name)
        # Load the weights saved using the restore method.
        self.saver.restore(self.sess, tf.train.latest_checkpoint(check_point))    
        # Accessing the default graph which we have restored
        self.graph = tf.get_default_graph()    
        # In the original network y_pred is the tensor that is the prediction of the network
        self.y_pred = self.graph.get_tensor_by_name("y_pred:0")    
        # # Let's feed the images to the input placeholders
        self.x = self.graph.get_tensor_by_name("x:0") 
        self.y_true = self.graph.get_tensor_by_name("y_true:0") 
        self.y_test_images = np.zeros((1, len(next(os.walk(check_point))[1])))     
        # # Image settings
        self.image_size = image_size
        self.num_channels = 3
    
    def Predict2(self, image, show=True):
        # Reading the image using OpenCV
        images = []
        if show :
            cv2.imshow('O', image)
            cv2.waitKey(0)
        # Resizing the image to our desired size and preprocessing will be done exactly as done during training
        image = cv2.resize(image, (self.image_size, self.image_size), 0, 0, cv2.INTER_LINEAR)
        images.append(image)
        images = np.array(images, dtype=np.uint8)
        images = images.astype('float32')
        images = np.multiply(images, 1.0 / 255.0) 
        # The input to the network is of shape [None image_size image_size num_channels]. Hence we reshape.
        x_batch = images.reshape(1, self.image_size, self.image_size, self.num_channels)
        
        # ## Creating the feed_dict that is required to be fed to calculate y_pred 
        feed_dict_testing = {self.x: x_batch, self.y_true: self.y_test_images}
        result = self.sess.run(self.y_pred, feed_dict=feed_dict_testing)
        return result
    
    def Predict(self, filename):
        image = cv2.imread(filename)
        self.Predict2(image)