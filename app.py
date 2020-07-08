from flask import Flask, render_template, request, redirect, url_for, flash, Response,session,g
import mysql.connector
import os
import datetime
from openpyxl import Workbook
from base64 import b64encode
import detect
from openpyxl.writer.excel import save_virtual_workbook
import statistics

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



def mark_attendence(face , table):
    mydb = CONNECTION()
    cursor = mydb.cursor()
    today = datetime.date.today()
    print(today)
    # today = today.strftime("%b,%d,%Y")
    print(today)
    query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = %s; "
    cursor.execute(query,(today,))
    r = cursor.fetchall()
    if (len(r)==0):
        q= f"ALTER TABLE `database`.`{table}` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
        cursor.execute(q)

    mark = f"UPDATE `{table}` SET `{today}`= 1 WHERE name=%s"
    cursor.execute(mark,(face,))
    mydb.commit()
    cursor.close()
    mydb.close()




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

##################################################  Route to INDEX Page #####################################################

@app.route('/')
def index():
    session.pop('user',None)
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


########################################### Loads the face recogniser #######################################################

@app.route('/detect',methods = ['GET','POST'])
def detect():

    facelist = facerecognition()
    if len(facelist) > 0:

        face = statistics.mode(facelist)
        mark_attendence(str(face),'student')

        flash('Attendence Marked Successfully!!!')
    else:
        flash('Did not recognise you. Try Again. ')

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
        query = "SHOW TABLES"
        cursor.execute(query)
        res = cursor.fetchall()
        table_list = [x[0] for x in res]
        # table_list = table_list[1:]
        # print(table_list)

        return render_template('admin.html' , classes = table_list)
    return redirect(url_for('index'))


@app.route('/create',methods= ['GET','POST'])
def create_class():
    classname = request.form['classname']
    mydb = CONNECTION()
    cursor = mydb.cursor()
    query = f"CREATE TABLE `database`.`{classname}` (`Id` VARCHAR(45) NULL,`name` VARCHAR(45) NULL );"
    cursor.execute(query)
    mydb.commit()

    return redirect(url_for('admin'))


@app.route('/deleteclass/<string:table>')
def deleteclass(table):
    query = f"DROP TABLE `database`.`{table}`;"
    mydb = CONNECTION()
    cursor = mydb.cursor()
    cursor.execute(query)
    mydb.commit()
    cursor.close()
    return redirect(url_for('admin'))


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
    print(col)


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
    print (s)
    mydb = CONNECTION()
    cursor = mydb.cursor()
    query = f"SELECT Id,name,{s} FROM {table}"
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    wb = Workbook()
    ws = wb.active
    ws.append(cursor.column_names)

    for row in data:
        ws.append(row)

    workbook_name = f"{table}"
    wb.save(workbook_name + ".xlsx")

    flash('Your File Has Been Downloaded.')
    return redirect(url_for('database', table=table))


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
            if table == 'new_table' or table == 'StudentRecord' or table == 'TeacherRecord':
                continue
            q= f"SELECT 1 FROM {table} WHERE Id = %s"
            cur.execute(q,(id,))
            flag = cur.fetchall()
            if (len(flag)>= 1):
                classes.append(table)

        print(classes)

        return  render_template('student.html',classes = classes,id = id ,classlist = table_list)
    return redirect(url_for('index'))





@app.route('/student/<string:table>/<string:id>', methods = ['GET','POST'])
def studentpage(table,id):
    print(g.user)
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
            print("woooooooh oooohhhhhh")
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
    return render_template('index.html')


############################################################################################################################
if __name__== "__main__":
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')

    app.run(debug=True)




