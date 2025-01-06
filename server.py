import time
import random
import textwrap

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
        
def create_packets_from_file(filename):
    packets = []
    with open(filename, 'r+') as f:
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

def create_single_packet_from_file(filename):
    with open(filename, 'r+') as f:
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
                packet=(Packet(**packet_info))
                packet_info = {}
                break
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

        contents=contents[contents.find("%%EOP\n\n")+7:]
        f.seek(0)
        f.truncate()
        f.write(contents)
    return packet


def send_packet(packet):
    global sent_time, seq_num
    filename = "network.txt"
    with open(filename, "a") as f:
        f.write(str(packet))
        f.write("\n%%EOP\n\n")
    sent_time[seq_num] = time.time()

def threeway_first():
    global source_port, dest_port, timer, seq_num, max_buffer
    packet=Packet(source_port, dest_port, seq_num, 0, 0, 1, 0, max_buffer, 0, "%%%")
    send_packet(packet)
    timer=time.time()+timeout_sec
    print("3way hanshake: 1단계 완료")

def generate_packet_error():
    if random.random() < 0.4:
        return 1
    else:
        return 0

def move_window(need_for_ACK):
    #print("무빙", end='')
    global last_ACK, send_buffer, send_buffer_size, storage
    if len(send_buffer)==0 or last_ACK>send_buffer[0][0].seq_num:
        while len(send_buffer) and last_ACK>send_buffer[0][0].seq_num:
            send_buffer=send_buffer[1:]
        while len(send_buffer)<send_buffer_size:
            #print("루핑", end='')
            #print(storage["send"])
            if len(storage["send"]):
                send_buffer.append([storage["send"][0], time.time()+timeout_sec])
                send_packet(send_buffer[-1][0])
                storage["send"]=storage["send"][1:]
            elif need_for_ACK:
                packet=Packet(source_port, dest_port, -1, received_seq+data_len, 1, 0, 0, receive_buffer_size, 0, "%%%")
                send_packet(packet)
                break
            else:
                break
    elif need_for_ACK:
        packet=Packet(source_port, dest_port, -1, received_seq+data_len, 1, 0, 0, receive_buffer_size, 0, "%%%")
        send_packet(packet)
                

def make_data():
    global source_port, dest_port, seq_num, received_seq, receive_buffer_size, data_len
    
    with open("server_input.txt", 'r+') as f:
        contents = f.read()
        if contents == "":
            return 0
        f.seek(0)
        f.truncate(0)
        
    s=contents+"%%EOD"
    #print("s: ", s)
    wrapped=textwrap.wrap(s,data_len)

    for i, data in enumerate(wrapped):
        seq_num+=data_len
        packet=Packet(source_port, dest_port, seq_num, received_seq+data_len, 1, 0, 0, receive_buffer_size, 0, data)
        packet.data = packet.data.ljust(data_len, "%")
        print("패킷 전송, data: {} seq={}".format(packet.data, packet.seq_num))
        storage["send"].append(packet)
    print()


def receive_packet():
    #print("리시빙", end='')
    global source_file, last_ACK, received_seq, data_len, receive_buffer, receive_buffer_size, receive_buffer_blank, storage
    packet = create_single_packet_from_file(source_file)
    if packet==0:
        return 0
    if packet.checksum_error:
        return 0

    if last_ACK==packet.ACK_num and len(send_buffer):
        #print("(dup_ACK)retransmission occured!: seq={}".format(send_buffer[0][0].seq_num))
        retransmission()
        
    last_ACK = max(last_ACK, packet.ACK_num)
    if packet.seq_num==-1:
        return 0

    #print(str(packet))
    #packet.data = packet.data.ljust(data_len, "%")
    start_index = packet.seq_num-(received_seq + data_len)
    if 0 <= start_index <= receive_buffer_size-data_len:
        if receive_buffer[start_index]==0:
            del receive_buffer[start_index:start_index+data_len]
        receive_buffer = receive_buffer[:start_index] + list(packet.data) + receive_buffer[start_index:]
        receive_buffer = receive_buffer[:receive_buffer_size]


    i=0
    for c in receive_buffer:
        if c:
            storage["receive"]+=c
            receive_buffer=receive_buffer[1:]
            receive_buffer.append(0)
            i+=1
            #print("c",c)
        else:
            break
    if i:
        print()
        print("receive_storage:",storage["receive"])
        print("receive_buffer:",receive_buffer)
        print()
    received_seq += i
    return packet

