import sqlite3

connection = sqlite3.connect('data.db')
create_table = "CREATE TABLE IF NOT EXISTS users (id INTEGER, username text, password text)"
insert_query = "INSERT INTO users VALUES (?,?,?)"

cursor = connection.cursor()
cursor.execute(create_table)
user = (1, 'joe', 'pass')
cursor.execute(insert_query, user)
users = [
    (2, 'deep2', 'pwd'),
    (3, 'deep3', 'pwd')
]
cursor.executemany(insert_query, users)

select_query = "SELECT * FROM users"
for row in cursor.execute(select_query):
    print(row)


create_table = "CREATE TABLE IF NOT EXISTS tasks (id INTEGER, subject text, status int)"
insert_query = "INSERT INTO tasks VALUES (?,?,?)"
tasks = [
    (1, "demo1", 1),
    (2, "demo2", 2)
]
cursor = connection.cursor()
cursor.execute(create_table)
cursor.executemany(insert_query, tasks)
select_query = "SELECT * FROM tasks"
for row in cursor.execute(select_query):
    print(row)


connection.commit()
connection.close()
