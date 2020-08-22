from flask import Flask, render_template, request, redirect, url_for, flash, session,g
import mysql.connector
import os
import datetime
from openpyxl import Workbook
from base64 import b64encode
from keras_facenet import FaceNet
import numpy as np
import cv2
from PIL import Image
from mtcnn import MTCNN
# import facenet as 
import statistics
import pickle

from keras.models import load_model


from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC


embedder = MTCNN()
# detector = FaceNet()

facenet_model = load_model('facenet_keras.h5')
print('Loaded Model')

def CONNECTION():
    mydb =  mysql.connector.connect(

        host="localhost",
        user="admin",
        passwd="Abhishek@6204",
        database="MyDatabase",
        use_pure="True"
    )
    return mydb





def drawBoxes(image, bounding_box):
        cv2.rectangle(image,(bounding_box[0], bounding_box[1]),(bounding_box[0]+bounding_box[2], bounding_box[1] + bounding_box[3]),(255,0,0),2)

def distance(emb1, emb2):
 return np.sum(np.square(emb1 - emb2))


def getEmbeddings(face):
    face = face.astype('float32')

    mean ,std = face.mean() , face.std()
    face = (face - mean) /std

    sample = np.expand_dims(face , axis =0)
    var = facenet_model.predict(sample)
    return var[0]

def mark_attendence(face , table):
    mydb = CONNECTION()
    # print(table)
    cursor = mydb.cursor()
    today = datetime.date.today()
    

    try:
        query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = %s; "
        cursor.execute(query,(today,))
        r = cursor.fetchall()
        if (len(r)==0):
            q= f"ALTER TABLE `MyDatabase`.`{table}` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
            cursor.execute(q)

        mark = f"UPDATE `{table}` SET `{today}`= 1 WHERE name= %s"
        v= (face,)
        cursor.execute(mark,v)
        mydb.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        return err.msg
    
    cursor.close()
    mydb.close()


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

#-----------------------------ROUTES----------------------------####


@app.route('/')
def index():
    try:
        return render_template('index.html')

    except Exception as e:
        return e


@app.route('/about')
def about():
    try:
        return render_template('doc.html')
    except Exception as e:
        return e


########################################### Loads the face recogniser #######################################################


@app.route('/markattendance/<string:id>', methods = ['GET','POST'])
def markattendace(id):
    try:
        if(request.method == 'POST'):
            names = []
            file = request.files['file']
            table = request.form['classname']

            imagede = Image.open(file)
            imagede = imagede.convert('RGB')

            pixels = np.asarray(imagede)

            print("face detection started")
            results = embedder.detect_faces(pixels)
            facelist = []
            # print("reusts" , results)
            mydb = CONNECTION()
            cursor=mydb.cursor()
            today = datetime.date.today()        
            query = f" SELECT name,FaceData,`{today}` FROM `{table}` "
            cursor.execute(query)
            res = cursor.fetchall()
          #  print("reeeeeeeeeeeeesssssssss" , type(res[0][1]))

            # embeddings = [pickle.loads(x[1]) for x in res]
            embeddings = []
            namelist = []
            # AttendanceList = []
            for x in res:
                # x= list(x)
                namelist.append(x[0])

                s = x[1][1:]
                s = s[:-2]
                s= s.split()
                arr = np.asarray(s)
                y = arr.astype(np.float)
                # print(y)
                embeddings.append(y)
                # d =  pickle.loads(x[1])
                # print(d)


            for result in results:

                bounding_box = result['box']
                
                drawBoxes(pixels,bounding_box)
                #face_locations.append(bounding_box)
                x1 = bounding_box[0]
                y1 = bounding_box[1]
                width = bounding_box[2]
                height = bounding_box[3]
                x1,y1 = abs(x1) ,abs(y1)
                x2,y2 = x1+width , y1+height

                face = pixels[y1:y2,x1:x2]

                image =  Image.fromarray(face)
                image = image.resize((160,160))
                crop_face = np.asarray (image)
                facelist.append(crop_face)

            X = np.asarray(facelist)
            print("embeddings started")
            img2= pixels
            img2 = img2[:,:,::-1]


            success, encoded_image = cv2.imencode('.jpg',img2)
            content2 = encoded_image.tobytes()
            classphoto = b64encode(content2).decode("utf-8")   



            for f in X:
                face_encoding = getEmbeddings(f)
               # print("type fo face encodings",(face_encoding))
                mylist = []
                for embedding in embeddings:
                    dist = distance(face_encoding , embedding)
                    mylist.append(dist)

                print ("Attendance face distances" , mylist)

                arr = np.array(mylist)
                minindex = np.argmin(arr)

  
                if(mylist[minindex] < 100):
                   # print("identified face " ,namelist[minindex])

                    mark_attendence(namelist[minindex], table)

            mydb = CONNECTION()
            cursor=mydb.cursor()
            today = datetime.date.today()        
            query = f" SELECT name,`{today}` FROM `{table}` "
            cursor.execute(query)
            res = cursor.fetchall()
            # flash("Attendance Marked Successfully!")
            return render_template('attendanceform.html',table= table,id= id ,image=classphoto, students= res , l = len(res))

        return redirect(url_for('facultyhome',id = id))

    except Exception as e:
        return e


