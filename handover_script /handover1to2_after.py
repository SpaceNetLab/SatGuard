import socket
send = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
send.sendto(b'hi',("240b::2",10000))
send.sendto(b'hi',("240b::3",10000))
