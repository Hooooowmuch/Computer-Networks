from socket import *
import ssl
import base64

subject = input("请输入邮件主题：\n")
msg = input("请输入邮件内容：\n")
endmsg = "\r\n.\r\n"
# 配置邮件服务器和用户信息
mailserver = "smtp.qq.com" # SMTP 服务器地址，例如 smtp.qq.com
fromAddress = # 输入发件人邮箱地址
# 支持逗号分隔多个收件人，例如: a@example.com,b@example.com
toInput = input("请输入收件人邮箱地址（多个用逗号分隔）：\n")
# 解析收件人列表并去除空白
toAddresses = [addr.strip() for addr in toInput.split(',') if addr.strip()]

username = fromAddress  # 发件人邮箱地址作为用户名
password = # 邮箱授权码

# 创建客户端套接字并建立连接（明文连接到 587）
serverPort = 587
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((mailserver, serverPort))
recv = clientSocket.recv(2048).decode()
print(recv)
if recv[:3] != '220':
    print('220 reply not received from server.')

# 使用 EHLO
ehloCommand = 'EHLO local\r\n'
clientSocket.sendall(ehloCommand.encode())
recv1 = clientSocket.recv(2048).decode()
print(recv1)
if recv1[:3] != '250':
    print('250 reply not received from server.')

# 发送 STARTTLS，进入加密会话
clientSocket.sendall(b'STARTTLS\r\n')
recv_tls = clientSocket.recv(2048).decode()
print(recv_tls)
if recv_tls[:3] != '220':
    print('STARTTLS failed or not supported by server.')
else:
    # 将 socket 包装为 TLS
    context = ssl.create_default_context()
    clientSocket = context.wrap_socket(clientSocket, server_hostname=mailserver)

    # 在 TLS 上重新 EHLO
    clientSocket.sendall(ehloCommand.encode())
    recv_ehlo2 = clientSocket.recv(2048).decode()
    print(recv_ehlo2)

    # AUTH PLAIN：使用 base64 编码 \0username\0password
    auth_raw = '\0{0}\0{1}'.format(username, password).encode('utf-8')
    auth_b64 = base64.b64encode(auth_raw).decode('ascii')
    clientSocket.sendall(f'AUTH PLAIN {auth_b64}\r\n'.encode())
    recv2 = clientSocket.recv(2048).decode()
    print(recv2)
    if not (recv2.startswith('235') or recv2.startswith('334')):
        print('Authentication may have failed.')

    # 发送 MAIL FROM
    mailFromCommand = f'MAIL FROM:<{fromAddress}>\r\n'
    clientSocket.sendall(mailFromCommand.encode())
    recv3 = clientSocket.recv(2048).decode()
    print(recv3)

    # 对每个收件人发送 RCPT TO，并记录被服务器接受的地址
    accepted = []
    for addr in toAddresses:
        rcptCmd = f'RCPT TO:<{addr}>\r\n'
        clientSocket.sendall(rcptCmd.encode())
        resp = clientSocket.recv(2048).decode()
        print(resp)
        # 250/251 表示接受（251 是用户在本地的别名等）
        if resp.startswith('250') or resp.startswith('251'):
            accepted.append(addr)
        else:
            print(f'收件人 {addr} 被拒绝: {resp.strip()}')

    if not accepted:
        print('没有被接受的收件人，结束连接。')
        clientSocket.sendall(b'QUIT\r\n')
        print(clientSocket.recv(2048).decode())
    else:
        # 发送 DATA
        dataCommand = 'DATA\r\n'
        clientSocket.sendall(dataCommand.encode())
        recv5 = clientSocket.recv(2048).decode()
        print(recv5)

        # 构造符合 RFC 的邮件头，To 列出所有被接受的收件人
        headers = [
            f'From: {fromAddress}',
            'To: ' + ', '.join(accepted),
            f'Subject: {subject}',
            'MIME-Version: 1.0',
            'Content-Type: text/plain; charset="utf-8"',
            '',  # 头部和正文之间的空行
        ]
        message = '\r\n'.join(headers) + '\r\n' + msg + '\r\n'

        clientSocket.sendall(message.encode('utf-8'))
        clientSocket.sendall(endmsg.encode())
        recv6 = clientSocket.recv(2048).decode()
        print(recv6)

        quitCommand = 'QUIT\r\n'
        clientSocket.sendall(quitCommand.encode())
        recv7 = clientSocket.recv(2048).decode()
        print(recv7)
