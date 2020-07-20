from keras_facenet import FaceNet
import numpy as np
import cv2, queue, threading, time
import requests, os
import sys
from sklearn import svm
from train import train
from train import test
import mysql.connector
from datetime import date,datetime
import statistics

from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC


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



def mark_attendence(face , table):
    mydb = mysql.connector.connect(

        host="localhost",
        user="root",
        passwd="Abhishek@6204",
        database="database",
        use_pure="True"
    )
    print(table)
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




def detection(table):

    embedder = FaceNet()
    video_capture = VideoCapture(0)
    # face_locations=[]
    
    process_this_frame = True
    start_time = datetime.now()

    data = np.load('training-dataset-embeddings.npz')
    trainX, trainy = data['arr_0'], data['arr_1']
    in_encoder = Normalizer(norm='l2')
    trainX = in_encoder.transform(trainX)

	# label encode targets
    out_encoder = LabelEncoder()
    out_encoder.fit(trainy)
    trainy = out_encoder.transform(trainy)

	# fit model
    model = SVC(kernel='linear', probability=True)
    model.fit(trainX, trainy)

    while True:
            # Grab a single frame of video
        frame = video_capture.read()
        time_delta = datetime.now() - start_time

            # Process every frame only one time
        if process_this_frame:
                # Find all the faces and face encodings in the current frame of video
            
            detections = embedder.extract(frame, threshold=0.95)


                # Initialize an array for the name of the detected users
            face_names = []
            face_locations=[]
            for detection in detections:
                    # See if the face is a match for the known face(s)
                    # name= 'UNKNOWN'
                face_encoding = detection['embedding']
                sample = np.expand_dims(face_encoding , axis =0)
                yhat_class = model.predict(sample)
                yhat_prob = model.predict_proba(sample)

                #getting name

                class_index = yhat_class[0]
                class_probability = yhat_prob[0, class_index] * 100
                predict_names = out_encoder.inverse_transform(yhat_class)

                name = predict_names[0]
                print (name)

                
                if(name):
                    mark_attendence(str(name), table)
                    detection['name'] = name

                    # face_names.append(*name)
                    # face_locations = face_locations.append( detection['box'])

                # face = statistics.mode(face_names)
           

	            # print(face_names)

        process_this_frame = not process_this_frame

            # Display the results
        window_width= 1500
        window_height = 800
        cv2.namedWindow('Recognising Face', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Recognising Face', window_width, window_height)
        # if time_delta.total_seconds() < 5:
        #     draw_rectangle(face_locations, face_names, frame)
        # else:
        #     draw_rectangle1(face_locations , face_names ,frame)
        # drawBoxes(face_locations , face_names ,frame)       
            # Display the resulting image

        drawBoxes(detections , frame)
        cv2.imshow('Recognising Face', frame)
            # cv2.waitKey(10)

            # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        # cv2.waitKey(1)
        # if ( time_delta.total_seconds() >= 8):
        #     break

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    
    arg = sys.argv[1]
    
    detection(arg)



    


