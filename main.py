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



from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC


embedder = MTCNN()
detector = FaceNet()


def CONNECTION():
    mydb =  mysql.connector.connect(

        host="localhost",
        user="admin",
        passwd="Abhishek@6204",
        database="MyDatabase",
        use_pure="True"
    )
    return mydb



# def drawBoxes(image , a,b,c,d):

#     cv2.rectangle(image, (a, b),(a+ c, b + d),(0,155,255)  , 2)
#     cv2.imwrite("ivan_drawn.jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))




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
    mydb = CONNECTION()
    # print(table)
    cursor = mydb.cursor()
    today = datetime.date.today()
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
########################################################################################################################
                                                                                                                       #                                                                                                                    #
    # try:                                                                                                             #
    #     lang = request.args.get('proglang', 0, type=str)                                                             #
    #     if lang.lower() == 'python':                                                                                 #
    #         return jsonify(result='You are wise')                                                                    #
    #     else:                                                                                                        #
    #         return jsonify(result='Try again.')                                                                      #
    # except Exception as e:                                                                                           #
    #     return str(e)                                                                                                #
########################################################################################################################


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

#-----------------------------ROUTES----------------------------####


##################################################  Route to INDEX Page #####################################################

@app.route('/')
def index():
    session.pop('user',None)
    mydb = CONNECTION()
    cursor = mydb.cursor()
    today = datetime.date.today()
    # print(today)
    # today = today.strftime("%b,%d,%Y")
    # print(today)
    cursor.execute("SHOW TABLES")
    res = cursor.fetchall()
    table_list = [x[0] for x in res]

    for table in table_list:
        if (table=='StudentRecord'  or table=='TeacherRecord' or table=='new_table' or table=='TeacherClasses'):
            continue
        query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = %s;"
        cursor.execute(query,(today,))
        r = cursor.fetchall()
        if (len(r)==0):
            q= f"ALTER TABLE `database`.`{table}` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
            cursor.execute(q)

    return render_template('index.html', classes = table_list)


########################################### Loads the face recogniser #######################################################

# @app.route('/detect/<string:id>',methods = ['GET','POST'])
# def detect(id):
#     # detection('CS204')
#     if request.method == 'POST':
#         c = request.form['classname']
#         print("value of c = ")
#         print(c)
#         arg1 = str(c)

#         # f.detection(detector, arg1)


        # os.system(f'python facenet.py  {arg1}')

#     return redirect(url_for('studenthome',id = id))

@app.route('/markattendance/<string:id>', methods = ['GET','POST'])
def markattendace(id):
    if(request.method == 'POST'):
        file = request.files['file']
        table = request.form['classname']

        imagede = Image.open(file)
        imagede = imagede.convert('RGB')

        pixels = np.asarray(imagede)
        # pixels = np.flip(pixels,axis = 0 )
        print(pixels)
        print("dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd")
        # img = cv2.imread(file.filename)
        # print(img)

        # img = cv2.imread(file.filename)
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

        detector = FaceNet()
        # frame = cv2.imread()
        # print(frame)
        detections = detector.extract(pixels)
        # print(detections)

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
        
        return redirect(url_for('facultyhome',id= id))

    return redirect(url_for('index'))




#################################################### ADMIN PANEL ROUTES ##################################################

@app.route('/login',methods= ['GET','POST'])
def login():

    if request.method == 'POST':
        session.pop('user',None)
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            flash('Invalid Credentials. Please try again.')
            # return alert('Invalid Credentials. Please try again.')
        else:
            session['user'] = request.form['username']
            return redirect(url_for('admin'))

    return redirect(url_for('index'))


@app.route('/admin')
def admin():
    if g.user == 'admin':
        mydb = CONNECTION()
        cursor = mydb.cursor()
        query = "SELECT * FROM StudentRecord"
        cursor.execute(query)
        res = cursor.fetchall()

        cur = mydb.cursor()
        cur.execute("SELECT * FROM TeacherRecord")
        res1 = cur.fetchall()
        
        # table_list = table_list[1:]
        # print(table_list)

        return render_template('admin.html' ,teachers = res1, students = res)
    return redirect(url_for('index'))


# @app.route('/create',methods= ['GET','POST'])
# def create_class():
#     classname = request.form['classname']
#     mydb = CONNECTION()
#     cursor = mydb.cursor()
#     query = f"CREATE TABLE `database`.`{classname}` (`Id` VARCHAR(45) NULL,`name` VARCHAR(45) NULL );"
#     cursor.execute(query)
#     mydb.commit()

#     return redirect(url_for('admin'))


# @app.route('/deleteclass/<string:table>')
# def deleteclass(table):
#     query = f"DROP TABLE `database`.`{table}`;"
#     mydb = CONNECTION()
#     cursor = mydb.cursor()
#     cursor.execute(query)
#     mydb.commit()
#     cursor.close()
#     return redirect(url_for('admin'))


