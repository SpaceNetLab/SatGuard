import socket
send = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
send.sendto(b'handover_signal',("240b::3",6000))
send.sendto(b'handover_signal',("240b::4",9999))
send.sendto(b'handover_signal',("240b::2",8000))
