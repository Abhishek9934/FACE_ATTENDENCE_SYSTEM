import face_recognition
import numpy as np
import cv2, queue, threading, time
import requests, os
from sklearn import svm
import mysql.connector
import pickle


def read_img(path):
    img = cv2.imread(path)
    (h, w) = img.shape[:2]
    width = 500
    ratio = width / float(w)
    height = int(h * ratio)
    return cv2.resize(img, (width, height))




def train():
	mydb = mysql.connector.connect(

		host="localhost",
		user="root",
		passwd="Abhishek@6204",
		database="database"
	)
	cursor = mydb.cursor()
	print("Training data ......")
	delq = "DELETE FROM new_table"
	cursor.execute(delq)
	mydb.commit()
	known_dir = 'Known'
	# temp()
	# generates all the encodings for the knowm faces
	for person in os.listdir(known_dir):
		for file in os.listdir(known_dir+'/'+person):
			img = read_img(known_dir +'/'+person+'/'+ file)
			faceloc = face_recognition.face_locations(img)
			if len(faceloc)==1:
				img_enc = face_recognition.face_encodings(img)[0]  # here we are selecting only the first face identified in the image
				# print(pickle.dumps(img_enc))
				query = "INSERT INTO new_table (name,face) VALUES (%s,%s) "
				val = (person,pickle.dumps(img_enc))
				cursor.execute(query,val)
				mydb.commit()
	cursor.close()
	mydb.close()


	#


def test():
	mydb = mysql.connector.connect(

		host="localhost",
		user="root",
		passwd="Abhishek@6204",
		database="database",
		use_pure="True"
	)
	cursor = mydb.cursor()

	known_face_encodings = []
	known_face_names = []

	query = "SELECT * FROM new_table"
	cursor.execute(query)
	res= cursor.fetchall()
	for x in res:

		known_face_encodings.append(pickle.loads(x[1]))
		known_face_names.append(x[0])
	# print(len(known_face_names))
	# print(known_face_encodings)

	clf = svm.SVC(gamma='scale')
	clf.fit(known_face_encodings, known_face_names)
	cursor.close()
	mydb.close()
	return clf



if __name__== "__main__":
	train()
# 	test()