@app.route('/classes/<string:table>')
def database(table):
    # print(g.user)
    # if g.user == 'admin':
        # session.pop('user',None)
    mydb = CONNECTION()
    cursor = mydb.cursor()

    cursor.execute(f"SELECT * FROM {table}")
    res= cursor.fetchall()
    col= cursor.column_names
    # col = col[5:]
    # print(col)


    return render_template('database.html',att= res ,col= col,l=len(col) , classname = table)

    # return redirect(url_for('index'))



@app.route('/insert/<string:table>' ,methods = ['POST'])
def insert(table):
    if request.method == 'POST':

        flash("Data Inserted Successfully")
        name = request.form['name']
        id = request.form['id']
        # email = request.form['email']
        # f = request.files['file']
        # dob = request.form['dob']
        # data = f.read()
        # print(type(data))
        mydb = CONNECTION()
        cursor = mydb.cursor()
        query = f"INSERT INTO {table} (Id,name) VALUES (%s,%s)"
        cursor.execute(query,(id,name,))
        mydb.commit()
        cursor.close()
        mydb.close()
        return redirect(url_for('database',table = table))



@app.route('/update/<string:table>', methods = ['POST','GET'])
def update(table):
    if request.method == 'POST':
        id = request.form['id']
        newid = request.form['newid']
        name = request.form['name']
        mydb = CONNECTION()
        cursor = mydb.cursor()

        query = f" UPDATE {table} SET Id =%s ,name=%s WHERE Id= %s "
        cursor.execute(query,(newid,name,id,))
        flash("Data Updated Successfully")
        mydb.commit()
        return redirect(url_for('database',table = table))

@app.route('/delete/<string:table>/<string:id>',methods = ['GET'])
def delete(table,id):
    flash("Record Has been Deleted Successful")
    mydb = CONNECTION()
    cursor = mydb.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = %s" ,(id,))
    mydb.commit()
    cursor.close()
    mydb.close()
    return redirect(url_for('database',table= table))


@app.route('/export/<string:table>')
def export(table):

    today = datetime.date.today()
    start_date = datetime.date(2020, 7, 6)

    delta = datetime.timedelta(days=1)
    s=''
    while start_date < today:
        s = s+'`'+str(start_date)+'`,'
        start_date += delta

    s=s+ '`'+str(today)+'`'
    # print (s)
    mydb = CONNECTION()
    cursor = mydb.cursor()
    query = f"SELECT Id,name,{s} FROM {table}"
    cursor.execute(query)
    data = cursor.fetchall()
    # print(data)
    wb = Workbook()
    ws = wb.active
    ws.append(cursor.column_names)

    for row in data:
        ws.append(row)

    workbook_name = f"{table}"
    wb.save(workbook_name + ".xlsx")

    flash('Your File Has Been Downloaded.')
    return redirect(url_for('database', table=table))


@app.route('/teacherlogin',methods = ['GET','POST'])
def teacherlogin():
    if request.method == 'POST':

        session.pop('user',None)
        name = request.form['name']
        password = request.form['password']
        mydb= CONNECTION()
        cursor= mydb.cursor()
        cursor.execute("SELECT password FROM TeacherRecord  WHERE TeacherName=%s",(name,))
        d= cursor.fetchone()
        # print('reached here')
        # print(birth)
        if (d!=None and d[0] == str(password)):
            session['user'] = request.form['name']
            return  redirect(url_for('facultyhome', id = name))
        else:
            flash('Invalid Credentials. Please try again.')
    return  redirect(url_for('index'))




############################################################# route for student panel #######################################

@app.route('/studentlogin', methods =['GET','POST'])
def studentlogin():
    if request.method == 'POST':

        session.pop('user',None)
        id = request.form['id']
        birth = request.form['dob']
        mydb= CONNECTION()
        cursor= mydb.cursor()
        cursor.execute("SELECT DOB FROM StudentRecord  WHERE Id=%s",(id,))
        d= cursor.fetchone()

        # print(birth)
        if (d!=None and d[0] == str(birth)):
            session['user'] = request.form['id']
            return  redirect(url_for('studenthome', id=id))
        else:
            flash('Invalid Credentials. Please try again.')
    return  redirect(url_for('index'))

@app.route('/student/<string:id>')
def studenthome(id):
    if g.user == str(id):
        mydb = CONNECTION()
        cursor = mydb.cursor()
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
            q= f"SELECT 1 FROM {table} WHERE Id =%s"
            cur.execute(q,(id,))
            flag = cur.fetchall()
            if (len(flag)>= 1):
                classes.append(table)

        # print(classes)

        return  render_template('student.html',classes = classes,id = id ,classlist = table_list)
    return redirect(url_for('index'))





@app.route('/student/<string:table>/<string:id>', methods = ['GET','POST'])
def studentpage(table,id):
    # print(g.user)
    if g.user == str(id):
        # session.pop('user',None)
        mydb= CONNECTION()
        cursor = mydb.cursor()
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
        query = f"SELECT * FROM {table} WHERE Id =%s"
        cur.execute(query,(id,))
        res = cur.fetchall()
        names = cur.column_names
        l =len(names)


        return render_template('home.html',names= names, data = data , l= l,image = image,att = res ,tab = table)
    return redirect(url_for('index'))


