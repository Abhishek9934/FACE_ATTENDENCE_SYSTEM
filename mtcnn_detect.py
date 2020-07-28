
import cv2
from mnist import MNIST
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




def drawBoxes(bounding_box , keypoints):

	cv2.rectangle(image,
		          (bounding_box[0], bounding_box[1]),
		          (bounding_box[0]+bounding_box[2], bounding_box[1] + bounding_box[3]),
		          (0,155,255),
		          2)

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



def extract_faces(file):

	detector = MTCNN()

	image = Image.open(file)
	image = image.convert('RGB')

	pixels = asarray(image)

	result = detector.detect_faces(pixels)
	bounding_box = result[0]['box']
	keypoints = result[0]['keypoints']
	# drawBoxes(bounding_box,keypoints)

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


	return crop_face




def train():
	
	facenet_model = load_model('facenet_keras.h5')
	print('Loaded Model')

	face_list=[]
	labels = []
	known_dir = 'Known'
	# temp()
	# generates all the encodings for the knowm faces
	for person in os.listdir(known_dir):
		for file in os.listdir(known_dir+'/'+person):
			img_path = known_dir +'/'+person+'/'+ file
			# print(img_path)
			face = extract_faces(img_path)
			print (face)
			face_list.append(face)
			labels.append(person)
	
	X = asarray(face_list)
	y = asarray(labels)

	print(X)


 	#loading the facenet model
	print(X.shape , y.shape)
	embeddings = []
	for f in X:
		emd = getEmbeddings(facenet_model , f)
		embeddings.append(emd)
 	
	embeddings = asarray(embeddings)
	print(embeddings[0])
	print(embeddings.shape)
	savez_compressed('training-dataset-embeddings.npz',embeddings,y)


if __name__== "__main__":
	train()




