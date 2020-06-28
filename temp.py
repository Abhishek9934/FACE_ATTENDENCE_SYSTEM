import mysql.connector
import pickle
from datetime import date,timedelta
# mydb = mysql.connector.connect(
#
#     host = "localhost",
#     user = "root",
#     passwd = "Abhishek@6204",
#     database = "database",
#     use_pure="True"
#
# )
#
# cursor = mydb.cursor()
# today = date.today()
# yesterday = today - timedelta(days=1)
# tod= str(today)
# print(tod)
#
#
# q = "SELECT face FROM new_table"
#
# show = "SHOW COLUMNS FROM student LIKE 2020-06-28"
#
# # query = "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'student' AND COLUMN_NAME = %s; "
# q1 = f"ALTER TABLE `database`.`student` ADD COLUMN `{tod}` INT NULL DEFAULT 0;"
# q3 ="ALTER TABLE `database`.`student` ADD COLUMN `2020-07-80` INT NULL DEFAULT 0;"
#
# q = "ALTER TABLE `database`.`student` ADD COLUMN `"+ tod + "` INT NULL DEFAULT 0;"
# print (q)
# print(q3)
#
# cursor.execute(q1)
# # r = cursor.fetchall()
# # if (len(r)) == 0:
# #     cursor.execute(q, val)
#
#
#
#
#
#
#
# # insert = "INSERT INTO student (Id ,name) VALUES (%s,%s)"
# # val = (today,today,)
#
# delq= "DELETE FROM new_table"
#
# mark = "UPDATE student SET Jun28= 0  "
# v = ('abhishek',)
# # cursor.execute(insert , val)
#
#
# # rows = cursor.fetchall()
# mydb.commit()
# # print(cursor.rowcount, "recorded ")
#
# ## Get the results
# # for each in rows:
# #     ## The result is also in a tuple
# #     for face_stored_pickled_data in each:
# #         face_data = pickle.loads(face_stored_pickled_data)
# #         print(face_data)


def mark_attendence(face):
    mydb = mysql.connector.connect(

        host="localhost",
        user="root",
        passwd="Abhishek@6204",
        database="database",
        use_pure="True"
    )
    cursor = mydb.cursor()
    today = str(date.today())
    query = f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'student' AND COLUMN_NAME = %s; "
    cursor.execute(query,(today,) )
    r = cursor.fetchall()
    if (len(r) == 0):
        q = f"ALTER TABLE `database`.`student` ADD COLUMN `{today}` INT NULL DEFAULT 0;"
        cursor.execute(q)

    mark = f"UPDATE student SET `{today}` = 1 WHERE name= `{face}`;  "
    v= (face,)
    cursor.execute(mark)

    mydb.commit()
    cursor.close()
    mydb.close()


if __name__== "__main__":
    s='animesh'
    mark_attendence(s)