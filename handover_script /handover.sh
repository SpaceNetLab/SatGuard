python3 handover2to1_before.py
sshpass -p admin ssh 240b::4 'sh gs_handover_route_update.sh'&
sshpass -p admin ssh 240b::2 'sh sat_handover_route_update.sh'
sleep 0.1
python3 handover2to1_after.py


