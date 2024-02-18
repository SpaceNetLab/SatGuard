import math
import os
import argparse
import time
import socket
from multiprocessing import Pipe,Process,Value
from threading import Thread
import threading
import sys
from utils import *

# Network configuration
sender_IP = '240c:3055::1'
recv_IP = '240c:3116::2'
recv_HACK_IP = '240c:3136::2'
preloading_dst_IP = '240c:3052::2'
recv_handover_info_IP = '240b::12'
recv_preloading_pkts_IP = '240c:3052::1'
send_HACK_IP = '240c:3136::2'
send_handover_HACK_IP_1 = '240c:3126::2'
send_handover_HACK_IP_2 = '240c:3136::2'
send_handover_HACK_MAC_1 = '11:11:11:11:11:11'
send_handover_HACK_MAC_2 = '22:22:22:22:22:22'

def mac2byte(mac):
    macstr = mac[0:2] + mac[3:5] + mac[6:8] + mac[9:11] + mac[12:14] + mac[15:17]
    macbyte = bytes.fromhex(macstr)
    return macbyte

send_handover_HACK_MAC_1 = mac2byte(send_handover_HACK_MAC_1)
send_handover_HACK_MAC_2 = mac2byte(send_handover_HACK_MAC_2)


# Parsing Arguments
parser = argparse.ArgumentParser(description='arguments for SatGuard', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--location', '-l', type = str, help='upstream or downstream')
parser.add_argument('--scenario', '-s', type = str, help='dynamic or static')
parser.add_argument('--debug', '-d', type = int, help='1 or 0')
args = parser.parse_args()

os.system("ip6tables -F")   #   Clear previous filter rules
os.system("ip6tables -F -t mangle")     # Clear previous filter rules

if args.scenario == 'static':
    if args.location == 'upstream':
        os.system("ip6tables -I FORWARD -d %s/128 -s %s/128 -j NFQUEUE --queue-num 1" % (recv_IP, sender_IP))       # Capture normal packets
        os.system("ip6tables -t mangle -A PREROUTING -d %s/128 -p udp --dport 4000 -j NFQUEUE --queue-num 2" % recv_HACK_IP)     # Capture feedback (HACK) packet
    if args.location == 'downstream':
        os.system("ip6tables -I FORWARD -d %s/128 -s %s/128 -j NFQUEUE --queue-num 1" % (recv_IP, sender_IP))       # Capture normal packets

if args.scenario == 'dynamic':
    if args.location == 'upstream':
        os.system("ip6tables -I FORWARD -d %s/128 -s %s/128 -j NFQUEUE --queue-num 1" % (recv_IP, sender_IP))  # Capture normal packets
        os.system("ip6tables -t mangle -A PREROUTING -d %s/128 -p udp --dport 4000 -j NFQUEUE --queue-num 2" % recv_HACK_IP)  # Capture feedback (HACK) packet
        os.system("ip6tables -I OUTPUT -d ::1/128 -p udp --dport 5000 -j NFQUEUE --queue-num 3")    # Capture virtual local ReTx pkts
        os.system("ip6tables -t mangle -A PREROUTING -d %s/128 -p udp --dport 9000 -j NFQUEUE --queue-num 4" % recv_preloading_pkts_IP)   # Capture preloading pkts
        os.system("ip6tables -I INPUT -d %s/128 -p udp --dport 6000 -j NFQUEUE --queue-num 5" % recv_handover_info_IP)  # Capture handover start info in  port 6000
        os.system("ip6tables -I INPUT -d %s/128 -p udp --dport 10000 -j NFQUEUE --queue-num 6" % recv_handover_info_IP) # Capture handover end info in port 10000

    if args.location == 'downstream':
        # donwstream handover only
        os.system("ip6tables -I FORWARD -d %s/128 -s %s/128 -j NFQUEUE --queue-num 1" % (recv_IP, sender_IP))
        os.system("ip6tables -I INPUT -d %s/128 -p udp --dport 8888 -j NFQUEUE --queue-num 7" % recv_handover_info_IP)
        os.system("ip6tables -I INPUT -d %s/128 -p udp --dport 9999 -j NFQUEUE --queue-num 8" % recv_handover_info_IP)

if args.location == 'static':
    if args.location == 'upstream':
        recv_HACK_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        recv_HACK_socket.bind((recv_HACK_IP, 4000))        #receive HACK

if args.scenario == 'dynamic':
    if args.location == 'upstream':
        recv_virtual_ReTx_pkt_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        recv_virtual_ReTx_pkt_socket.bind(('::1', 5000))       # receive local retransmission signal

        recv_handover_start_info_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        recv_handover_start_info_socket.bind((recv_handover_info_IP, 6000))       #recv handover start info

        recv_preloading_pkts_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        recv_preloading_pkts_socket.bind((recv_preloading_pkts_IP, 9000))        #receive preloading packets

        recv_handover_end_info_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        recv_handover_end_info_socket.bind((recv_handover_info_IP, 10000))       #recv handover end info
    if args.location == 'downstream':
        handover_from_sat1_to_sat2_signal_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        handover_from_sat1_to_sat2_signal_socket.bind((recv_handover_info_IP, 8888))  # activation
        handover_from_sat2_to_sat1_signal_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        handover_from_sat2_to_sat1_signal_socket.bind((recv_handover_info_IP, 9999))  # activation

send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)