@app.route('/attendanceform/<string:table>/<string:id>' , methods = ['GET','POST'])
def attendanceform(table,id):
    try:
        if request.method == 'POST':
            form = request.form
           # print("formmmmmmm,",form)
            mydb = CONNECTION()
            cursor=mydb.cursor()
            today = datetime.date.today()
            l = int(request.form['length'])
            for i in range(1,l+1):
                idx = f"atten{i}"
                name = f"name{i}"
                atten = form[idx]
                namedata = form[name]

                try:

                    query = f" UPDATE `{table}` SET `{today}`= %s WHERE name= %s "
                    cursor.execute(query,(atten,namedata,))
                    mydb.commit()

                except mysql.connector.Error as err:
                    print(err)
                    print("Error Code:", err.errno)
                    print("SQLSTATE", err.sqlstate)
                    print("Message", err.msg)
                    return err.msg
            flash("Attendance Marked Successfully!")
        
            return redirect(url_for('facultyhome',id = id))

    except Exception as e:
        return e


######################ADMIN PANEL ROUTES ##################################################

@app.route('/login',methods= ['GET','POST'])
def login():
    try:
        if request.method == 'POST':
            session.pop('user',None)
            if request.form['username'] != 'admin' or request.form['password'] != 'is_admin_secure?':
                flash('Invalid Credentials. Please try again.')
                # return alert('Invalid Credentials. Please try again.')
            else:
                session['user'] = request.form['username']
                return redirect(url_for('admin'))

        return redirect(url_for('index'))

    except Exception as e:
        return e

@app.route('/admin')
def admin():
    try:
        if g.user == 'admin':
            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:
                query = "SELECT * FROM StudentRecord"
                cursor.execute(query)
                res = cursor.fetchall()

                cur = mydb.cursor()
                cur.execute("SELECT * FROM TeacherRecord")
                res1 = cur.fetchall()
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
             
            # table_list = table_list[1:]
            # print(table_list)

            return render_template('admin.html' ,teachers = res1, students = res)
        return redirect(url_for('index'))

    except Exception as e:
        return e


###
@app.route('/classes/<string:table>/<string:id>')
def database(table,id):
    try:
        mydb = CONNECTION()
        cursor = mydb.cursor()
        today = datetime.date.today()

        try:

            query1 = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = %s;"
            cursor.execute(query1,(today,))
            r = cursor.fetchall()
            if (len(r)==0):
                q= f"ALTER TABLE `MyDatabase`.`{table}` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
                cursor.execute(q)
            cursor.execute(f"SELECT * FROM `{table}`")
            res= cursor.fetchall()
            # print("dkdkkdk",res)
            result = []
            for r in res:
                s=0

                # print(type(r[2]))
                for i in range(4,len(r)):
                    s=s+r[i]
                atper = (s/(len(r)-4)) * 100

                r1 = list(r)    
                x = r1[2]
                image = x.decode("utf-8")
                r1[2]=image
                r1.insert(4,atper)
                result.append(r1)
               # print(r1)


            col= cursor.column_names
            col = list(col) 
            col.insert(3,'Attendance %')
          #  print(col)
        except mysql.connector.Error as err:
            print(err)
            print("Error Code:", err.errno)
            print("SQLSTATE", err.sqlstate)
            print("Message", err.msg)
            return err.msg
        
        return render_template('database.html',att= result ,col= col,l=len(col) ,id = id, classname = table)


    except Exception as e:
        return e

