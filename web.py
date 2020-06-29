from flask import Flask, render_template, request, redirect, url_for, flash, Response
import mysql.connector
import os
from multipleface import VideoCamera


def CONNECTION():
    mydb =  mysql.connector.connect(

        host="localhost",
        user="root",
        passwd="Abhishek@6204",
        database="database",
        use_pure="True"
    )
    return mydb
#
# def gen(camera):
#     while True:
#         frame = camera.get_frame()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

#-----------------------------ROUTES----------------------------####


# @app.route('/video_feed')
# def video_feed():
#     return Response(gen(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/')
def index():
  return render_template('index.html')

@app.route('/my-link')
def my_link():
  print ('I got clicked!')
  os.system('python detect.py')

  return redirect(url_for('index'))

@app.route('/student_data/<string:id>',methods = ['GET'])
def student_data():
    print("Coming Soon")

@app.route('/admin')
def database():
    mydb = CONNECTION()
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM student")
    data= cursor.fetchall()
    cursor.close()

    return render_template('database.html',students= data)


@app.route('/insert' ,methods = ['POST'])
def insert():
    if request.method == 'POST':

        flash("Data Inserted Successfully")
        name = request.form['name']
        id = request.form['id']
        face = request.form['face']
        mydb = CONNECTION()
        cursor = mydb.cursor()
        query = "INSERT INTO student (id,name,Image) VALUES (%s,%s,%s)"

        cursor.execute(query,(id,name, face,))
        mydb.commit()
        cursor.close()
        mydb.close()
        return redirect(url_for('database'))


@app.route('/delete/<string:id>',methods = ['GET'])
def delete(id):
    flash("Record Has been Deleted Successful")
    mydb = CONNECTION()
    cursor = mydb.cursor()
    cursor.execute("DELETE FROM student WHERE id = %s" ,(id,))
    mydb.commit()
    cursor.close()
    mydb.close()
    return redirect(url_for('database'))

@app.route('/update', methods = ['POST','GET'])
def update():
    if request.method == 'POST':
        name = request.form['name']
        id = request.form['id']
        face = request.form['face']
        mydb = CONNECTION()
        cur = mydb.cursor()
        cur.execute(""" UPDATE students SET id=%s, name=%s, face=%s WHERE id= %s """, (id,name,face,id,))
        flash("Data Updated Successfully")
        mydb.commit()
        return redirect(url_for('database'))

if __name__== "__main__":
    app.run(debug=True)