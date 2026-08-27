# DTU 透传桥接器

使用 Python 创建 TCP 服务端，接收通过 4G 网络透传过来的 DTU 数据，并可通过同一 TCP 连接发送数据。DTU 的现场串口和波特率由 DTU 设备自身配置，本程序不需要设置 `baudrate`。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

## 运行

主程序作为 TCP 服务端，DTU 通过 4G 主动连接服务器。监听全部网卡：

```bash
python main.py --tcp-port 9000
```

请将 DTU 的 4G 网络目标地址设置为服务器公网 IP 或域名、目标端口设置为 `9000`，并在云服务器安全组和系统防火墙放行该 TCP 端口。

DTU 建立连接后，第一段数据必须是 ASCII 格式的 15 位 IMEI，并通过 Luhn 校验；校验失败会拒绝连接。注册成功后，业务数据会以十六进制写入日志。程序不解析其他 DTU 厂商协议，不添加帧头、校验或换行符；业务程序可调用 `DtuTcpServer.send(data)` 向当前 DTU 发送原始字节。

## 测试

```bash
pytest -q
```