DEBUG = args.debug       # DEBUG flag

HSeq_Lock = threading.Lock()        # Lock for HSeq number
send_ack_flag_Lock = threading.Lock()       # Lock for send_ack_flag described bellow

HSeq = []
hbh_header = '000204'
hbh_header = bytearray.fromhex(hbh_header)
for i in range(0,2**24):        # prepare hexadecimal HSeq
    hexstr = hex(i)
    hexstr = hexstr[2:]
    hexstr = hexstr.zfill(6)
    HSeq.append(bytearray.fromhex(hexstr))
print('Ready.')     # Ready for local ReTx
down_handover_flag = 0      #flag = 1 means handover happens
pre_hack_no = Value('i',-1)
pre_HSeq = -1
index = 0   # current HSeq number
maxHSeq = 2 ** 24      # MAX HSeq number
cache=[0 for i in range(1,2**24)]       # in-network cache

send_ack_flag = 0   # this flag means which upstream node to send ACK to in a handover
preloading_flag = 1    # this flag means whether to preload cache pkts.
# Once the new satellite is in the transmission path, the old satellite does not need to preload pkts to save bandwidth

new_next_header = hex(0)        # next_header = 0 means the next header is a hop-by-hop header
new_next_header = new_next_header[2:]
new_next_header = new_next_header.zfill(2)

def func(out_pipe, in_pipe, pre_hack_no):
    global maxHSeq
    in_pipe.close()
    while True:
        try:
            hack_no = out_pipe.recv_bytes(8)
            hack_no = int(hack_no.hex(),16)
            if DEBUG:
                print(pre_hack_no,hack_no)
            cnt = 0
            for loss_no in range(max(0,hack_no-3000),hack_no):
                send_socket.sendto(HSeq[loss_no],("::1", 5000))
                time.sleep(0.00005)
        except EOFError:
            out_pipe.close()
            break

################################################ upstream specific ####################################

def pack_without_hbh(pkt):      # Embed HSeq to the pkt without IPv6 hop-by-hop extension header
    global index, pre_hack_no, down_handover_flag, preloading_flag
    if DEBUG:
        print('send packet',down_handover_flag,index)
    pld = pkt.get_payload()
    HSeq_Lock.acquire()
    if index==maxHSeq:
        index = 0
    seq = index
    index += 1
    HSeq_Lock.release()
    pldarray = bytearray(pld)
    pldarray[1:4] = HSeq[seq]    # Embed HSeq in floa label and traffic class filed
    pld = bytes(pldarray)
    pkt.set_payload(pld)
    cache[seq]=pld          # cache Embeded pkt
    if down_handover_flag == 1 and preloading_flag == 1:     # flag=1 means preloading pkts to next predicted satellite
        if DEBUG:
            print('preloading')
        send_socket.sendto(pld,(preloading_dst_IP, 9000))
    pkt.accept()

def pack_with_hbh(pkt):      # Embed HSeq to the pkt with IPv6 hop-by-hop extension header
    global down_handover_flag,index, pre_hack_no, preloading_flag
    if DEBUG:
        print('send packet',down_handover_flag,index)
    pld = pkt.get_payload()
    HSeq_Lock.acquire()
    if index==maxHSeq:
        index = 0
    seq = index
    index += 1
    HSeq_Lock.release()
    if pkt.get_mark()!= 1:
        payload = bytearray()
        if pld[6] == bytes(bytearray.fromhex('00'))[0]:
            if DEBUG:
                print('reassign hseq')
            payload.extend(pld[:44])
            payload.extend(HSeq[seq])
            payload.extend(pld[48:])
        else:
            payload.extend(pld[:4])
            payload.extend(bytes.fromhex(hex(int.from_bytes(pld[4:6], 'big') + 8)[2:].zfill(4)))
            payload.extend(bytes.fromhex(new_next_header))
            payload.extend(pld[7:40])
            payload.extend(pld[6:7])
            payload.extend(hbh_header)
            payload.extend(HSeq[seq])
            payload.extend(pld[40:])
        pld = bytes(payload)
        pkt.set_payload(pld)
        cache[seq]=pld
        if down_handover_flag == 1 and preloading_flag == 1:
            if DEBUG:
                print('preloading')
            send_socket.sendto(pld,(preloading_dst_IP, 9000))
    else:       # locally ReTx pkts
        hbh = HSeq[seq]
        pldarray = bytearray(pld)
        payload = pldarray[:41] + hbh_header + hbh + pldarray[48:]
        pld = bytes(payload)
        pkt.set_payload(pld)
        cache[seq]=pld
    pkt.accept()

