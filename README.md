# TCP-UDP-Remapper
A remapper in python for TCP and UDP

CSI 416 Project 1, The remapper : socket programming and reliable data transfer
----------------------------------------------------------------------------------------
Remapping functionality: The application will allow a user to upload a text file of
arbitrary size to the server. The file will then be loaded, read, and each character will be
remapped. The redacted text will be stored in a new file. The remapper function will
replace each character in the text file with a corresponding character that is N positions
ahead in the English alphabet. For example, if the target string is “clock”, and N=5 the
remapped string will be “hqthp”. Once the server is done remapping, it will issue a
message to the user indicating the output filename. The server will then allow the client
to download the output file. We will implement a limited remapping function that will
only work on the lower-case letters of the English alphabet (no uppercase letters,
numbers or special characters will have to be remapped).

Supported commands: Your program should allow a user to upload and download text
files, specify the remapping offset N, and quit the program. To this end, you will
implement the following commands that the client can send to the server:
- Copy a file from the client to the server (put), which takes as an input argument the
full path to a file [file] on the client. Example execution:
put [file]
- Copy a file from a server to a client (get), which also takes as an argument the full
path to a file [file] on the server. Example execution:
get [file]
- Remap command that will allow the user to specify a remapping offset N and a
target file in which to perform the remapping. Example execution:
remap [int] [file]
- Quit the program per user request.
Example execution: "quit"
