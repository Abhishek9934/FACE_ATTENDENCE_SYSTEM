from numpy import asarray 
import os
from mtcnn import MTCNN

from os import listdir
from PIL import Image
from numpy import savez_compressed
from numpy import load
from numpy import expand_dims
from keras.models import load_model

from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC


import face_recognition
import numpy as np
import cv2, queue, threading, time
import requests, os
import sys
from sklearn import svm
import mysql.connector
from datetime import date,datetime
import statistics


detector = MTCNN()

facenet_model = load_model('facenet_keras.h5')
print('Loaded Model')

# bufferless VideoCapture
class VideoCapture:

  def __init__(self, name):
    self.cap = cv2.VideoCapture(name)
    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # read frames as soon as they are available, keeping only most recent one
  def _reader(self):
    while True:
      ret, frame = self.cap.read()
      if not ret:
        break
      if not self.q.empty():
        try:
          self.q.get_nowait()   # discard previous (unprocessed) frame
        except queue.Empty:
          pass
      self.q.put(frame)

  def read(self):
    return self.q.get()



def mark_attendence(face , table):
    mydb = mysql.connector.connect(

        host="localhost",
        user="root",
        passwd="Abhishek@6204",
        database="database",
        use_pure="True"
    )
    # print(table)
    cursor = mydb.cursor()
    today = date.today()
    # print(today)
    # today = today.strftime("%b,%d,%Y")
    # print(today)

    query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = %s; "
    cursor.execute(query,(today,))

    r = cursor.fetchall()
    if (len(r)==0):
        q= f"ALTER TABLE `database`.`{table}` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
        cursor.execute(q)

    mark = f"UPDATE `{table}` SET `{today}`= 1 WHERE name= %s"
    v= (face,)
    cursor.execute(mark,v)

    mydb.commit()
    cursor.close()
    mydb.close()



def drawBoxes(results, image):
            # Draw a label with a name below the face
    font = cv2.FONT_HERSHEY_DUPLEX
    s= 'Marking your Attendence. Please Wait.'
    cv2.putText(image,s,(50 , 40 ), font, 0.9, (0, 255, 255), 2)

    for result in results:
        bounding_box = result['box']
        keypoints = result['keypoints']
            
        cv2.rectangle(image,
                      (bounding_box[0], bounding_box[1]),
                      (bounding_box[0]+bounding_box[2], bounding_box[1] + bounding_box[3]),
                      (0,155,255),
                      2)
        cv2.putText(image, result['name'], (bounding_box[0], bounding_box[1]), font, 1.0, (0, 0, 255), 1)


        cv2.circle(image,(keypoints['left_eye']), 2, (0,155,255), 2)
        cv2.circle(image,(keypoints['right_eye']), 2, (0,155,255), 2)
        cv2.circle(image,(keypoints['nose']), 2, (0,155,255), 2)
        cv2.circle(image,(keypoints['mouth_left']), 2, (0,155,255), 2)
        cv2.circle(image,(keypoints['mouth_right']), 2, (0,155,255), 2)


def getEmbeddings(model , face):

    face = face.astype('float32')

    mean ,std = face.mean() , face.std()
    face = (face - mean) /std

    sample = expand_dims(face , axis =0)
    var = model.predict(sample)
    return var[0]



def extract_faces(image):


    # image = image.convert('RGB')
    face_locations=[]
    pixels = asarray(image)

    results = detector.detect_faces(pixels)
    facelist = []
    for result in results:

        bounding_box = result['box']
        keypoints = result['keypoints']
        # drawBoxes(bounding_box,keypoints)
        face_locations.append(bounding_box)
        x1 = bounding_box[0]
        y1 = bounding_box[1]
        width = bounding_box[2]
        height = bounding_box[3]
        x1,y1 = abs(x1) ,abs(y1)
        x2,y2 = x1+width , y1+height

        face = pixels[y1:y2,x1:x2]

        image =  Image.fromarray(face)
        image = image.resize((160,160))
        crop_face = asarray (image)
        facelist.append(crop_face)


    X = asarray(facelist)
    embeddings =[]

    for f in X:
        emd = getEmbeddings(facenet_model , f)
        embeddings.append(emd)

    # print(embeddings[0])

    # embeddings.asarray(embeddings)


    return results,embeddings







def detection(table):

    video_capture = VideoCapture(0)


    data = load('training-dataset-embeddings.npz')

        

    trainX, trainy = data['arr_0'], data['arr_1']
    # normalize input vectors
    in_encoder = Normalizer(norm='l2')
    trainX = in_encoder.transform(trainX)

    # label encode targets
    out_encoder = LabelEncoder()
    out_encoder.fit(trainy)
    trainy = out_encoder.transform(trainy)
    
    # fit model
    model = SVC(kernel='linear', probability=True)
    model.fit(trainX, trainy)
    

    i=0
    face_locations = []
    face_names = []
    process_this_frame = True
    start_time = datetime.now()


    while True:
            # Grab a single frame of video
        frame = video_capture.read()
        time_delta = datetime.now() - start_time

            # Process every frame only one time
        if process_this_frame:
                # Find all the faces and face encodings in the current frame of video
            # print(frame)
            results , face_encodings = extract_faces(frame)
            face_names = []
            index =0
            for face_encoding in face_encodings:
                #predictio for face
                # print(face_encoding)
                sample = expand_dims(face_encoding , axis =0)
                yhat_class = model.predict(sample)
                yhat_prob = model.predict_proba(sample)

                #getting name

                class_index = yhat_class[0]
                class_probability = yhat_prob[0, class_index] * 100
                predict_names = out_encoder.inverse_transform(yhat_class)

                name = predict_names[0]
                print (i)
                i=i+1
            
                mark_attendence(str(name), table)
                results[index]['name'] = name
                index=index+1

            face_encodings = []


            # print(face_names)

        process_this_frame = not process_this_frame
        window_width= 1500
        window_height = 800
        cv2.namedWindow('Recognising Face', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Recognising Face', window_width, window_height)
        drawBoxes(results, frame)
        cv2.imshow('Recognising Face', frame)

            # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # cv2.waitKey(1)
        # if ( time_delta.total_seconds() >= 15):
        #     break

    cv2.destroyAllWindows()


if __name__ == '__main__':
    
    arg = sys.argv[1]
    # arg = 'student'
    
    detection(arg)



    


