import random
import time

class Packet:
    def __init__(self, source_port, dest_port, seq_num, ACK_num, ACK_bit, SYN_bit, FIN_bit, receive_window, checksum_error, data):
        self.source_port = source_port
        self.dest_port = dest_port
        self.seq_num = seq_num
        self.ACK_num = ACK_num
        self.ACK_bit = ACK_bit
        self.SYN_bit = SYN_bit
        self.FIN_bit = FIN_bit
        self.receive_window = receive_window
        self.checksum_error = checksum_error
        self.data = data
    
    def __str__(self):
        return f"source_port: {self.source_port}\ndest_port: {self.dest_port}\nseq_num: {self.seq_num}\nACK_num: {self.ACK_num}\nACK_bit: {self.ACK_bit}\nSYN_bit: {self.SYN_bit}\nFIN_bit: {self.FIN_bit}\nreceive_window: {self.receive_window}\nchecksum_error: {self.checksum_error}\ndata: {self.data}"


def forward_packet(packet):
    filename = "{}.txt".format(packet.dest_port)
    with open(filename, "a") as f:
        f.write(str(packet))
        f.write("\n%%EOP\n\n")



def create_packets_from_network():
    packets = []
    with open(network, 'r+') as f:
        contents = f.read()
        if contents == "":
            return 0
        f.seek(0)
        lines = f.readlines()
        packet_info = {}
        data=""
        d_key=0
        for line in lines:
            line = line.strip()
            if line=="" or line=="\n":
                continue
            elif line.startswith("%%EOP"):
                packet_info["data"] = data.lstrip("data: ").rstrip('\n')
                packets.append(Packet(**packet_info))
                packet_info = {}
                data=""
                d_key=0
            elif d_key or line.startswith("data: "):
                d_key=1
                data+=line
                data+='\n'
                continue
            else:
                key, value = line.split(": ")
                if key!="data":
                    value=int(value)
                packet_info[key] = value
        f.seek(0)
        f.truncate(0)
    return packets



def create_single_packet_from_network():
    global network
    with open(network, 'r+') as f:
        contents = f.read()
        if contents == "":
            return 0
        f.seek(0)
        lines = f.readlines()
        packet_info = {}
        for line in lines:
            line = line.strip()
            if line=="" or line=="\n":
                continue
            elif line.startswith("%%EOP"):
                packet=Packet(**packet_info)
                packet_info = {}
                break
            else:
                key, value = line.split(": ")
                if key!="data":
                    value=int(value)
                packet_info[key] = value

        contents=contents[contents.find("%%EOP\n\n")+7:]
        f.seek(0)
        f.truncate()
        f.write(contents)
    return packet

def random_delay():
    x=random.random()
    if x < 0.01:
        return 10
    elif x<0.05:
        return 6
    elif x<0.2:
        return 3
    elif x<0.5:
        return 1
    else:
        return 0

def generate_packet_error():
    if random.random() < 0.1:
        return 1
    else:
        return 0


buffer=[]
for i in range(0,50):
    buffer.append(0)
    
network = "network.txt"
with open(network, "w") as f:
    f.write("")

while True:
    with open(network, "r+") as f:
        packets=create_packets_from_network()
        if packets!=0:
            for temp in packets:
                delay=random_delay()
                while buffer[delay]:
                    delay+=1
                temp.checksum_error=generate_packet_error()
                buffer[delay]=temp

    for a in buffer:
        if a==0:
            print(end=',')
        else:
            print(a.seq_num, end=',')
    print()
        
    packet=buffer[0]
    buffer.append(0)
    buffer=buffer[1:]
    if packet:
        forward_packet(packet)
        print()
        print()
        print(str(packet))
        print("전송 완료\n")
    time.sleep(0.1)
                