###
@app.route('/insert/<string:table>/<string:tid>' ,methods = ['POST'])
def insert(table,tid):
    try:
        if request.method == 'POST':

            flash("Data Inserted Successfully")
            name = request.form['name']
            id = request.form['id']
            file = request.files['file']   

            imagede = Image.open(file)
            imagede = imagede.convert('RGB')

            pixels = np.asarray(imagede)
            img = pixels
            img = img[:,:,::-1]
            images = []
            detections = embedder.detect_faces(pixels)
            bounding_box = detections[0]['box']
            x1 = bounding_box[0]
            y1 = bounding_box[1]
            width = bounding_box[2]
            height = bounding_box[3]
            x1 = abs(x1)
            y1 = abs(y1)
            x2 =  x1+width 
            y2 = y1+height

            face = pixels[y1:y2,x1:x2]

            photo =  Image.fromarray(face)
            photo = photo.resize((160,160))
            crop_face = np.asarray (photo)
            emd = getEmbeddings(crop_face)
            emd = str(emd)

            crop_image =  img[bounding_box[1]-20:bounding_box[1]+ bounding_box[3]+20,bounding_box[0]-20:bounding_box[0]+ bounding_box[2]+20]

            if(crop_image.any()):
                success, encoded_image = cv2.imencode('.jpg', crop_image)
                content2 = (encoded_image).tobytes()
                image = b64encode(content2).decode("utf-8")
            else:
                return "No Face Detected.Please Upload a different Photograph."

            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:

                query = f"INSERT INTO `{table}` (Id,name,Image,FaceData) VALUES (%s,%s,%s,%s)"
                cursor.execute(query,(id,name,image,emd,))
                mydb.commit()
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            
            cursor.close()
            mydb.close()
            return redirect(url_for('database',table = table,id = tid))


    except Exception as e:
        return e

####
@app.route('/update/<string:table>/<string:tid>', methods = ['POST','GET'])
def update(table,tid):
    try:
        if request.method == 'POST':
            id = request.form['id']
            newid = request.form['newid']
            name = request.form['name']
            file = request.files['file']
            
            imagede = Image.open(file)
            imagede = imagede.convert('RGB')
            facelist = []
            pixels = np.asarray(imagede)
            img = pixels
            img = img[:,:,::-1]
            images = []
            detections = embedder.detect_faces(pixels)
            bounding_box = detections[0]['box']
            x1 = bounding_box[0]
            y1 = bounding_box[1]
            width = bounding_box[2]
            height = bounding_box[3]
            x1 = abs(x1)
            y1 = abs(y1)
            x2 =  x1+width 
            y2 = y1+height

            face = pixels[y1:y2,x1:x2]

            photo =  Image.fromarray(face)
            photo = photo.resize((160,160))
            crop_face = np.asarray (photo)
            emd = getEmbeddings(crop_face)
            emd = str(emd)

         #   print(emd)
            # emd = pickle.dumps(emd)

            crop_image =  img[bounding_box[1]-20:bounding_box[1]+ bounding_box[3]+20,bounding_box[0]-20:bounding_box[0]+ bounding_box[2]+20]

            if(crop_image.any()):
                success, encoded_image = cv2.imencode('.jpg', crop_image)
                content2 = (encoded_image).tobytes()
                image = b64encode(content2).decode("utf-8")
            else:
                return "No Face Detected.Please Upload a different Photograph."

            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:
                query = f"UPDATE `{table}` SET Id =%s,name=%s,Image=%s,FaceData=%s WHERE Id= %s; "
                cursor.execute(query,(newid,name,image,emd,id,))
                flash("Data Updated Successfully")
                mydb.commit()
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            
            return redirect(url_for('database',table = table,id =tid ))

    except Exception as e:
        return e



@app.route('/updatestudent', methods = ['POST','GET'])
def updstudent():
    try:
        if request.method == 'POST':
            id = request.form['id']
            newid = request.form['newid']
            name = request.form['name']
            email = request.form['email']
            f = request.files['file']
            data = f.read()
            dob = request.form['dob']
            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:
                query = f" UPDATE StudentRecord SET Id =%s ,Name=%s ,Image=%s ,Email= %s, DOB=%s  WHERE Id= %s "
                cursor.execute(query,(newid,name,data,email,dob,id,))
                flash("Data Updated Successfully")
                mydb.commit()
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            
            return redirect(url_for('admin'))

    except Exception as e:
        return e



