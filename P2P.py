# -*- coding: utf-8 -*-
## This is a TCP based p2p file share Python application
# for Coure Networking: Principles, Protocols and Architectures
# to bridge netwoking theory to be practical experience

# socket module for transport layer communication between different host
#!/usr/bin/python
import socket
# threading module to manage muti-task concurrently run within a program
import threading
# os library for os related operation,like folder,files...
import os
import ipaddress
import time

# Configure your peer IP address in the list,then it can support auto discovery
Peer_ip_List ={'10.0.0.209'}

# Setting HOST ip addr for TCP socket to listen,0.0.0.0 can listen all IP address
HOST = '0.0.0.0'
# setting TCP port as 50000 which normal not used by common application
PORT = 50000

FILE_TRANS_BUFFER_SIZE = 1024*1024*3 #3MB
# Send and received files put in this folder
SHARE_FOLDER = 'P2P_Share'
# Create folder if not exist
os.makedirs(SHARE_FOLDER, exist_ok=True)

# verify input ip is valid or not
def is_valid_ip(address):
    try:
        ipaddress.IPv4Address(address)
        return True
    except ipaddress.AddressValueError:
        return False


def client_reponse(client_socket, address):
    print("\n")
    print(f"Accepted TCP connection from {address}")

    # Receive data from the client
    received_data = client_socket.recv(FILE_TRANS_BUFFER_SIZE).decode()

    # handle option 3 get peer file list
    # check if it is just to get file list
    if received_data == "ONLINE_GET_PEER_FILE_LIST":
      files_share_str = ''.join([f'{elem}{"":3}' for elem in os.listdir(SHARE_FOLDER)])
      client_socket.send(files_share_str.encode())
      client_socket.close()
      return

    # handle option 2 input peer address filename
    # Receive the filename from the client
    filename =  received_data
    file_path = os.path.join(SHARE_FOLDER, filename)
    if os.path.exists(file_path):
        file_exist_flag ='FILE_EXISTS'
        client_socket.send(file_exist_flag.encode())

        # Send the file to the client
        with open(file_path, 'rb') as file:
            read_data_size = 0
            while True:
                data = file.read(FILE_TRANS_BUFFER_SIZE)
                read_data_size_temp = len(data)
                read_data_size = read_data_size + read_data_size_temp
                if not data:
                    # if all data sentout,then send a FILE_SEND_FINISH tell client
                    client_socket.sendall(b'FILE_SEND_FINSHZI!')
                    file.close()
                    read_data_size_temp = 0
                    read_data_size = 0
                    break
                client_socket.sendall(data)
                # Calculate total sending file size
                print("File sending on going...Total",(read_data_size/(1024*1024))," MB sent!")

            read_data_size_temp = 0
            read_data_size = 0
        print(f"File successfully sent to {address}")
        print("\nPress any key to continue...")

    else:
        file_exist_flag = 'FILE_NOT_EXISTS'
        client_socket.send(file_exist_flag.encode())
        print(f"Request Error:The file {filename} does not exist at {SHARE_FOLDER}.")
        print("Press any key to continue...")

    client_socket.close()

# for server thread listen to client conection request,if there is then create
#  client reponse thread
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    # enable server to be ready to accept TCP connection，3 is maximum queue for connection
    server_socket.listen(3)
    print(f"\nServer start listening on {HOST}:{PORT}")

    while True:
        # Accept a connection from a client
        client_socket, address = server_socket.accept()
        # creat a thread for handle client connection,input argument is client_reponse func
        client_handler = threading.Thread(target=client_reponse, args=(client_socket, address))
        client_handler.start()

