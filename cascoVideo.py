# -*- coding: utf-8 -*-
"""Casco.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lc143a2R4knBq40FlbOXKECbZRa8M4oi
"""

import os
import numpy as np
import random

import colorsys
import cv2

from mrcnn.config import Config
from mrcnn import model as modellib


model_filename = "mask_rcnn_casco_0050.h5"
class_names = ['BG', 'casco']
min_confidence = 0.6

#camera = cv2.VideoCapture(1)
camera = cv2.VideoCapture("video.mp4")

class CascoConfig(Config):
    """Configuration for training on the helmet  dataset.
    """
    # Give the configuration a recognizable name
    NAME = "casco"

    # Train on 1 GPU and 1 image per GPU. Batch size is 1 (GPUs * images/GPU).
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

    # Number of classes (including background)
    NUM_CLASSES = 1 + 1  # background + 1 (casco)

    # All of our training images are 512x512
    IMAGE_MIN_DIM = 512
    IMAGE_MAX_DIM = 512

    # You can experiment with this number to see if it improves training
    STEPS_PER_EPOCH = 500

    # This is how often validation is run. If you are using too much hard drive space
    # on saved models (in the MODEL_DIR), try making this value larger.
    VALIDATION_STEPS = 5
    
    # Matterport originally used resnet101, but I downsized to fit it on my graphics card
    BACKBONE = 'resnet50'

    # To be honest, I haven't taken the time to figure out what these do
    RPN_ANCHOR_SCALES = (8, 16, 32, 64, 128)
    TRAIN_ROIS_PER_IMAGE = 32
    MAX_GT_INSTANCES = 50 
    POST_NMS_ROIS_INFERENCE = 500 
    POST_NMS_ROIS_TRAINING = 1000 
    
config = CascoConfig()
config.display()

class InferenceConfig(CascoConfig):
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    #IMAGE_MIN_DIM = 512
    #IMAGE_MAX_DIM = 512
    DETECTION_MIN_CONFIDENCE = min_confidence
    

inference_config = InferenceConfig()

# Recreate the model in inference mode
model = modellib.MaskRCNN(mode="inference", config=inference_config,  model_dir='logs')

# Get path to saved weights
# Either set a specific path or find last trained weights
model_path = os.path.join('logs', model_filename)
#model_path = model.find_last()

# Load trained weights (fill in path to trained weights here)
assert model_path != "", "Provide path to trained weights"
print("Loading weights from ", model_path)
model.load_weights(model_path, by_name=True)

  

while camera:
    ret, frame = camera.read()
    frame = cv2.resize(frame, (640, 480), interpolation = cv2.INTER_AREA)
    
    results = model.detect([frame], verbose=0)
    r = results[0]
    
    N =  r['rois'].shape[0]
    boxes=r['rois']
    masks=r['masks']
    class_ids=r['class_ids']
    scores=r['scores']
    
       
    hsv = [(i / N, 1, 0.7) for i in range(N)]
    colors = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
    
    random.shuffle(colors)
    #print("N_obj:",N)
    masked_image = frame.astype(np.uint32).copy()
    
    for i in range(N):
        
        if not np.any(boxes[i]):
            # Skip this instance. Has no bbox. Likely lost in image cropping.
            continue

        color = list(np.random.random(size=3) * 256)
        mask = masks[:, :, i]
        alpha=0.5

        
        for c in range(3):
            masked_image[:, :, c] = np.where(mask == 1,
                                  masked_image[:, :, c] *
                                  (1 - alpha) + alpha * color[c],
                                  masked_image[:, :, c])
            
        
        frame_obj=masked_image.astype(np.uint8)
        y1, x1, y2, x2 = boxes[i]
        cv2.rectangle(frame_obj, (x1, y1), (x2, y2),color, 2)  
        
        class_id = class_ids[i]
        score = scores[i] if scores is not None else None
        label = class_names[class_id]
        caption = "{} {:.3f}".format(label, score) if score else label
        cv2.putText(frame_obj,caption,(int(x1), int(y1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        masked_image = frame_obj.astype(np.uint32).copy()
    
        
    if N>0:
        cv2.imshow('frame', frame_obj)
    else:
        cv2.imshow('frame', frame)
    
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break;
        
camera.release()
cv2.destroyAllWindows()