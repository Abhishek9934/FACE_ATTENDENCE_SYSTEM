import mysql.connector
mydb = mysql.connector.connect(

    host = "localhost",
    user = "root",
    passwd = "Abhishek@6204",
    database = "database"
)

cursor = mydb.cursor()
query = "INSERT INTO new_table(id,name,entryno,face) VALUES (5,'barackkk' , '20102ja' ,LOAD_FILE('./Known/obama.jpg'))"
q = "SELECT * FROM my_table"
delq= "DELETE FROM new_table WHERE name = 'barack'"
# cursor.execute(query)
cursor.execute(q)

# mydb.commit()
#
# print(cursor.rowcount, "recorded.")
res = cursor.fetchall()
for x in res:
    print(x)