def send_file(peer_ip, filename):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((peer_ip, PORT))

        # Send the filename to the peer
        client_socket.send(filename.encode())

        # Check the file exisit or not
        file_exist_flag = client_socket.recv(FILE_TRANS_BUFFER_SIZE).decode()
        if file_exist_flag == 'FILE_EXISTS':
              # Receive and save the file to share folder
              file_recv_data = b''
              with open(os.path.join(SHARE_FOLDER, filename), 'wb') as file:
                  received_size = 0
                  while True:
                      file_recv_data = client_socket.recv(FILE_TRANS_BUFFER_SIZE)

                      # check received data size
                      received_size_temp = len(file_recv_data)
                      received_size = received_size + received_size_temp

                      if file_recv_data.find(b'FILE_SEND_FINSHZI!') >= 0:
                          file.write(file_recv_data)
                          print("File receiving on going...Total",(received_size/(1024*1024))," MB received.")
                          print("File_Receive_Finish!")
                          received_size = 0
                          received_size_temp = 0
                          break
                      file.write(file_recv_data)
                      # Calculate total received size
                      print("File receiving on going...Total",(received_size/(1024*1024))," MB received.")

                  received_size = 0
                  received_size_temp = 0
              file.close()
              print(f"File successfully received from {peer_ip}")
        else:
          print(f"\nThe file {filename} does not exist at {SHARE_FOLDER}")
        client_socket.close()

# find on line peer and request get file list
def find_peer(peer_ip, is_online_flag):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      client_socket.connect((peer_ip, PORT))
      # Send the to the peer
      client_socket.send(is_online_flag.encode())

      # Check the file exisit or not
      folder_info = client_socket.recv(FILE_TRANS_BUFFER_SIZE).decode()
      return folder_info

    except socket.error as e:
          # Handle the connection error here
          return "NOT_online"

    client_socket.close()


if __name__ == "__main__":
    # Get the local host name
    hostname = socket.gethostname()
    # Get the IP address associated with the local host
    local_ip_address = socket.gethostbyname(hostname)
    print(f"Local Hostname: {hostname}")
    print(f"Local IP: {local_ip_address}")

    # Start the server in a seperate thread，input argument is start_server func
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    time.sleep(2)
    print("Files need to be put in P2P_Share folder")

    restart_flag = True
    while restart_flag:
      while True:
            print("\n1. GET Local File Ready To Share")
            print("2. Discovery Online Peer And Get Share List")
            print("3. Download File From Peer")
            print("**For Option2 Peer IP addr need added in the Python Code Line16 Peer_ip_List**")

            option = input("\nInput Option Num: ")
            if option == '1':
                print("***Files in This Host Ready To Share:")
                files_share_str = ''.join([f'{elem}{"":3}' for elem in os.listdir(SHARE_FOLDER)])
                print(files_share_str)


            elif option == '2':
              peer_count =0
              for peer_ip in Peer_ip_List:
                  if peer_ip != local_ip_address:
                    is_online_flag ="ONLINE_GET_PEER_FILE_LIST"

                    verify_peer = find_peer(peer_ip, is_online_flag)
                    if verify_peer != "NOT_online":
                      print("\n")
                      print(f"***Peer {peer_ip} Online,Its Share List:")
                      print(verify_peer)
                      print("\n")
                      peer_count = peer_count + 1

              if peer_count == 0:
                print("***0 Peer Online,Please make sure you Peer IP registered")
              else:
                print("***",peer_count,"Peers Online,Chose Option 3 To Download!")

            elif option == '3':
                peer_ip = input("Input Peer IP: ")
                if is_valid_ip(peer_ip):
                  if peer_ip == local_ip_address:
                    print(f"{peer_ip} is same as Local host IP.")
                    break
                  if peer_ip != local_ip_address:
                    is_online_flag ="ONLINE_GET_PEER_FILE_LIST"
                    verify_peer = find_peer(peer_ip, is_online_flag)
                    if verify_peer != "NOT_online":
                      filename = input("Input File Name With Extension: ")
                      send_file(peer_ip, filename)
                    else:
                      print("\nPeer Not online!")
                    break
                else:
                    print(f"{peer_ip} is not a valid IP address.")
                    break

            elif option == '3':
                peer_ip = input("Input Peer IP: ")
                if is_valid_ip(peer_ip):
                  if peer_ip == local_ip_address:
                    print(f"{peer_ip} is same as Local host IP.")
                    break
                  else:
                    filename = input("Input File Name With Extension: ")
                    send_file(peer_ip, filename)
                    break
                else:
                    print(f"{peer_ip} is not a valid IP address.")
                    break

            else:
                print("Invalid input. Please try again.")
                break