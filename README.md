# 자체 추가 과제: TCP 프로토콜 구현

기존 과제에서 요구하지 않았지만, `Socket 라이브러리` 없이 직접 TCP 프로토콜의 동작을 Low-Level에서 구현해보고 싶어 시도했다.

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
  - `client`와 `3way-handshaking`을 가지고, `network.py`로부터 전달되는 `packet 객체`를 읽는다.
  - `receive_buffer`에 읽은 객체를 넣고 관리하며, `seq_num`과 `ACK_num`을 통해 **패킷 손실을 추적**한다. 받은 패킷에 대해 `ACK packet`을 클라이언트쪽으로 송신하며, 이때 `send_buffer`가 사용된다.
  - `‘selective repeat’ 방식`을 채택하여 **`pipeline`이 구현**되었고, **모든 데이터가 상대방 측에 성공적으로 전송**되도록 한다.
  - ACK은 `‘누적 ACK’ 방식`을 따른다.
  - 송신하려는 데이터 문자열은 **길이 `5`의 작은 여러개의 문자열로 나뉘고**, 각각 **`헤더`를 입히고** **`패킷`으로 만들어** `network.py`에 전달(송신)한다.
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

- 클라이언트와 서버가 구동 직후 `3-way-handshake`를 수립했다.
- 클라이언트에 입력한 문자열이 `5` 길이의 작은 단위로 쪼개져 각각 패킷이 되었다.
- 먼저 도착했어야 할 `"yname"` 문자열보다 `",sung"` 문자열이 서버에 먼저 도착했다.
  - 이는 `"yname"` 패킷의 `checksum_error`가 감지됐거나
  - `"yname"` 패킷 자체가 유실되었거나
  - 네트워크 상에서 순서가 엉켰거나
  이들 중 하나의 경우에 해당함을 의미한다.
  1. `"yname"` 패킷의 `checksum_error`가 감지됐을 경우:
      1. `checksum_error`가 감지된 패킷을 버린다.
      2. `",sung"` 문자열은 버퍼에서 대기한다.
      3. 클라이언트는 ACK이 돌아오지 않음으로써 타임아웃을 감지하고, 패킷을 재전송한다.
      4. 이후 올바른 `"yname"` 문자열이 도착했을 때, 버퍼 내의 `",sung"` 문자열과 함께 올바른 순서로 결과물에 더해진다.
  2. `"yname"` 패킷이 유실되었을 경우:
      1. `",sung"` 문자열은 버퍼에서 대기한다.
      2. 클라이언트는 ACK이 돌아오지 않음으로써 타임아웃을 감지하고, 패킷을 재전송한다.
      3. 이후 재전송된 `"yname"` 문자열이 도착했을 때, 버퍼 내의 `",sung"` 문자열과 함께 올바른 순서로 결과물에 더해진다.
  3. 네트워크 상에서 순서가 엉켰을 경우:
      1. 먼저 도착한 `",sung"` 문자열은 버퍼에서 대기한다.
      2. 나중에 도착한 `"yname"` 문자열이 오면, seq_num을 확인하여 올바른 순서를 파악한다.
      3. 버퍼에 저장된 `",sung"` 문자열과 함께 올바른 순서로 결과물에 더해진다.
      4. 이 경우는 패킷 손실이나 에러가 없었기 때문에 재전송은 발생하지 않는다.

- 클라이언트가 보낸 데이터가 모두 완성되자(EOF 문자 감지), 서버가 이에 대해 해석하고 그 응답으로 "Success!" 문자열을 전송했다.

뒤의 실행 결과들에서도 위와 동일한 방식으로, 모든 경우에서 receive_buffer를 통해 순서가 맞지 않는 패킷들을 임시 저장하고, 올바른 순서의 패킷이 도착했을 때 함께 처리함으로써 데이터의 순서를 보장한다.

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
