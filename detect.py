import face_recognition
import numpy as np
import cv2, queue, threading, time
import requests, os
from sklearn import svm
from train import train
from train import test
import mysql.connector
from datetime import date,datetime


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
                    self.q.get_nowait()  # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()


video_capture = VideoCapture(0)


def mark_attendence(face):
    mydb = mysql.connector.connect(

        host="localhost",
        user="root",
        passwd="Abhishek@6204",
        database="database",
        use_pure="True"
    )
    cursor = mydb.cursor()
    today = date.today()
    print(today)
    # today = today.strftime("%b,%d,%Y")
    print(today)
    query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'student' AND COLUMN_NAME = %s; "
    cursor.execute(query,(today,))
    r = cursor.fetchall()
    if (len(r)==0):
        q= f"ALTER TABLE `database`.`student` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
        cursor.execute(q)


    mark = f"UPDATE student SET `{today}`= 1 WHERE name=%s"
    v= (face,)
    cursor.execute(mark,v)


    mydb.commit()
    cursor.close()
    mydb.close()






# function to read image and resize it into desired shape
def read_img(path):
    img = cv2.imread(path)
    (h, w) = img.shape[:2]
    width = 500
    ratio = width / float(w)
    height = int(h * ratio)
    return cv2.resize(img, (width, height))


def draw_rectangle(face_locations, face_names, frame):
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 0, 255), 1)
        s= 'Marking your Attendence. Please Wait.'
        cv2.putText(frame,s,(50 , 40 ), font, 0.9, (0, 255, 255), 2)

def draw_rectangle1(face_locations ,face_names ,frame):
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 128, 0), 2)

        # Draw a label with a name below the face
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 255, 255), 1)
        s= 'Attendence Marked'
        cv2.putText(frame,s,(100 , 50 ), font, 1.2, (0,128,34), 2)


clf = test()
face_locations = []
face_encodings = []
# face_names = []
process_this_frame = True
start_time = datetime.now()


while True:
    # Grab a single frame of video
    frame = video_capture.read()
    time_delta = datetime.now() - start_time

    # Process every frame only one time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        # Initialize an array for the name of the detected users
        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            # name= 'UNKNOWN'
            name=clf.predict([face_encoding])
            print (*name)
            if(name):

                mark_attendence(str(*name))
            face_names.append(*name)

        # print(face_names)

    process_this_frame = not process_this_frame

    # Display the results
    window_width= 1500
    window_height = 800
    cv2.namedWindow('Recognising Face', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Recognising Face', window_width, window_height)
    if time_delta.total_seconds() < 5:
        draw_rectangle(face_locations, face_names, frame)
    else:
        draw_rectangle1(face_locations , face_names ,frame)

    # Display the resulting image
    cv2.imshow('Recognising Face', frame)
    # cv2.waitKey(10)

    # Hit 'q' on the keyboard to quit!
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break
    cv2.waitKey(1)
    if ( time_delta.total_seconds() >= 8):
        break

video_capture.release()
cv2.destroyAllWindows()



