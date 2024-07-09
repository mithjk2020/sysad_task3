import threading
import socket

alias = input('Choose an alias >>> ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 8383))

def client_receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith('Enter'):
                print(message)
                response = input('')
                client.send(response.encode('utf-8'))
            else:
                print(message)
        except:
            print('Error!')
            client.close()
            break

def client_send():
    while True:
        message = input("")
        client.send(message.encode('utf-8'))

receive_thread = threading.Thread(target=client_receive)
receive_thread.start()

send_thread = threading.Thread(target=client_send)
send_thread.start()
