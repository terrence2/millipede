class error(Exception):
	pass

class socket:
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.family = None
		self.proto = None
		self.timeout = None
		self.type = None
	def __getattribute__(self, *args, **kwargs): pass
	def __init__(self, *args, **kwargs): pass
	def __repr__(self, *args, **kwargs): pass
	def bind(self, *args, **kwargs): pass
	def close(self, *args, **kwargs): pass
	def connect(self, *args, **kwargs): pass
	def connect_ex(self, *args, **kwargs): pass
	def fileno(self, *args, **kwargs): pass
	def getpeername(self, *args, **kwargs): pass
	def getsockname(self, *args, **kwargs): pass
	def getsockopt(self, *args, **kwargs): pass
	def gettimeout(self, *args, **kwargs): pass
	def listen(self, *args, **kwargs): pass
	def recv(self, *args, **kwargs): pass
	def recv_into(self, *args, **kwargs): pass
	def recvfrom(self, *args, **kwargs): pass
	def recvfrom_into(self, *args, **kwargs): pass
	def send(self, *args, **kwargs): pass
	def sendall(self, *args, **kwargs): pass
	def sendto(self, *args, **kwargs): pass
	def setblocking(self, *args, **kwargs): pass
	def setsockopt(self, *args, **kwargs): pass
	def settimeout(self, *args, **kwargs): pass
	def shutdown(self, *args, **kwargs): pass



def dup(*args, **kwargs): pass
def getaddrinfo(*args, **kwargs): pass
def getdefaulttimeout(*args, **kwargs): pass
def gethostbyaddr(*args, **kwargs): pass
def gethostbyname(*args, **kwargs): pass
def gethostbyname_ex(*args, **kwargs): pass
def gethostname(*args, **kwargs): pass
def getnameinfo(*args, **kwargs): pass
def getprotobyname(*args, **kwargs): pass
def getservbyname(*args, **kwargs): pass
def getservbyport(*args, **kwargs): pass
def htonl(*args, **kwargs): pass
def htons(*args, **kwargs): pass
def inet_aton(*args, **kwargs): pass
def inet_ntoa(*args, **kwargs): pass
def inet_ntop(*args, **kwargs): pass
def inet_pton(*args, **kwargs): pass
def ntohl(*args, **kwargs): pass
def ntohs(*args, **kwargs): pass
def setdefaulttimeout(*args, **kwargs): pass
def socketpair(*args, **kwargs): pass



