# CSI 416 Project 1, The remapper : socket programming and reliable data transfer
# ----------------------------------------------------------------------------------------
# Remapping functionality: The application will allow a user to upload a text file of
# arbitrary size to the server. The file will then be loaded, read, and each character will be
# remapped. The redacted text will be stored in a new file. The remapper function will
# replace each character in the text file with a corresponding character that is N positions
# ahead in the English alphabet. For example, if the target string is “clock”, and N=5 the
# remapped string will be “hqthp”. Once the server is done remapping, it will issue a
# message to the user indicating the output filename. The server will then allow the client
# to download the output file. We will implement a limited remapping function that will
# only work on the lower-case letters of the English alphabet (no uppercase letters,
# numbers or special characters will have to be remapped).

# Supported commands: Your program should allow a user to upload and download text
# files, specify the remapping offset N, and quit the program. To this end, you will
# implement the following commands that the client can send to the server:
# - Copy a file from the client to the server (put), which takes as an input argument the
# full path to a file <file> on the client. Example execution:
# put <file>
# - Copy a file from a server to a client (get), which also takes as an argument the full
# path to a file <file> on the server. Example execution:
# get <file>
# - Remap command that will allow the user to specify a remapping offset N and a
# target file in which to perform the remapping. Example execution:
# remap <int> <file>
# - Quit the program per user request
# quit

import os
import sys
from time import sleep
import socket

# Connection INFO
HOST = sys.argv[1]  
PORT = int(sys.argv[2]) 

BUFFER_SIZE = 4096 
SEPARATOR = "<SEPARATOR>"

def main():
    # Utilizes the same connection after every command
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        while True:
            response = input("Enter Command : ")
            response_arr = response.split(' ')  # print(arr[0])
            keyword = response_arr[0]

            match(keyword):

                case 'put':
                    if response_arr[1]:
                        put = "put"
                        path = response_arr[1]
                        sock.sendall(f"{put}{SEPARATOR}{path}".encode()) #Send state and path together; delimit at server side
                        
                        if not os.path.exists(path) :
                            raise Exception("Path does not exist.")
                        print("Awaiting server response")

                        #Open and read the file, sending each chunk to server
                        with open(path, "rb") as reader:
                            while True:
                                chunk = reader.read(BUFFER_SIZE)
                                if not chunk: #Chunk is empty
                                    break
                                sock.sendall(chunk)
                            #Send this to server when all is read; 
                            sleep(0.1) # Without sleeping, the messages (chunk + ending message) will couple and leave both programs stalled. 
                            sock.sendall("Finished put".encode())
                    else:
                        raise Exception("Please include path of the file")
                    print('Server Response : File Uploaded.')

                case 'get':
                    if response_arr[1]:
                        # Let the server know what file you want to get
                        get = "get"
                        path = response_arr[1]
                        sock.sendall(f"{get}{SEPARATOR}{path}".encode())

                        # Get the chunks and write those chunks to client's file
                        with open(path, "wb") as writer:
                            while True:
                                chunk = sock.recv(BUFFER_SIZE)
                                # When the server has sent all bytes of the file, it will send one last message ("Finished get") 
                                # so that the client can exit the loop and get to the next command.
                                # If this is not done, the socket will keep on waiting for more bytes to be received endlessly,
                                # thus halting the program. 
                                if chunk == b'Finished get':
                                    break
                                writer.write(chunk) 
                        print(f"File {path} downloaded. ")
                    else:
                        raise Exception("Please include path of the file")

                case 'remap':
                    if response_arr[1] and response_arr[2]: 
                        remap = "remap"
                        offset = response_arr[1]
                        file = response_arr[2]
                        sock.sendall(f"{remap}{SEPARATOR}{offset}{SEPARATOR}{file}".encode())

                        # Receive server response detailing the path to the remapped file
                        response = sock.recv(BUFFER_SIZE)
                        print(response.decode())
                    else :
                        raise Exception("Please include the offset and target file") 

                case 'quit':
                    quit = "quit"
                    sock.sendall(f"{quit}".encode())

                    print("Exiting Program !")
                    exit(1)
                case _ : #Default case
                    raise Exception("Command undefined, please try again")


# This is so that main is called when file is run
if __name__ == '__main__':
    main()