######### upstream handover specific ###################################

def change_handover_flag(pkt):     # receive handover signal from handover manager to set handover_flag to 1 to start cache migration
    global down_handover_flag
    if DEBUG:
        print('start handover')
    #Lock2.acquire()
    down_handover_flag = 1
    # remove the Lock about down_handover_flag
    # therefore the handover interval should be longer than route change time
    # recommending time > 10s
    #Lock2.release()
    pkt.accept()

def handover_finish(pkt):
    # run in the previous satellite of a handover
    # current handover is finished
    # receive signal from handover manager, clean state and restart, ready for next handover to forward pkts
    if DEBUG:
        print('clean state and restart')
    global index, pre_hack_no,down_handover_flag
    HSeq_Lock.acquire()
    index = 0
    pre_hack_no = -1
    if DEBUG:
        print('index, pre_ack',index, pre_hack_no)
    HSeq_Lock.release()
    # Lock2.acquire()
    down_handover_flag = 0
    # add_retran = 0
    # Lock2.release()
    pkt.drop()

def cache_preloading_pkt(pkt):
    # run in the next satellite of a handover
    # cache preloaded packets

    global index,add_ack,add_retran
    pld = pkt.get_payload()
    #print(pld)
    #pldarray = bytearray(pld)
    #in_pipe2.send_bytes(pld[48:])   # format: ipv6 header (src:upstream, dst:downstream) (40bytes) udp header (8bytes) + ipv6 header (src: src, dst: dst)(40bytes) + hbh header (8bytes)+ payload
    #handover_cache.append(pldarray[48:])
    HSeq_Lock.acquire()
    if index==maxHSeq:
       index = 0
    seq = index
    index += 1
    HSeq_Lock.release()
    payload = bytearray()
    payload.extend(pld[48:])
    # cache pkts from current HSeq instead of 0
    # because current satellite may receives normal pkts before preloading pkts, depending on your routing change mechanism
    cache[seq]=bytes(payload)

    #if add_retran:
    #    for loss_no in range(add_ack,seq+1):
    #        send_socket.sendto(HSeq[loss_no],("::1", 5000))
    #        print('cache preloading and retran pkt done, mark as ',loss_no)
    if DEBUG:
        print('cache preloading pkt done, mark as ',seq)
    pkt.drop()

######### upstream handover specific ###################################



######### upstream ReTx specific ###################################


def HNACK_to_ReTx(pkt):
    # change an HNACK feedback pkt to a ReTx pkt
    # ReTx pkt has the old HSeq
    pld = pkt.get_payload()
    loss = pld[48:]
    loss_no = int(loss.hex(),16)
    pkt.set_payload(cache[loss_no])
    pkt.accept()

def send_ReTx_signal_to_pipe(pkt,in_pipe):
    pld = pkt.get_payload()
    in_pipe.send_bytes(pld[48:])
    pkt.drop()

def udp_to_ReTx(pkt):
    # change an local UDP pkt to a ReTx pkt
    # ReTx pkt has the old HSeq
    pld = pkt.get_payload()
    loss = pld[48:]
    loss_no = int(loss.hex(),16)
    pkt.set_payload(cache[loss_no])
    pkt.accept()


######### upstream ReTx specific ###################################




################################################ upstream specific ####################################


################################################ downstream specific ####################################

def send_acknowledgments(start, end, ip, port):
    # function for sending HACK to the upstream node
    for no in range(start, end):
        send_socket.sendto(HSeq[no], (ip, port))

