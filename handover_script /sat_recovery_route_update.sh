ip -6 route del 240c:3116::/64 via fe80::2 dev ens6
sleep 0.05
ip -6 route add 240c:3116::/64 via fe80::1 dev ens7
