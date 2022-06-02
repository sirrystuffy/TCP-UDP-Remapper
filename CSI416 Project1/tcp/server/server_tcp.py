import collections
import socket
import os
import sys
from time import sleep

# Connection INFO
HOST = ""
PORT = int(sys.argv[1]) 

BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"
alphabet = "abcdefghijklmnopqrstuvwxyz"

def main() :
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))  
        sock.listen()  
        conn, addy = sock.accept()
        with conn: 
            print(f"Connected by: {addy}")
            #Keep running until connection is severed by client
            while True : 
                # Receives all the data, delimits it by "SEPARATOR" and puts it in an array
                initial_data = conn.recv(BUFFER_SIZE).decode()
                data_arr = initial_data.split(SEPARATOR)
                state = data_arr[0]

                match (state) : 

                    case 'put' :
                        file = data_arr[1]
                        with open(file, "wb") as writer:
                            while True:
                                chunk = conn.recv(BUFFER_SIZE)
                                if chunk == b'Finished put': #'Finished put' is the final chunk telling us that no more chunks will be sent
                                    break
                                writer.write(chunk) 
                        print("File Downloaded.")

                    case 'get' :
                        path = data_arr[1]
                        # Check if the file exists
                        if not os.path.exists(path) :
                            raise Exception("Path does not exist.")
                        print("file exists")

                        with open(path, 'rb') as reader : 
                            while True :
                                chunk = reader.read(BUFFER_SIZE)
                                if not chunk : 
                                    break 
                                conn.sendall(chunk)
                            sleep(0.1)

                            #Let the client know that you are done sending
                            conn.sendall("Finished get".encode())
                        print("File Uploaded.")
                    case 'remap' :
                        offset = data_arr[1] 
                        path = data_arr[2]
                        # Splitting the file by '.' to create a new file 
                        # For example, "test.txt" --> [test], [txt] --> "test_remap.txt"
                        pathList = path.split('.')
                        new_path = pathList[0] + "_remap." + pathList[1]
                        
                        # Check if the file exists
                        if not os.path.exists(path) :
                            raise Exception("Path does not exist.")
                        print("file exists")

                        #Do the remapping
                        remappedList = remapList(offset)
                        new_alphabet = "".join(remappedList).encode() #Convert remapped list to a string

                        # The file to be remapped has previously been remapped, since its remap counterpart (xxxx_remap.txt) exists 
                        # Thus, we must overwrite the last remap with this new remap ! 
                        if os.path.exists(new_path) : 
                            with open(new_path, "wb") as writer : # Another solution would be to delete the file using os.remove(new_path) 
                                remapFile(path, new_alphabet, new_path)
                        else : 
                            # The file to be remapped is a remap virgin, since its remap counterpart does not exist
                            remapFile(path, new_alphabet, new_path)

                        print("remapping complete")
                        # Let the server know where to find the remapped file.
                        conn.sendall(f"File {os.path.basename(path)} remapped. Output file is {new_path}".encode())

                    case 'quit' :
                        print("Client has ended connection . . .")
                        exit(1)

# Make an array of strings, rotate the array, and return that array
def remapList(amount) : 
    lettersList = list(alphabet)
    tempVar = collections.deque(lettersList)
    # By rotating elements to the left, the letters that are ahead replace the positions of the original letters to allow accurate mapping
    # Original => Shifted to the left 2 times
    # [a, b, c, d, e, f] => [c, d, e, f, a, b] 
    tempVar.rotate(-int(amount))
    finalList = list(tempVar)
    return finalList

# Read chunks from the desired file, remap each byte/character, and write it to a new file
def remapFile(path, new_alphabet, new_path) :
    with open(path, "rb") as reader : 
        while True : 
            chunk = reader.read(BUFFER_SIZE)
            if not chunk : 
                break
            # Make a translation table with the alphabet and the remapped alphabet
            translation = chunk.maketrans(alphabet.encode(), new_alphabet)
            # Store the translated chunk into new variable
            transChunk = chunk.translate(translation)   
            with open(new_path, "a+b") as user :
                user.write(transChunk)

# auto closes so no need for sock.close()

if __name__ == '__main__' :
    main()