@app.route('/updateteacher', methods = ['POST','GET'])
def updteacher():
    try:
        if request.method == 'POST':
            id = request.form['id']
            name = request.form['name']
            email = request.form['email']

            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:
                query = f" UPDATE TeacherRecord SET TeacherName =%s ,Email=%s WHERE TeacherName= %s "
                cursor.execute(query,(name,email,id,))
                q = f"UPDATE TeacherClasses SET TeacherName=%s WHERE TeacherName=%s"
                cursor.execute(q,(name,id))
                flash("Data Updated Successfully")
                mydb.commit()
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            
            return redirect(url_for('admin'))

    except Exception as e:
        return e

@app.route('/del/<string:id>',methods = ['GET'])
def delstudent(id):
    try:
        mydb = CONNECTION()
        cursor = mydb.cursor()
        cursor.execute(f"DELETE FROM StudentRecord WHERE Id = %s" ,(id,))
        mydb.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        return err.msg
    cursor.close()
    mydb.close()

    return redirect(url_for('admin'))

@app.route('/deleteteacher/<string:id>',methods = ['GET'])
def delteacher(id):
    try:
        mydb = CONNECTION()
        cursor = mydb.cursor()
        cursor.execute(f"DELETE FROM TeacherRecord WHERE TeacherName = %s" ,(id,))
        mydb.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        return err.msg
    cursor.close()
    mydb.close()

    return redirect(url_for('admin'))
    



@app.route('/delete/<string:table>/<string:tid>/<string:id>',methods = ['GET'])
def delete(table,id,tid):
    try:
        flash("Record Has been Deleted Successfully")
        mydb = CONNECTION()
        cursor = mydb.cursor()
        cursor.execute(f"DELETE FROM `{table}` WHERE id = %s" ,(id,))
        mydb.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        return err.msg
    
    cursor.close()
    mydb.close()

    return redirect(url_for('database',table= table,id=tid))



@app.route('/teacherlogin',methods = ['GET','POST'])
def teacherlogin():
    try:

        if request.method == 'POST':

            session.pop('user',None)
            name = request.form['name']
            password = request.form['password']
            mydb= CONNECTION()
            cursor= mydb.cursor()
            try:
                cursor.execute("SELECT password FROM TeacherRecord  WHERE TeacherName=%s",(name,))
                d= cursor.fetchone()
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            
            if (d!=None and d[0] == str(password)):
                session['user'] = request.form['name']
                return  redirect(url_for('facultyhome', id = name))
            else:
                flash('Invalid Credentials. Please try again.')
        return  redirect(url_for('index'))


    except Exception as e:
        return e


############################################################# route for student panel #######################################

@app.route('/studentlogin', methods =['GET','POST'])
def studentlogin():
    try:
        if request.method == 'POST':

            session.pop('user',None)
            id = request.form['id']
            birth = request.form['dob']
            mydb= CONNECTION()
            cursor= mydb.cursor()
            try:

                cursor.execute("SELECT DOB FROM StudentRecord  WHERE Id=%s",(id,))
                d= cursor.fetchone()
            
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            
            # print(birth)
            if (d!=None and d[0] == str(birth)):
                session['user'] = request.form['id']
                return  redirect(url_for('studenthome', id=id))
            else:
                flash('Invalid Credentials. Please try again.')
        return  redirect(url_for('index'))

    except Exception as e:
        return e

@app.route('/student/<string:id>')
def studenthome(id):
    try:
        if g.user == str(id):
            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:
                query = "SHOW TABLES"
                cursor.execute(query)
                res = cursor.fetchall()
                cursor.close()
                table_list = [x[0] for x in res]
                classes=[]
                for table in table_list:
                    cur = mydb.cursor()
                    if table == 'new_table' or table == 'StudentRecord' or table == 'TeacherRecord' or table == 'TeacherClasses':
                        continue
                    q= f"SELECT 1 FROM `{table}` WHERE Id =%s"
                    cur.execute(q,(id,))
                    flag = cur.fetchall()
                    if (len(flag)>= 1):
                        classes.append(table)
            
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            # print(classes)

            return  render_template('student.html',classes = classes,id = id ,classlist = table_list)
        return redirect(url_for('index'))

    except Exception as e:
        return e




