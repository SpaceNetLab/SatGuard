import socket
send = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
send.sendto(b'handover_signal',("240b::2",6000))
send.sendto(b'handover_signal',("240b::4",9000))
send.sendto(b'handover_signal',("240b::4",8888))
