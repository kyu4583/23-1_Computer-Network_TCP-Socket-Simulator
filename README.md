# 자체 추가 과제: TCP 프로토콜 구현

기존 과제에서 요구하지 않았지만, Socket 라이브러리 없이 직접 TCP 프로토콜의 동작을 Low-Level에서 구현해보고 싶었다.

## 개요

TCP의 동작 방식을 재현하는 게 목적이기에, 실제로 네트워크 통신을 할 필요까지는 없다.

그저 서버와 클라이언트가 어떤 방식이 되었든 패킷 구조체를 주고받고, unreliable한 요소를 인위적으로 부여할 수만 있으면 된다.

txt 파일을 읽고 쓰는 방식이 어려운 개념이 없고 ‘파이썬 프로그래밍’ 강의에서 다룬 적이 있기에 이 방식을 채택했다.

서버와 클라이언트는 각각 별도의 Python 파일(server.py, client.py)로 구성되며, 전송 딜레이와 패킷 에러를 부여하여 서버와 클라이언트로 패킷을 포워딩하는 network.py, 클라이언트에게 사용자 입력을 전달하는 client_input.py가 같이 실행된다.

서버와 클라이언트는 각각 배정된 txt파일에 패킷 정보를 저장하고 불러올 것이다. 규격은 다음과 같다.

<img src="https://github.com/user-attachments/assets/1a6fc048-e6d0-4255-9a5b-81af072d6576" width="450" height="300">

문단마다 새그먼트를 구성하는 정보들이 적혀있고, `'%%EOP'`를 통해 어디까지가 하나의 객체인지를 표시한다. 위의 두 패킷은 예시로 작성되었다.

## 동작 설명

- server.py
  - client와 `3way-handshaking`을 가지고, network.py로부터 전달되는 `packet 객체`를 읽는다.
  - receive_buffer에 읽은 객체를 넣고 관리하며, `seq_num`과 `ACK_num`을 통해 **패킷 손실을 추적**한다. 받은 패킷에 대해 ACK packet을 클라이언트쪽으로 송신하며, 이때 send_buffer가 사용된다.
  - `‘selective repeat’ 방식`을 채택하여 **pipeline이 구현**되었고, **모든 데이터가 상대방 측에 성공적으로 전송**되도록 한다.
  - ACK은 `‘누적 ACK’ 방식`을 따른다.
  - 송신하려는 데이터 문자열은 **길이 `5`의 작은 여러개의 문자열로 나뉘고**, 각각 **`헤더`를 입히고** **`패킷`으로 만들어** network.py에 전달(송신)한다.
  - 주고받은 데이터를 통해 기존 과제의 방식에서 구현한 코드와 같이 명령어에 따라 딕셔너리를 관리하는 동작을 한다.
 
- client.py
  - server.py와 대체로 유사하게 구현되었다.
  - 3way-handshaking을 할 때의 역할이 server.py와 가장 다른 점이다.

- client_input.py
  - 클라이언트가 사용자로부터 입력을 대기하고 있으면 다른 역할을 못하기에, client_input.py가 txt파일에 사용자 입력을 저장해두면 client.py가 루프를 도는 중간에 읽어오도록 했다.

- network.py
  - 서버와 클라이언트로부터 송신되는 패킷을 전달받아, dest_port를 참조하여 목적지로 포워딩한다.
  - **무작위로 패킷의 도착 순서가 섞이도록** 한다.
  - **무작위로 패킷의 데이터 변질 에러를 만들어낸다.**

## 실행 결과

사진 상의 좌측부터 network.py, server.py, client.py, client_input.py가 실행중이다.
network.py, server.py, client.py는 좌측부터 정렬된 순서대로 실행 해야 한다.

### 첫 번째 입력(PUT):
![image](https://github.com/user-attachments/assets/885f0a1b-0c6f-4855-9d88-58808be0087a)

### 두 번째 입력(PUT):
![image](https://github.com/user-attachments/assets/4a6ae480-36a4-44ab-8513-d4594f83ebcc)

### 세 번째 입력(PUT):
![image](https://github.com/user-attachments/assets/8c85553b-1115-4179-8e98-60f8f73df55c)

### 네 번째 입력(GET):
![image](https://github.com/user-attachments/assets/e2da34ed-bed6-429d-912d-8e00a7937154)

### 다섯 번째 입력(DELETE):
![image](https://github.com/user-attachments/assets/e635e204-8464-40b7-b01f-6db9fe7ba196)

### 여섯 번째 입력(LIST):
![image](https://github.com/user-attachments/assets/0afa4a53-cf15-43d4-86a8-0c44ce5b117e)

### 일곱 번째 입력(예외 입력):
![image](https://github.com/user-attachments/assets/efadebf0-cd86-49f6-b87d-4fc2e9810304)

## 개선할 점

txt파일을 읽고 쓰는 방식이 속도나 안정성 측면에서 비효율적이다. 여러 프로세스가 읽고 쓰는 시간이 겹치면 대량 패킷 손실로 이어지기에 동작 시간을 늦출 수밖에 없었다. 공유 메모리와 같은 방식을 썼더라면 더 빠르고 안정적인 프로그램이 되었을 수 있다.
