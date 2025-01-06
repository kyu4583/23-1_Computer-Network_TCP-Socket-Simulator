with open("client_input.txt", "w") as f:
    f.write("")


while True:
    
    s=input("전송할 데이터를 입력하세요: ")

    with open("client_input.txt", "a") as f:
        f.write(s)

