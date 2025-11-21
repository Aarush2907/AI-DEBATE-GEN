import sqlite3

connection = sqlite3.connect('LoginData.db')

cursor = connection.cursor()

cmd1 = """ CREATE TABLE IF NOT EXISTS users (
    first_name varchar(50),
    last_name varchar(50),
    email varchar(50) primary key,
    password varchar(50) not null
)"""

cursor.execute(cmd1)

cmd2 = """ INSERT INTO users(first_name, last_name, email, password) VALUES('admin', 'admin', 'admin@admin', 'admin') """

try:
    cursor.execute(cmd2)
    connection.commit()
    print("User 'admin' inserted successfully.")
except sqlite3.IntegrityError:
    print("User 'admin' already exists.")

print("\nCurrent Users in Database:")
ans = cursor.execute(""" SELECT * FROM users """).fetchall()

for i in ans:
    print(i)

connection.close()