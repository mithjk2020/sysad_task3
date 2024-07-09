import threading
import pymysql as sqltor
import socket
import hashlib

# Connect to MySQL database
mycon = sqltor.connect(
    host='localhost',
    database='QUIZ',
    user='root',
    password='root1234'
)
if not mycon.open:
    print("Error")
cursor = mycon.cursor()

# Socket setup
host = '127.0.0.1'
port = 8383
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
clients = []
aliases = []

# Database setup
cursor.execute("CREATE DATABASE IF NOT EXISTS QUIZ")
cursor.execute("USE QUIZ")
cursor.execute(""" CREATE TABLE IF NOT EXISTS LEADERBOARD (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50),
        last_attempted INT DEFAULT 0,
        score INT DEFAULT 0)""")
cursor.execute(""" CREATE TABLE IF NOT EXISTS QUESTIONS (
        id INT AUTO_INCREMENT PRIMARY KEY,
        creator VARCHAR(50),
        question VARCHAR(350),
        answer INT NOT NULL)""")
cursor.execute(""" CREATE TABLE IF NOT EXISTS details (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(100))""")
mycon.commit()

def broadcast(message):
    for client in clients:
        client.send(message)

# Function to handle clients' connections
def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            broadcast(message)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            alias = aliases[index]
            broadcast(f'{alias} has left the quiz room!'.encode('utf-8'))
            aliases.remove(alias)
            break

def ask_q(client, alias):
    client.send("Enter the question:".encode('utf-8'))
    quest = client.recv(1024).decode('utf-8')
    client.send("Enter option 1:".encode('utf-8'))
    opt1 = client.recv(1024).decode('utf-8')
    client.send("Enter option 2:".encode('utf-8'))
    opt2 = client.recv(1024).decode('utf-8')
    client.send("Enter option 3:".encode('utf-8'))
    opt3 = client.recv(1024).decode('utf-8')
    client.send("Enter option 4:".encode('utf-8'))
    opt4 = client.recv(1024).decode('utf-8')
    client.send("Enter the correct option number:".encode('utf-8'))
    crct = client.recv(1024).decode('utf-8')
    final_quest = f"{quest}\n1. {opt1}\n2. {opt2}\n3. {opt3}\n4. {opt4}"
    cursor.execute('INSERT INTO QUESTIONS(creator, question, answer) VALUES (%s, %s, %s);', (alias, final_quest, crct))
    mycon.commit()

def ans_q(client, alias):
    cursor.execute("SELECT last_attempted FROM LEADERBOARD WHERE name = %s;", (alias,))
    attempted = int(cursor.fetchone()[0])
    while True:
        cursor.execute("SELECT creator FROM QUESTIONS WHERE id = %s;", (attempted + 1,))
        result = cursor.fetchone()
        if result is None:
            client.send("No more questions available.".encode('utf-8'))
            return
        owner = result[0]
        if owner != alias:
            break
        attempted += 1
    cursor.execute("SELECT question FROM QUESTIONS WHERE id = %s;", (attempted + 1,))
    quest = cursor.fetchone()[0]
    client.send(quest.encode('utf-8'))
    cursor.execute("SELECT answer FROM QUESTIONS WHERE id = %s;", (attempted + 1,))
    real = cursor.fetchone()[0]
    client.send("Enter the correct option number:".encode('utf-8'))
    crct = client.recv(1024).decode('utf-8')
    if int(real) == int(crct):
        client.send("Correct answer!! You gained one point.".encode('utf-8'))
        cursor.execute("UPDATE LEADERBOARD SET score = score + 1 WHERE name = %s;", (alias,))
    else:
        client.send(f'Wrong answer, the correct answer was {real}!'.encode('utf-8'))
    cursor.execute("UPDATE LEADERBOARD SET last_attempted = %s where name = %s;", (attempted + 1, alias))
    mycon.commit()

def register_user(client):
    while True:
        client.send('Enter new username:'.encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        client.send('Enter new password:'.encode('utf-8'))
        password = client.recv(1024).decode('utf-8')
        
        # Hash password using SHA-256
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        try:
            cursor.execute('INSERT INTO details (username, password) VALUES (%s, %s)', (username, hashed_password))
            mycon.commit()
            client.send('Registration successful!'.encode('utf-8'))
            return username
        except sqltor.IntegrityError:
            client.send('Username already exists. Try again.'.encode('utf-8'))

def authenticate_user(client):
    while True:
        client.send('Enter username:'.encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        client.send('Enter password:'.encode('utf-8'))
        password = client.recv(1024).decode('utf-8')
        
        # Hash password using SHA-256 for comparison
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        cursor.execute('SELECT password FROM details WHERE username = %s', (username,))
        result = cursor.fetchone()
        if result and hashed_password == result[0]:
            client.send('Login successful!'.encode('utf-8'))
            return username
        else:
            client.send('Invalid username or password. Try again.'.encode('utf-8'))

# Main function to receive the clients connection
def receive():
    while True:
        print('Server is running and listening ...')
        client, address = server.accept()
        print(f'Connection is established with {str(address)}')
        
        client.send('1. Register\n2. Login\nChoose an option:'.encode('utf-8'))
        option = client.recv(1024).decode('utf-8')
        
        alias = None
        if option == '1':
            alias = register_user(client)
        elif option == '2':
            while not alias:
                alias = authenticate_user(client)
        
        if alias:
            cursor.execute("INSERT IGNORE INTO LEADERBOARD (name) VALUES (%s)", (alias,))
            mycon.commit()
            aliases.append(alias)
            clients.append(client)
            print(f'The alias of this client is {alias}')
            broadcast(f'{alias} has connected to the quiz room'.encode('utf-8'))
            client.send('You are now connected!'.encode('utf-8'))
            
            while True:
                client.send('What action do you want to perform?\nEnter 1 for asking a question\nEnter 2 for answering a question\nEnter 3 to view the leaderboard\nEnter 4 to exit\nEnter an option:'.encode('utf-8'))
                var = int(client.recv(1024).decode('utf-8'))
                if var == 1:
                    ask_q(client, alias)
                elif var == 2:
                    ans_q(client, alias)
                elif var == 3:
                    cursor.execute("SELECT * FROM LEADERBOARD ORDER BY score DESC;")
                    result = cursor.fetchall()
                    for row in result:
                        client.send(f"{row}\n".encode('utf-8'))
                elif var == 4:
                    break
            
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()

if __name__ == "__main__":
    receive()