def feedback_HNACK(pkt):
    # HNACK feedback, but we don't care about ReTx loss if the upsrtream node don't give ReTx pkt a larger HSeq
    # Recommended for static scenarios, e.g., loss in ISLs
    # The ability of loss detection for ReTx pkt is determined by the upstream node instead of the downstream node
    global pre_HSeq      # recv previous serial HSeq
    pld = pkt.get_payload()
    pldarray = bytearray(pld)
    current_no = pldarray[1:4]
    current_no = int(current_no.hex(),16)   # recv current HSeq
    if current_no - pre_HSeq != 1:       # HSeq mutation is detected
        if pre_HSeq - current_no > maxHSeq // 2:         # recv HSeq list is: pre_HSeq..loss..loss..max-1...0...1...2...current
            send_acknowledgments(pre_HSeq + 1, maxHSeq, send_HACK_IP, 4000)        # TODO: ipm5 should be an arguement
            send_acknowledgments(0, current_no, send_HACK_IP, 4000)
            #print(current_no,pre_HSeq)
            pre_HSeq = current_no
        elif current_no > pre_HSeq:                      # recv HSeq list is: pre_HSeq..loss..loss..current
            send_acknowledgments(pre_HSeq + 1, current_no, send_HACK_IP, 4000)
            #print(current_no,pre_HSeq)
            pre_HSeq = current_no
        # if current_no < pre_HSeq and pre_HSeq - current_no < maxHSeq // 2, recv an ReTx pkt
    else:           # in order
        pre_HSeq = current_no
    if pre_HSeq == maxHSeq-1:
        pre_HSeq = -1
    pkt.accept()


def feedback_HACK(pkt):
    # HNACK feedback, but we don't care about ReTx loss if the upsrtream node don't give ReTx pkt a larger HSeq
    global index, maxHSeq, pre_HSeq, send_ack_flag
    if send_ack_flag == 1:
        pld = pkt.get_payload()
        pldarray = bytearray(pld)
        current_no = pldarray[1:4]
        current_no = int(current_no.hex(), 16)
        if DEBUG:
            print('recv ', current_no, ' send to satellite 1')
        try:
            if pkt.get_hw()[0:6] == send_handover_HACK_MAC_1:
                if DEBUG:
                    print('send ack to satellite 1', current_no)
                send_socket.sendto(HSeq[current_no], (send_handover_HACK_IP_1, 4000))
                send_ack_flag = 0
        except OSError:
            pass
    elif send_ack_flag == 2:
        pld = pkt.get_payload()
        pldarray = bytearray(pld)
        current_no = pldarray[1:4]
        current_no = int(current_no.hex(), 16)
        if DEBUG:
            print('recv ', current_no, ' send to satellite 2')
        try:
            if pkt.get_hw()[0:6] == send_handover_HACK_MAC_2:
                if DEBUG:
                    print('send ack to satellite 2', current_no)
                send_socket.sendto(HSeq[current_no], (send_handover_HACK_IP_2, 4000))
                send_ack_flag = 0
        except OSError:
            pass
    pkt.accept()

def signal2sat1(pkt):       # switch to satellite 1
    global send_ack_flag
    if DEBUG:
        print('start handover')
    send_ack_flag_Lock.acquire()
    send_ack_flag = 1
    send_ack_flag_Lock.release()
    pkt.accept()

def signal2sat2(pkt):      # # switch to satellite 2
    global send_ack_flag
    if DEBUG:
        print('start handover')
    send_ack_flag_Lock.acquire()
    send_ack_flag = 2
    send_ack_flag_Lock.release()
    pkt.accept()

################################################ downstream specific ####################################

if __name__ == '__main__':

    pre_hack_no = 0
    out_pipe, in_pipe = Pipe()
    Process(target=func, args=(out_pipe, in_pipe, pre_hack_no,)).start()
    # Instantiate loop
    loop = asyncio.get_event_loop()
    # Create NFQueue3 objects
    queues = []
    if args.scenario == 'static':
        if args.location == 'upstream':
            queues.append(NFQueue3(1, pack_without_hbh))
            queues.append(NFQueue3(2, HNACK_to_ReTx))
        if args.location == 'downstream':
            queues.append(NFQueue3(1, feedback_HNACK))
    if args.scenario == 'dynamic':
        if args.location == 'upstream':
            queues.append(NFQueue3(1, pack_without_hbh))
            queues.append(NFQueue3(2, send_ReTx_signal_to_pipe, in_pipe))
            queues.append(NFQueue3(3, udp_to_ReTx))
            queues.append(NFQueue3(4, cache_preloading_pkt))
            queues.append(NFQueue3(5, change_handover_flag))
            queues.append(NFQueue3(6, handover_finish))
        if args.location == 'downstream':
            queues.append(NFQueue3(1, feedback_HACK))
            queues.append(NFQueue3(7, signal2sat2))
            queues.append(NFQueue3(8, signal2sat1))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    for q in queues:
        q.terminate()
    loop.close()
os.system("ip6tables -F")
os.system("ip6tables -F -t mangle")