def timecheck():
    global send_buffer
    if len(send_buffer):
        if send_buffer[0][1] < time.time():
            #print("(timeout)retransmission occured!: seq={}".format(send_buffer[0][0].seq_num))
            retransmission()
            send_buffer[0][1]+=timeout_sec

def retransmission():
    global send_buffer, received_seq, data_len
    if len(send_buffer):
        send_buffer[0][0].ACK_num=received_seq+data_len
        send_packet(send_buffer[0][0])
    

def write_str(string):
     with open("server_input.txt", "a") as f:
        f.write(string)


source_port=50
dest_port=80
seq_num=70
last_ACK=0
received_seq=0
receive_buffer_size=15
receive_buffer=[]
receive_buffer_blank=[]
send_buffer_size=2
send_buffer=[[]]
storage={"receive":"","send":[]}
timer=0
timeout_sec=10
sent_time={}
data_len=5
source_file = "{}.txt".format(source_port)


with open(source_file, "w") as f:  #포트에 대한 txt 파일 생성
    f.write("")
with open("server_input.txt", "w") as f:
    f.write("")
for i in range(0,receive_buffer_size):
    receive_buffer.append(0)


while True:
    with open(source_file, "r") as f:
            temp=create_packets_from_file(source_file)
            if temp:
                if temp[0].SYN_bit==1:
                    received_seq = temp[0].seq_num
                    print("3way hanshake: SYN 수신 완료")
                    print("seq_num of client: {}".format(received_seq))
                    break
                else:
                    continue

while True:
    timer=time.time()+timeout_sec
    packet=Packet(source_port, dest_port, seq_num, received_seq+data_len, 1, 1, 0, receive_buffer_size, 0, "%%%")
    send_buffer[0]=[packet,time.time()+timeout_sec]
    send_packet(packet)
    print("3way hanshake: SYNACK 전송 완료")
    while True:
        '''
        temp=create_packets_from_file(source_file)
        if temp and temp[0].SYN_bit==0:
            if temp[0].checksum_error==1:
                temp=temp[1:]
                continue
            received_seq=temp[0].seq_num-data_len
            '''
        packet=receive_packet()
        if packet!=0:
            
            #packet=Packet(source_port, dest_port, -1, received_seq+data_len, 1, 0, 0, receive_buffer_size, 0, "%%%")
            #send_packet(packet)
            break
        if timer-time.time()<0:
            break
    if timer-time.time()<0:
        print("TimeOut!\n")
        continue
    break



dic = {}


write_str("%")
while True:
    time.sleep(1)
    make_data()
    move_window(receive_packet())
    timecheck()

    i=storage["receive"].find("%%EOD")
    if i != -1:
        command=storage["receive"][0:i]
        storage["receive"]=storage["receive"][i+5:]
        command = command.replace("%","")
        if command=="":
            continue
        print("==============================================================")
        print("from client:", command)
        print("==============================================================\n")
        command = command.split(',')



        if command[0]=="PUT":
            # PUT 명령어 처리
            dic[command[1]] = command[2]    # 딕셔너리에 데이터 추가
            write_str("Success!")    # 클라이언트에게 결과 전송

        elif command[0]=="GET":
            # GET 명령어 처리
            if command[1] in dic:    # 딕셔너리에 데이터가 있는 경우
                write_str(dic[command[1]])    # 클라이언트에게 결과 전송
            else:    # 딕셔너리에 데이터가 없는 경우
                write_str("Not exist!")    # 클라이언트에게 결과 전송

        elif command[0]=="DELETE":
            # DELETE 명령어 처리
            if command[1] in dic:    # 딕셔너리에 데이터가 있는 경우
                del dic[command[1]]    # 딕셔너리에서 데이터 삭제
                write_str("Success!")    # 클라이언트에게 결과 전송
            else:    # 딕셔너리에 데이터가 없는 경우
                write_str("Not exist!")    # 클라이언트에게 결과 전송

        elif command[0]=="LIST":
            # LIST 명령어 처리
            if len(dic)==0:    # 딕셔너리가 비어 있는 경우
                write_str("Not exist!")    # 클라이언트에게 결과 전송
            else:    # 딕셔너리에 데이터가 있는 경우
                list_str=""    # 리스트 문자열 초기화
                for k, v in dic.items():    # 딕셔너리의 모든 아이템에 대해 반복
                    list_str += "[{},{}], ".format(k,v)    # 리스트 문자열에 아이템 추가
                write_str(list_str)    # 클라이언트에게 결과 전송
        else:
            # 예외 처리
            write_str("command error.")    # 클라이언트에게 결과 전송

