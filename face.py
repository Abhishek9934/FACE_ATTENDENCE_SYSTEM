import face_recognition
import numpy as np
import cv2, queue, threading, time
import requests, os, re



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


video_capture = VideoCapture(0)


# function to read image and resize it into desired shape
def read_img (path):
	img = cv2.imread(path)
	(h, w) = img.shape[:2]
	width  = 500
	ratio = width / float(w)
	height = int (h * ratio)
	return cv2.resize(img, (width, height))


def draw_rectangle(face_locations,face_names,frame):

	for (top, right, bottom, left), name in zip(face_locations, face_names):
		
		cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

		# Draw a label with a name below the face
		# cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
		font = cv2.FONT_HERSHEY_DUPLEX
		cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


known_dir = 'Known'
known_face_encodings = []
known_face_names = []

#generates all the encodings for the knowm faces
for file in os.listdir(known_dir):
	img = read_img(known_dir+'/'+file)
	img_enc = face_recognition.face_encodings(img)[0]  #here we are selecting only the first face identified in the image
	known_face_encodings.append(img_enc)
	known_face_names.append (file.split('.')[0])



# print (known_face_encodings)


def detect_faces(frame):
	faceloc = face_recognition.face_locations(frame)
	if (len(faceloc))>0:
		return True
	return False



face_locations = []
face_encodings = []
face_names = []
process_this_frame = True


while True:
	# for i in range(5):
	#     video_capture.grab()
	# Grab a single frame of video
	frame = video_capture.read()
	
	# # Resize frame of video to 1/4 size for faster face recognition processing
	# small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
	# print(sys.exc_info())
	# Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
	# frame = frame[:, :, ::-1]
	
	# Process every frame only one time
	if process_this_frame:
		# Find all the faces and face encodings in the current frame of video
		face_locations = face_recognition.face_locations(frame)
		face_encodings = face_recognition.face_encodings(frame, face_locations)
		
		# Initialize an array for the name of the detected users
		face_names = []


		# * ---------- Initialyse JSON to EXPORT --------- *
		json_to_export = {}
		
		for face_encoding in face_encodings:
			# See if the face is a match for the known face(s)

			matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
			name = "Unknown"

			# # If a match was found in known_face_encodings, just use the first one.
		  #  if True in matches:
			 #   first_match_index = matches.index(True)
			#    name = known_face_names[first_match_index]

			# Or instead, use the known face with the smallest distance to the new face
			face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
			try:
				best_match_index = np.argmin(face_distances)
				if matches[best_match_index] and face_distances[best_match_index] <= 0.56:
					name = known_face_names[best_match_index]
			
				# * ---------- SAVE data to send to the API -------- *
					json_to_export['name'] = name
					json_to_export['hour'] = f'{time.localtime().tm_hour}:{time.localtime().tm_min}'
					json_to_export['date'] = f'{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday}'
					json_to_export['picture_array'] = frame.tolist()

				# * ---------- SEND data to API --------- *


			   # r = requests.post(url='http://127.0.0.1:5000/receive_data', json=json_to_export)
			   # print("Status: ", r.status_code)
			except ValueError:
				pass
			face_names.append(name)
		
	process_this_frame = not process_this_frame
			
			# Display the results
	draw_rectangle(face_locations,face_names,frame)


	# Display the resulting image
	cv2.imshow('Video', frame)

	# Hit 'q' on the keyboard to quit!
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break





video_capture.release()
cv2.destroyAllWindows()


