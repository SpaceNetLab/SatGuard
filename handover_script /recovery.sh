python3 handover1to2_before.py
sshpass -p admin ssh 240b::2 'sh sat_recovery_route_update.sh'&
sshpass -p admin ssh 240b::4 'sh gs_recovery_route_update.sh'
sleep 0.1
python3 handover1to2_after.py
