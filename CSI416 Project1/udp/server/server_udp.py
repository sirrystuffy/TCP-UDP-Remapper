import collections
import socket
import os
import sys

# Connection INFO
HOST = ""  # Any host can access
PORT = int(sys.argv[1]) #6969

BUFFER_SIZE = 1000
SEPARATOR = "<SEPARATOR>"
alphabet = "abcdefghijklmnopqrstuvwxyz"


def main():
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((HOST, PORT))
            # Receives all the premature data, delimits it by "SEPARATOR" and puts it in an array
            initial_data, addr = sock.recvfrom(BUFFER_SIZE)
            print(f"Connected to : {addr}")
            initial_data = initial_data.decode()
            data_arr = initial_data.split(SEPARATOR)
            state = data_arr[0]

            match (state):

                case 'put':
                    file = data_arr[1]

                    #This should apply to subsequent sock.recv 
                    sock.settimeout(1.0)

                    # If no data arrives at the receiver within one second from the reception of a LEN message, the receiver program should terminate
                    try : 
                        expectedSize, addr = sock.recvfrom(BUFFER_SIZE)
                    except TimeoutError:
                        print("Did not receive data. Terminating.")
                        exit(1)

                    # The expectedSize is a string, "LEN:{bytes}", and I only care about the bytes, so I store it in a new variable. 
                    size_arr = expectedSize.decode().split(":")
                    sizeOfFile = int(size_arr[1])
                    received = 0

                    # receive and write chunks to the file
                    with open(file, "wb") as writer:
                        while True:
                            # If no data is received by the receiver within one second of issuing an ACK, the receiver will terminate
                            try:
                                chunk, addr = sock.recvfrom(BUFFER_SIZE)
                            except TimeoutError:
                                print("Data transmission terminated prematurely.")
                                exit(1)

                            # 'Finished put' is a special message telling us that no more chunks will be sent
                            if chunk == b'Finished put':
                                break

                            sock.sendto("ACK: put".encode(), addr)
                            writer.write(chunk)
                            # Track the amount of bytes received to compare 
                            received = received + len(chunk)
                    
                    print("File Downloaded.")
                    # Check if server received all expected bytes
                    if received == sizeOfFile:
                        sock.sendto("FIN: put".encode(), addr) # Send last chunk to symbolize the end of the connection
                        print("All expected bytes received. Terminating connection.")
                    else:
                        print("Not all bytes have been received.")

                case 'get':
                    path = data_arr[1]
                    pathSize = os.path.getsize(path)
                    expectedSize = "LEN:" + str(pathSize)
                    # Check if the file exists
                    if not os.path.exists(path):
                        raise Exception("Path does not exist.")
                    print("file exists")

                    # Send expected file size
                    sock.sendto(expectedSize.encode(), addr)

                    with open(path, 'rb') as reader:
                        while True:
                            chunk = reader.read(BUFFER_SIZE)
                            if not chunk:
                                break

                            sock.sendto(chunk, addr)

                            # Disconnect if no response within 1 second of sending chunk
                            sock.settimeout(1.0)
                            try : 
                                response, addr = sock.recvfrom(BUFFER_SIZE)
                            except TimeoutError :
                                print("Did not receive ACK. Terminating.")
                                exit(1)
                            
                            # Anything other than the special message will raise an exception
                            if response != b"ACK: get" : 
                                raise Exception("ACK not received.")

                        sock.settimeout(None) # Reset
                        # Let the client know that you are done sending
                        sock.sendto("Finished get".encode(), addr)

                        finalResponse, addr = sock.recvfrom(BUFFER_SIZE)
                        if finalResponse == b'FIN: get' :
                            print("Server Response : File Uploaded. Terminating Connection")

                case 'remap':
                    offset = data_arr[1]
                    path = data_arr[2]
                    # Splitting the file by '.' to create a new file
                    # For example, "test.txt" --> [test], [txt] --> "test_remap.txt"
                    pathList = path.split('.')
                    new_path = pathList[0] + "_remap." + pathList[1]

                    # Check if the file exists
                    if not os.path.exists(path):
                        raise Exception("Path does not exist.")
                    print("file exists")

                    # Do the remapping
                    remappedList = remapList(offset)
                    # Convert remapped list to a string
                    new_alphabet = "".join(remappedList).encode()

                    # The file to be remapped has previously been remapped, since its remap counterpart (xxxx_remap.txt) exists
                    # Thus, we must overwrite the last remap with this new remap !
                    if os.path.exists(new_path):
                        # Another solution would be to delete the file using os.remove(new_path)
                        with open(new_path, "wb") as writer:
                            remapFile(path, new_alphabet, new_path)
                    else:
                        # The file to be remapped is a remap virgin, since its remap counterpart does not exist
                        remapFile(path, new_alphabet, new_path)

                    print("remapping complete")
                    # Let the server know where to find the remapped file.
                    sock.sendto(
                        f"File {os.path.basename(path)} remapped. Output file is {new_path}".encode(), addr)

                case 'quit':
                    print("Client has ended connection . . .")
                    exit(1)

# Make an array of strings, rotate the array, and return that array
def remapList(amount):
    lettersList = list(alphabet)
    tempVar = collections.deque(lettersList)
    # By rotating elements to the left, the letters that are ahead replace the positions of the original letters to allow accurate mapping
    # Original => Shifted to the left 2 times
    # [a, b, c, d, e, f] => [c, d, e, f, a, b]
    tempVar.rotate(-int(amount))
    finalList = list(tempVar)
    return finalList

# Read chunks from the desired file, remap each byte/character, and write it to a new file
def remapFile(path, new_alphabet, new_path):
    with open(path, "rb") as reader:
        while True:
            chunk = reader.read(BUFFER_SIZE)
            if not chunk:
                break
            # Make a translation table with the alphabet and the remapped alphabet
            translation = chunk.maketrans(alphabet.encode(), new_alphabet)
            # Store the translated chunk into new variable
            transChunk = chunk.translate(translation)
            with open(new_path, "a+b") as user:
                user.write(transChunk)

if __name__ == '__main__':
    main()
