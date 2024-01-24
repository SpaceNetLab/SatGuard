# SatGuard
SatGuard is a novel in-orbit loss recovery mechanism that can effectively improve user-perceived Web QoE by enabling fast link local retransmission and concealing endless and bursty packet losses in LSNs for endpoint applications.
# Prerequisites
SatGuard is mainly built upon Python. Since many emerging satellites run Linux-like on-board operating systems, we implement the current version of SatGuard upon Linux kernel 5.4. Before running SatGuard, please make sure you have already installed those dependencies on your machine.
- Python 3.8 or above.
- NetfilterQueue 1.1.0.
- Linux Kernel 4.10 or above.

For more details of the setup on NetfilterQueue, please check [here](https://github.com/oremanj/python-netfilterqueue).
SatGuard can work in can be run on a real physical server, virtual machine or container. We set up an LSN testbed based on [Starrynet](https://github.com/SpaceNetLab/StarryNet) and deploy SatGuard on the container nodes.

# Show Case