@app.route('/student/<string:table>/<string:id>', methods = ['GET','POST'])
def studentpage(table,id):
    # print(g.user)
    try:        
        if g.user == str(id):
            # session.pop('user',None)
            mydb= CONNECTION()
            cursor = mydb.cursor()
            try:
                query = f"SELECT * FROM StudentRecord WHERE Id =%s"
                cursor.execute(query,(id,))
                data = cursor.fetchall()
                # print("lnajlnvernladblrvanlljn")
                # print(data[0][1])

                image = b64encode(data[0][2]).decode("utf-8")
                # print(names)
                # print(l)
                cursor.close()
                cur=  mydb.cursor()
                query = f"SELECT * FROM `{table}` WHERE Id =%s"
                cur.execute(query,(id,))
                res = cur.fetchall()
                names = cur.column_names
                l =len(names)

            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            return render_template('home.html',names= names, data = data , l= l,image = image,att = res ,tab = table)
        return redirect(url_for('index'))

    except Exception as e: 
        return e



@app.route('/register',methods = ['GET','POST'])
def register():
    try:
        if request.method=='POST':

            flash("You have been registered successfully!!!")
            name = request.form['name']
            id = request.form['id']
            email = request.form['email']
            f = request.files['file']
            data = f.read()
            dob = request.form['dob']
            # print(type(data))
            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:
                query = f"INSERT INTO StudentRecord (Id,Name,Image,Email,DOB) VALUES (%s,%s,%s,%s,%s)"

                cursor.execute(query,(id,name,data,email,dob))
                mydb.commit()
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            cursor.close()
            mydb.close()

        return redirect(url_for('index'))

    except Exception as e:
        return e


@app.route('/registerclass/<string:table>/<string:id>' ,methods = ['GET','POST'])
def registerclass(table,id):
    try:
        if request.method == 'POST':
            file = request.files['file']
            imagede = Image.open(file)
            imagede = imagede.convert('RGB')

            pixels = np.asarray(imagede)
            img = pixels
            img = img[:,:,::-1]
            images = []
            detections = embedder.detect_faces(pixels)
            # print(detections)
            facelist = []
                
            for detection in detections:

                bounding_box = detection['box']
                x1 = bounding_box[0]
                y1 = bounding_box[1]
                width = bounding_box[2]
                height = bounding_box[3]
                x1 = abs(x1)
                y1 = abs(y1)
                x2 =  x1+width 
                y2 = y1+height

                face = pixels[y1:y2,x1:x2]

                photo =  Image.fromarray(face)
                # print(photo)
                # print("photosize" , photo.size)
                photo = photo.resize((160,160))
                # facelist.append(photo)

                crop_face = np.asarray (photo)
                # print(crop_face)
                emd = getEmbeddings(crop_face)
                facelist.append(emd)
                crop_image =  img[bounding_box[1]-10:bounding_box[1]+ bounding_box[3]+15,bounding_box[0]-10:bounding_box[0]+ bounding_box[2]+15]

                if(crop_image.any()):
                    success, encoded_image = cv2.imencode('.jpg', crop_image)
                    content2 = (encoded_image).tobytes()
                    image = b64encode(content2).decode("utf-8")
                    images.append(image)


          #  print(facelist)
            return render_template('faceregister.html',embeddings = facelist,l= len(detections),images = images ,table = table , id = id)

        return redirect(url_for('index'))


    except Exception as e:
        return e





@app.route('/classregface/<string:table>/<string:id>', methods=['GET','POST'])
def register_all_face(table,id):
    try:
        if request.method == 'POST':
            form = request.form
          #  print("formmmm",form)
            l = int(request.form['length'])
            # print(l)
            # # l = len(form)/2+1
            mydb= CONNECTION()
            cursor=mydb.cursor()
            for i in range(1,l+1):
                idx = f"id{i}"
                name = f"name{i}"
                xx = f"image{i}"
                yy = f"embedding{i}"

                iddata = form[idx]
                namedata = form[name]
                data = form[xx]
                facedata = form[yy]
              #  print(facedata)
                # crop_face = np.asarray(facedata)
                # print("ccccccccccccccccccccccccccccccccccccccccccccc",crop_face)

                try:
                    if(iddata!='' and namedata!=''):
                        query = f"INSERT INTO `{table}` (Id,name,Image,FaceData) VALUES (%s,%s,%s,%s)"
                        cursor.execute(query,(iddata,namedata,data,facedata,))
                        mydb.commit()

                except mysql.connector.Error as err:
                    print(err)
                    print("Error Code:", err.errno)
                    print("SQLSTATE", err.sqlstate)
                    print("Message", err.msg)
                    return err.msg
            flash("Students registered Successfully. ")


                # print(iddata,namedata)



            return redirect (url_for('facultyhome',id = id))


    except Exception as e:
        return e       





