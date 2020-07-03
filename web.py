from flask import Flask, render_template, request, redirect, url_for, flash, Response,session,g
import mysql.connector
import os
import datetime
from openpyxl import Workbook


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
    mydb = CONNECTION()
    cursor = mydb.cursor()
    today = datetime.date.today()
    print(today)
    # today = today.strftime("%b,%d,%Y")
    print(today)
    query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'student' AND COLUMN_NAME = %s; "
    cursor.execute(query,(today,))
    r = cursor.fetchall()
    if (len(r)==0):
        q= f"ALTER TABLE `database`.`student` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
        cursor.execute(q)


    return render_template('index.html')

@app.route('/export')
def export():

    today = datetime.date.today()
    start_date = datetime.date(2020, 6, 30)

    delta = datetime.timedelta(days=1)
    s=''
    while start_date < today:
        s = s+'`'+str(start_date)+'`,'
        start_date += delta

    s=s+ '`'+str(today)+'`'
    print (s)
    mydb = CONNECTION()
    cursor = mydb.cursor()
    query = f"SELECT Id,name,{s} FROM student"
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    wb = Workbook()
    ws = wb.active
    ws.append(cursor.column_names)

    for row in data:
        ws.append(row)

    workbook_name = "AttendenceRecord"
    wb.save(workbook_name + ".xlsx")
    flash('Your File Has Been Downloaded.')
    return redirect(url_for('database'))



@app.route('/detect')
def detect():
    print ('I got clicked!')
    os.system('python detect.py')
    flash('Attendence Marked Successfully!!!')

    return redirect(url_for('index'))

@app.route('/student_data/<string:id>',methods = ['GET'])
def student_data():
    print("Coming Soon")

@app.route('/admin')
def database():
    if g.user:

        mydb = CONNECTION()
        cursor = mydb.cursor()
        today = datetime.date.today()
        today = today.strftime("%b,%d,%Y")

        cursor.execute(f"SELECT Id,name,Email,DOB,Image FROM student")
        data= cursor.fetchall()
        cursor.close()

        today = datetime.date.today()
        start_date = datetime.date(2020, 6, 30)

        delta = datetime.timedelta(days=1)
        s=''
        while start_date < today:
            s = s+'`'+str(start_date)+'`,'
            start_date += delta

        s=s+ '`'+str(today)+'`'
        print (s)
        cursor = mydb.cursor()
        query = f"SELECT Id,name,{s} FROM student"
        cursor.execute(query)
        atten_data = cursor.fetchall()
        col= cursor.column_names
        return render_template('database.html',students= data ,attendence = atten_data,col= col,l=len(col))
    return redirect(url_for('index'))

@app.route('/insert' ,methods = ['POST'])
def insert():
    if request.method == 'POST':

        flash("Data Inserted Successfully")
        name = request.form['name']
        dob = request.form['dob']
        id = request.form['id']
        email = request.form['email']
        f = request.files['file']
        data = f.read()
        # print(type(data))
        mydb = CONNECTION()
        cursor = mydb.cursor()
        query = "INSERT INTO student (id,name,Image,DOB,Email) VALUES (%s,%s,%s,%s,%s)"

        cursor.execute(query,(id,name,data,dob,email,))
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

@app.route('/student/<string:id>', methods = ['GET','POST'])
def studentpage(id):
    if g.user:
        mydb= CONNECTION()
        cursor = mydb.cursor()
        # query = "SELECT "
        cursor.execute()

        return render_template('home.html')
    return redirect(url_for('index'))







@app.route('/update', methods = ['POST','GET'])
def update():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        dob = request.form['dob']
        email = request.form['email']
        mydb = CONNECTION()
        cur = mydb.cursor()
        f = request.files['file']
        data = f.read()
        cur.execute(""" UPDATE student SET Id =%s ,name=%s, Email= %s, Image= %s,DOB= %s WHERE id= %s """, (id,name,email,data,dob,id,))
        flash("Data Updated Successfully")
        mydb.commit()
        return redirect(url_for('database'))


@app.route('/login',methods= ['GET','POST'])
def login():

    if request.method == 'POST':
        session.pop('user',None)
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            flash('Invalid Credentials. Please try again.')
            # return alert('Invalid Credentials. Please try again.')
        else:
            # session['user'] = request.form['username']
            session['user']= True
            return redirect(url_for('database'))

    return redirect(url_for('index'))


@app.route('/studentlogin', methods =['GET','POST'])
def studentlogin():
    if request.method == 'POST':

        session.pop('user',None)
        id = request.form['id']
        birth = request.form['dob']
        mydb= CONNECTION()
        cursor= mydb.cursor()
        cursor.execute("SELECT DOB FROM student WHERE Id=%s",(id,))
        d= cursor.fetchone()

        # print(birth)
        if (d!=None and d[0] == str(birth)):
            session['user']= True
            return  redirect(url_for('studentpage', id=id))
        else:
            flash('Invalid Credentials. Please try again.')
    return  redirect(url_for('index'))

@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


@app.route('/logout')
def logout():
    # session.pop('user',None)
    session['user']= False
    return render_template('index.html')

if __name__== "__main__":
    app.run(debug=True)