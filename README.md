# SatGuard
SatGuard is a novel in-orbit loss recovery mechanism that can effectively improve user-perceived Web QoE by enabling fast link local retransmission and concealing endless and bursty packet losses in LSNs for endpoint applications.
# Prerequisites
SatGuard is mainly built upon Python. Since many emerging satellites run Linux-like on-board operating systems, we implement the current version of SatGuard upon Linux kernel 5.4. Before running SatGuard, please make sure you have already installed those dependencies on your machine.
- Python 3.8 or above.
- NetfilterQueue 1.1.0.
- Linux Kernel 4.10 or above.

For more details of the setup on NetfilterQueue, please check [here](https://github.com/oremanj/python-netfilterqueue).
SatGuard can work in can be run on a real physical server, virtual machine or container. We set up an LSN testbed based on [Starrynet](https://github.com/SpaceNetLab/StarryNet) and deploy SatGuard on the container nodes.

# Show Case 1
![image](https://github.com/SpaceNetLab/SatGuard/blob/main/doc/case1.png)

The above figure is a case of static scenario. For simplicity, we consider the Dishy directly as the sender in the case. Each node is a container instance. In this scenario, the link between the satellite and the ground station is unstable, enabling SatGuard in the upstream and downstream of the link can effectively improve transmission efficiency.

To reproduce the case, configure the `satguard.py` according to your real network and the follow these steps.
- Execute `python3 satguard.py -l upstream -s static` on the upstream node.
- Execute `python3 satguard.py -l downstream -s static` on the downstream node.
- After both node shows `ready`, the transmission test can begin.

# Show Case 2
![image](https://github.com/SpaceNetLab/SatGuard/blob/main/doc/case2.png)

The above figure is a case of dynamic scenario. The solid line represents the connection between the simulated nodes, and the string next to it represents the network segment. The handover manager is also a node in the simulation environment that is responsible for routing updates before and after the handover, but this is out of the scope of SatGuard. The dotted line represents the virtual connection between the handover manager and the nodes associated with the handover, which is used to control them to update the routing table.

To reproduce the case, configure the `satguard.py` and scripts about handover according to your real network and then follow these steps.
- Distribute the handover scripts to the handover manager and related nodes.
- Execute `python3 satguard.py -l downstream -s dynamic` on the downstream node.
- Execute `python3 satguard.py -l downstream -s dynamic` on the first upstream node.
- Execute `python3 satguard.py -l downstream -s dynamic` on the second upstream node.
- After all nodes shows `ready`, the transmission test can begin.
- Execute `handover.sh` to let the GS connect to satellite 1.
- Execute `recovery.sh` to let the GS connect to satellite 2.
