from flask import Flask, render_template
from flask import url_for
from flask import request
from flask_wtf import Form
from wtforms import SubmitField
from flask_wtf.file import FileField
import mysql.connector


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

@app.route('/', methods = ["GET","POST"])
def index():
    form = UploadForm()

    if request.method == "POST":

        if form.validate_on_submit():
            file_name = form.file.data
            populatedatabase(name=file_name.filename,data =file_name.read())
            print("FILE : {}" .format(file_name.filename))

    return render_template("home.html" , form = form)



class UploadForm(Form):
    file = FileField()
    submit = SubmitField("submit")

def populatedatabase(name,data):
    mydb = mysql.connector.connect(

        host="localhost",
        user="root",
        passwd="Abhishek@6204",
        database="database"
    )

    cursor = mydb.cursor()
    print(name)
    print(type(data))
    # cursor.execute("""CREATE TABLE IF NOT EXISTS my_table (name TEXT,data BLOB) """)
    q = "INSERT INTO my_table (name,data) VALUES (%s,%s) "
    val =(name,data)
    cursor.execute(q,val)
    mydb.commit()
    cursor.close()
    mydb.close()


if __name__== "__main__":
    app.run(debug=True)