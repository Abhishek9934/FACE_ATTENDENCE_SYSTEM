

from keras_facenet import FaceNet
import numpy as np
import cv2, queue, threading, time
import requests, os
import sys
from sklearn import svm
import mysql.connector
from datetime import date,datetime
import statistics
import pickle




def train():
	
	embedder = FaceNet()
	embed_array=[]
	y=[]
	print("Training data ......")
	known_dir = 'Known'
	for person in os.listdir(known_dir):
		for file in os.listdir(known_dir+'/'+person):
			img = cv2.imread(known_dir +'/'+person+'/'+ file)
			detections = embedder.extract(img)
			for detection in detections:
				img_enc = detection['embedding']

				embed_array.append(img_enc)
				print(person)
				y.append(person)

	# print(embed_array[20])

	np.savez_compressed('training-dataset-embeddings.npz',embed_array,y)



if __name__== "__main__":
	train()