AF_APPLETALK = 5
AF_ASH = 18
AF_ATMPVC = 8
AF_ATMSVC = 20
AF_AX25 = 3
AF_BRIDGE = 7
AF_DECnet = 12
AF_ECONET = 19
AF_INET = 2
AF_INET6 = 10
AF_IPX = 4
AF_IRDA = 23
AF_KEY = 15
AF_LLC = 26
AF_NETBEUI = 13
AF_NETLINK = 16
AF_NETROM = 6
AF_PACKET = 17
AF_PPPOX = 24
AF_ROSE = 11
AF_ROUTE = 16
AF_SECURITY = 14
AF_SNA = 22
AF_TIPC = 30
AF_UNIX = 1
AF_UNSPEC = 0
AF_WANPIPE = 25
AF_X25 = 9
AI_ADDRCONFIG = 32
AI_ALL = 16
AI_CANONNAME = 2
AI_NUMERICHOST = 4
AI_NUMERICSERV = 1024
AI_PASSIVE = 1
AI_V4MAPPED = 8
CAPI = None
EAI_ADDRFAMILY = -9
EAI_AGAIN = -3
EAI_BADFLAGS = -1
EAI_FAIL = -4
EAI_FAMILY = -6
EAI_MEMORY = -10
EAI_NODATA = -5
EAI_NONAME = -2
EAI_OVERFLOW = -12
EAI_SERVICE = -8
EAI_SOCKTYPE = -7
EAI_SYSTEM = -11
INADDR_ALLHOSTS_GROUP = 3758096385
INADDR_ANY = 0
INADDR_BROADCAST = 4294967295
INADDR_LOOPBACK = 2130706433
INADDR_MAX_LOCAL_GROUP = 3758096639
INADDR_NONE = 4294967295
INADDR_UNSPEC_GROUP = 3758096384
IPPORT_RESERVED = 1024
IPPORT_USERRESERVED = 5000
IPPROTO_AH = 51
IPPROTO_DSTOPTS = 60
IPPROTO_EGP = 8
IPPROTO_ESP = 50
IPPROTO_FRAGMENT = 44
IPPROTO_GRE = 47
IPPROTO_HOPOPTS = 0
IPPROTO_ICMP = 1
IPPROTO_ICMPV6 = 58
IPPROTO_IDP = 22
IPPROTO_IGMP = 2
IPPROTO_IP = 0
IPPROTO_IPIP = 4
IPPROTO_IPV6 = 41
IPPROTO_NONE = 59
IPPROTO_PIM = 103
IPPROTO_PUP = 12
IPPROTO_RAW = 255
IPPROTO_ROUTING = 43
IPPROTO_RSVP = 46
IPPROTO_TCP = 6
IPPROTO_TP = 29
IPPROTO_UDP = 17
IPV6_CHECKSUM = 7
IPV6_DSTOPTS = 59
IPV6_HOPLIMIT = 52
IPV6_HOPOPTS = 54
IPV6_JOIN_GROUP = 20
IPV6_LEAVE_GROUP = 21
IPV6_MULTICAST_HOPS = 18
IPV6_MULTICAST_IF = 17
IPV6_MULTICAST_LOOP = 19
IPV6_NEXTHOP = 9
IPV6_PKTINFO = 50
IPV6_RECVDSTOPTS = 58
IPV6_RECVHOPLIMIT = 51
IPV6_RECVHOPOPTS = 53
IPV6_RECVPKTINFO = 49
IPV6_RECVRTHDR = 56
IPV6_RECVTCLASS = 66
IPV6_RTHDR = 57
IPV6_RTHDRDSTOPTS = 55
IPV6_RTHDR_TYPE_0 = 0
IPV6_TCLASS = 67
IPV6_UNICAST_HOPS = 16
IPV6_V6ONLY = 26
IP_ADD_MEMBERSHIP = 35
IP_DEFAULT_MULTICAST_LOOP = 1
IP_DEFAULT_MULTICAST_TTL = 1
IP_DROP_MEMBERSHIP = 36
IP_HDRINCL = 3
IP_MAX_MEMBERSHIPS = 20
IP_MULTICAST_IF = 32
IP_MULTICAST_LOOP = 34
IP_MULTICAST_TTL = 33
IP_OPTIONS = 4
IP_RECVOPTS = 6
IP_RECVRETOPTS = 7
IP_RETOPTS = 7
IP_TOS = 1
IP_TTL = 2
MSG_CTRUNC = 8
MSG_DONTROUTE = 4
MSG_DONTWAIT = 64
MSG_EOR = 128
MSG_OOB = 1
MSG_PEEK = 2
MSG_TRUNC = 32
MSG_WAITALL = 256
NETLINK_DNRTMSG = 14
NETLINK_FIREWALL = 3
NETLINK_IP6_FW = 13
NETLINK_NFLOG = 5
NETLINK_ROUTE = 0
NETLINK_USERSOCK = 2
NETLINK_XFRM = 6
NI_DGRAM = 16
NI_MAXHOST = 1025
NI_MAXSERV = 32
NI_NAMEREQD = 8
NI_NOFQDN = 4
NI_NUMERICHOST = 1
NI_NUMERICSERV = 2
PACKET_BROADCAST = 1
PACKET_FASTROUTE = 6
PACKET_HOST = 0
PACKET_LOOPBACK = 5
PACKET_MULTICAST = 2
PACKET_OTHERHOST = 3
PACKET_OUTGOING = 4
PF_PACKET = 17
SHUT_RD = 0
SHUT_RDWR = 2
SHUT_WR = 1
SOCK_DGRAM = 2
SOCK_RAW = 3
SOCK_RDM = 4
SOCK_SEQPACKET = 5
SOCK_STREAM = 1
SOL_IP = 0
SOL_SOCKET = 1
SOL_TCP = 6
SOL_TIPC = 271
SOL_UDP = 17
SOMAXCONN = 128
SO_ACCEPTCONN = 30
SO_BROADCAST = 6
SO_DEBUG = 1
SO_DONTROUTE = 5
SO_ERROR = 4
SO_KEEPALIVE = 9
SO_LINGER = 13
SO_OOBINLINE = 10
SO_RCVBUF = 8
SO_RCVLOWAT = 18
SO_RCVTIMEO = 20
SO_REUSEADDR = 2
SO_SNDBUF = 7
SO_SNDLOWAT = 19
SO_SNDTIMEO = 21
SO_TYPE = 3
TCP_CORK = 3
TCP_DEFER_ACCEPT = 9
TCP_INFO = 11
TCP_KEEPCNT = 6
TCP_KEEPIDLE = 4
TCP_KEEPINTVL = 5
TCP_LINGER2 = 8
TCP_MAXSEG = 2
TCP_NODELAY = 1
TCP_QUICKACK = 12
TCP_SYNCNT = 7
TCP_WINDOW_CLAMP = 10
TIPC_ADDR_ID = 3
TIPC_ADDR_NAME = 2
TIPC_ADDR_NAMESEQ = 1
TIPC_CFG_SRV = 0
TIPC_CLUSTER_SCOPE = 2
TIPC_CONN_TIMEOUT = 130
TIPC_CRITICAL_IMPORTANCE = 3
TIPC_DEST_DROPPABLE = 129
TIPC_HIGH_IMPORTANCE = 2
TIPC_IMPORTANCE = 127
TIPC_LOW_IMPORTANCE = 0
TIPC_MEDIUM_IMPORTANCE = 1
TIPC_NODE_SCOPE = 3
TIPC_PUBLISHED = 1
TIPC_SRC_DROPPABLE = 128
TIPC_SUBSCR_TIMEOUT = 3
TIPC_SUB_CANCEL = 4
TIPC_SUB_PORTS = 1
TIPC_SUB_SERVICE = 0
TIPC_TOP_SRV = 1
TIPC_WAIT_FOREVER = -1
TIPC_WITHDRAWN = 2
TIPC_ZONE_SCOPE = 1
has_ipv6 = True
