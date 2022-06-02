import os
import socket
import sys

# Connection INFO
HOST = sys.argv[1]  
PORT = int(sys.argv[2]) 

BUFFER_SIZE = 1000 
SEPARATOR = "<SEPARATOR>"

def main():
    while True: # User has to quit manually
        # Utilizes a different connection after every command
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            response = input("Enter Command : ")
            response_arr = response.split(' ')  
            keyword = response_arr[0]

            match(keyword):

                case 'put':
                    if response_arr[1]:
                        put = "put"
                        path = response_arr[1]
                        pathSize = os.path.getsize(path)
                        expectedSize = "LEN:" + str(pathSize)

                        sock.sendto(f"{put}{SEPARATOR}{path}".encode(), (HOST, PORT)) #Send state, path, and size together; delimit at server side
                        print("Awaiting server response")
                        
                        sock.sendto(expectedSize.encode(), (HOST, PORT))

                        #Read the file in binary, sending each chunk to server
                        with open(path, "rb") as reader:
                            while True:
                                # If there is nothing more to read in the file, we break before sending the empty chunk which is why we send a crafted message to server telling them we have reached EOF.
                                chunk = reader.read(BUFFER_SIZE)
                                if not chunk:
                                    break

                                sock.sendto(chunk, (HOST, PORT))
                                
                                # Disconnect if no response within 1 second of sending chunk
                                sock.settimeout(1.0)
                                try : 
                                    response, addr = sock.recvfrom(BUFFER_SIZE)
                                except TimeoutError :
                                    print("Did not receive ACK. Terminating.")
                                    exit(1)

                                # Anything other than the special message will raise an exception
                                if response != b"ACK: put" : 
                                    raise Exception("ACK not received.")
                            
                            sock.settimeout(None) # Reset timeout for other receive instances - finalResponse
                            #Send this to server when all is read  
                            sock.sendto("Finished put".encode(), addr)
                            # Verify that the server is done receiving
                            finalResponse, addr = sock.recvfrom(BUFFER_SIZE)
                            if finalResponse == b'FIN: put':
                                print("Server Response : File Uploaded. Terminating Connection.")
                    else:
                        raise Exception("Please include path of the file")
                    
                case 'get':
                    if response_arr[1]:
                        get = "get"
                        path = response_arr[1]
                        sock.sendto(f"{get}{SEPARATOR}{path}".encode(), (HOST, PORT))

                        #This should apply to subsequent sock.recv 
                        sock.settimeout(1.0)

                        # If no data arrives at the receiver within one second from the reception of a LEN message, the receiver program should terminate
                        try : 
                            expectedSize, addr = sock.recvfrom(BUFFER_SIZE)
                        except TimeoutError:
                            print("Did not receive data. Terminating.")
                            exit(1)

                        # The expectedSize is a string, "LEN:{bytes}", and I only care about the bytes, so I separate it. 
                        size_arr = expectedSize.decode().split(":")
                        sizeOfFile = int(size_arr[1])
                        received = 0 # Sum of bytes

                        # Get the chunks and write those chunks to client's file
                        with open(path, "wb") as writer:
                            while True:
                                # If no data is received by the receiver within one second of issuing an ACK, the receiver will terminate
                                try : 
                                    chunk, addr = sock.recvfrom(BUFFER_SIZE)
                                except TimeoutError :
                                    print("Data transmission terminated prematurely.")
                                    exit(1)

                                if chunk == b'Finished get':
                                    break

                                sock.sendto("ACK: get".encode(), addr)
                                writer.write(chunk)  
                                received = received + len(chunk) # Tracking bytes
                            
                        print(f"File {os.path.basename(path)} downloaded. ")
                        if received == sizeOfFile : 
                            sock.sendto("FIN: get".encode(), addr) # Send last chunk to symbolize the end of the connection
                            print("All expected bytes received. Terminating connection.")
                        else : 
                            print("Not all bytes have been received.")
                    else:
                        raise Exception("Please include path of the file")

                case 'remap':
                    if response_arr[1] and response_arr[2]: 
                        remap = "remap"
                        offset = response_arr[1]
                        file = response_arr[2]
                        sock.sendto(f"{remap}{SEPARATOR}{offset}{SEPARATOR}{file}".encode(), (HOST, PORT))

                        # Receive server response detailing the path to the remapped file
                        response, addr = sock.recvfrom(BUFFER_SIZE)
                        print(response.decode())
                    else :
                        raise Exception("Please include the offset and target file") 

                case 'quit':
                    # Exit system
                    quit = "quit"
                    sock.sendto(f"{quit}".encode(), (HOST, PORT))
                    
                    print("Exiting Program !")
                    exit(1)
                case _ : #Default 
                    raise Exception("Command undefined, please try again")


if __name__ == "__main__" :
    main()