@app.route('/facultyreg',methods = ['GET','POST'])
def facultyreg():
    try:
        if request.method=='POST':

            name = request.form['name']
            email = request.form['email']
            password = request.form['password1']
            password2 = request.form['password2']

            if(password == password2):
                # print(type(data))
                mydb = CONNECTION()
                cursor = mydb.cursor()
                try:
                    query = f"INSERT INTO TeacherRecord (TeacherName,Email,password) VALUES (%s,%s,%s)"

                    cursor.execute(query,(name,email,password))
                    mydb.commit()
                except mysql.connector.Error as err:
                    print(err)
                    print("Error Code:", err.errno)
                    print("SQLSTATE", err.sqlstate)
                    print("Message", err.msg)
                    return err.msg
                cursor.close()
                mydb.close()
                flash("You have been registered successfully!!!")

            else:
                flash("Password do not match.")

        return redirect(url_for('index'))


    except Exception as e:
        return e


@app.route('/faculty/<string:id>')
def facultyhome(id):
    try:
        if g.user == str(id):
            mydb = CONNECTION()
            cursor = mydb.cursor()
            try:
                query = "SELECT ClassName FROM TeacherClasses WHERE TeacherName = %s"
                cursor.execute(query , (id,))
                res = cursor.fetchall()
                table_list = [x[0] for x in res]

                # print(table_list)
            except mysql.connector.Error as err:
                print(err)
                print("Error Code:", err.errno)
                print("SQLSTATE", err.sqlstate)
                print("Message", err.msg)
                return err.msg
            return  render_template('teacher.html',classes = table_list ,id = id)
        return redirect(url_for('index'))

    except Exception as e:
        return e

@app.route('/createclass/<string:name>' ,methods= ['GET','POST'])
def classcreate(name):
    try:
        classname = request.form['classname']
        # print(name)

        # print(classname)
        mydb = CONNECTION()
        try:
            cursor = mydb.cursor()

            query = f"CREATE TABLE `MyDatabase`.`{classname}` (`Id` VARCHAR(45) NULL,`name` VARCHAR(45) NULL ,`Image` LONGBLOB NULL , `FaceData` LONGBLOB NULL);"
            cursor.execute(query)
            today = datetime.date.today()
            q= f"ALTER TABLE `MyDatabase`.`{classname}` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
            cursor.execute(q)

            cur = mydb.cursor()
            q = f"INSERT INTO TeacherClasses (TeacherName,ClassName) VALUES (%s,%s)"
            cur.execute(q,(name, classname,))
            cur.close()
            mydb.commit()
        except mysql.connector.Error as err:
            print(err)
            print("Error Code:", err.errno)
            print("SQLSTATE", err.sqlstate)
            print("Message", err.msg)
            return err.msg
        cursor.close()

        return redirect(url_for('facultyhome', id = name))

    except Exception as e:
        return e


@app.route('/deleteclass/<string:table>/<string:name>')
def deleteclass(table , name):
    try:
        query = f"DROP TABLE `MyDatabase`.`{table}`;"
        mydb = CONNECTION()
        cur = mydb.cursor()
        try:

            q= "DELETE FROM `MyDatabase`.`TeacherClasses` WHERE ClassName = %s" 
            cur.execute(q,(table,))
            cursor = mydb.cursor()
            cursor.execute(query)
            cursor.close()

            mydb.commit()

            cur.close()
        except mysql.connector.Error as err:
            print(err)
            print("Error Code:", err.errno)
            print("SQLSTATE", err.sqlstate)
            print("Message", err.msg)
            return err.msg
        return redirect(url_for('facultyhome',id = name))

    except Exception as e:
        return e

##################################################route for before request #################################################
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


################################################# route for logout ########################################################

@app.route('/logout')
def logout():
    session.pop('user',None)
    # session['user']= False
    return redirect(url_for('index'))


############################################################################################################################
if __name__== "__main__":
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')

    app.run(host='0.0.0.0',port=9999, debug=True , threaded =True)




