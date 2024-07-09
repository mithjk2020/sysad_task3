import threading
import pymysql as sqltor
import socket
mycon = sqltor.connect(
        host = 'localhost',
        database = 'QUIZ',
        user = 'root',
        password = 'root1234'
    )
if not mycon.open:
    print("Error")
cursor =  mycon.cursor()

host = '127.0.0.1'
port = 8383
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
clients = []
aliases = []
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
mycon.commit()

def broadcast(message):
    for client in clients:
        client.send(message)

# Function to handle clients'connections
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
        cursor.execute("SELECT creator FROM QUESTIONS WHERE id = %s;", (attempted + 1,))  # Ensure attempted + 1 is a tuple
        result = cursor.fetchone()
        if result is None:
            client.send("No more questions available.".encode('utf-8'))
            return
        owner = result[0]
        if owner != alias:
            break
        attempted += 1
    cursor.execute("SELECT question FROM QUESTIONS WHERE id = %s;", (attempted + 1,))  # Ensure attempted + 1 is a tuple
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
        client.send(f'Uh oh wrong answer, the correct answer was {real}!'.encode('utf-8'))
    cursor.execute("UPDATE LEADERBOARD SET last_attempted = %s where name = %s;", (attempted + 1, alias))
    mycon.commit()
  

# Main function to receive the clients connection

def receive():
    while True:
        print('Server is running and listening ...')
        client, address = server.accept()
        print(f'connection is established with {str(address)}')
        client.send('alias?'.encode('utf-8'))
        alias = client.recv(1024)
        cursor.execute("INSERT IGNORE INTO LEADERBOARD (name) VALUES (%s)", (alias,))
        mycon.commit()
        aliases.append(alias)
        clients.append(client)
        print(f'The alias of this client is {alias}'.encode('utf-8'))
        broadcast(f'{alias} has connected to the quiz room'.encode('utf-8'))
        client.send('you are now connected!'.encode('utf-8'))
        while True:
            client.send('What action do you want to perform?\n Enter 1 for asking a question\n Enter 2 for answering a question\n Enter 3 to view the leaderboard\n Enter 4 to exit\n Enter an option:'.encode('utf-8'))
            var = int(client.recv(1024).decode('utf-8'))
            if var == 1:
                ask_q(client, alias)
            elif var == 2:
                ans_q(client, alias)
            elif var == 3:
                cursor.execute("SELECT * FROM LEADERBOARD ORDER BY  score DESC;")
                result = cursor.fetchall()
                for row in result:
                    client.send(f"{row}\n".encode('utf-8'))
            elif var == 4:
                break
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == "__main__":
    receive()