@app.route('/join/<string:id>',methods = ['GET','POST'])
def join(id):
    if request.method == 'POST':
        # flash("Data Inserted Successfully")
        table = request.form['classname']
        classcode = request.form['classcode']


        if classcode == table:
            # print("woooooooh oooohhhhhh")
            mydb = CONNECTION()
            cursor = mydb.cursor()
            cursor.execute(f"SELECT Name FROM StudentRecord WHERE Id = %s",(id,))
            res = cursor.fetchall()
            name = res[0][0]
            query = f"INSERT INTO {table} (Id,name) VALUES (%s,%s)"

            cursor.execute(query, (id, name,))
            mydb.commit()
            cursor.close()
            mydb.close()

    return redirect(url_for('studenthome',id = id))


@app.route('/register',methods = ['GET','POST'])
def register():

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
        query = f"INSERT INTO StudentRecord (Id,Name,Image,Email,DOB) VALUES (%s,%s,%s,%s,%s)"

        cursor.execute(query,(id,name,data,email,dob))
        mydb.commit()
        cursor.close()
        mydb.close()

    return redirect(url_for('index'))

# @app.route('/facereg/<string:table>')
# def facereg(table):

#     return re

@app.route('/registerclass/<string:table>' ,methods = ['GET','POST'])
def registerclass(table):

    if request.method == 'POST':
        file = request.files['file']
        # frame = file.read()
        # img = file.read()

        imagede = Image.open(file)
        imagede = imagede.convert('RGB')

        pixels = np.asarray(imagede)
        img = pixels
        # img = cv2.imread(file.filename)
        images = []

        detections = embedder.detect_faces(pixels)
        # print(detections[0])

        for detection in detections:

            bounding_box = detection['box']
            # drawBoxes(img ,int ( bounding_box[0]) ,int(bounding_box[1]), int(bounding_box[2]), int(bounding_box[3]))

            crop_image =  img[bounding_box[1]-10:bounding_box[1]+ bounding_box[3]+15,bounding_box[0]-10:bounding_box[0]+ bounding_box[2]+15]

            if(crop_image.any()):
                success, encoded_image = cv2.imencode('.jpg', crop_image)
                content2 = encoded_image.tobytes()
                image = b64encode(content2).decode("utf-8")

            
                images.append(image)
        # print("xiohifdiafieajfijifjeij")
        # print(images[1])
        return render_template('faceregister.html', images = images ,table = table)

    return redirect(url_for('index'))









@app.route('/registerstudent/<string:table>',methods= ['GET','POST'])
def registerstudent(table):
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']

        mydb = CONNECTION()
        cursor = mydb.cursor()
        query = f"INSERT INTO {table} (Id,name) VALUES (%s,%s)"

        cursor.execute(query, (id, name,))
        mydb.commit()
        cursor.close()
        mydb.close()



    return redirect(url_for('registerclass',table = table))


@app.route('/facultyreg',methods = ['GET','POST'])
def facultyreg():

    if request.method=='POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password1']
        password2 = request.form['password2']

        if(password == password2):
            # print(type(data))
            mydb = CONNECTION()
            cursor = mydb.cursor()
            query = f"INSERT INTO TeacherRecord (TeacherName,Email,password) VALUES (%s,%s,%s)"

            cursor.execute(query,(name,email,password))
            mydb.commit()
            cursor.close()
            mydb.close()
            flash("You have been registered successfully!!!")

        else:
            flash("Password do not match.")

    return redirect(url_for('index'))




@app.route('/faculty/<string:id>')
def facultyhome(id):
    if g.user == str(id):
        mydb = CONNECTION()
        cursor = mydb.cursor()
        query = "SELECT ClassName FROM TeacherClasses WHERE TeacherName = %s"
        cursor.execute(query , (id,))
        res = cursor.fetchall()
        table_list = [x[0] for x in res]

        # print(table_list)

        return  render_template('teacher.html',classes = table_list ,id = id)
    return redirect(url_for('index'))


@app.route('/createclass/<string:name>' ,methods= ['GET','POST'])
def classcreate(name):
    classname = request.form['classname']
    print(name)

    print(classname)
    mydb = CONNECTION()
    cur = mydb.cursor()
    q = f"INSERT INTO TeacherClasses (TeacherName,ClassName) VALUES (%s,%s)"
    cur.execute(q,(name, classname,))
    cur.close()
    cursor = mydb.cursor()

    query = f"CREATE TABLE `database`.`{classname}` (`Id` VARCHAR(45) NULL,`name` VARCHAR(45) NULL );"
    cursor.execute(query)
    mydb.commit()
    cursor.close()

    return redirect(url_for('facultyhome', id = name))



@app.route('/deleteclass/<string:table>/<string:name>')
def deleteclass(table , name):

    query = f"DROP TABLE `database`.`{table}`;"
    mydb = CONNECTION()
    cur = mydb.cursor()
    q= "DELETE FROM `database`.`TeacherClasses` WHERE ClassName = %s" 
    cur.execute(q,(table,))
    cursor = mydb.cursor()
    cursor.execute(query)
    cursor.close()

    mydb.commit()

    cur.close()
    return redirect(url_for('facultyhome',id = name))


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

    app.run(debug=True , threaded = False)





