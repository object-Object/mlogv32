# ppp

Based on the example in https://github.com/embassy-rs/ppproto/blob/bd16b3093fe2ededb4fd7662ed253d7bc6b39a9b/README.md.

Steps:

- Start the mlogv32-utils socket server.
- Run each of the following commands in a separate terminal (replace `127.0.0.1` with your [host ip](https://learn.microsoft.com/en-us/windows/wsl/networking#accessing-windows-networking-apps-from-linux-host-ip) if using WSL):

  ```sh
  # show log output from uart0
  echo '{"type":"serial","device":"uart0","stopOnHalt":false}' | netcat -v 127.0.0.1 5000

  # relay socket server to pty
  socat -v -x TCP4:127.0.0.1:5000 PTY,link=pty,rawer

  # connect pppd to uart1
  sudo pppd $PWD/pty 9600 192.168.7.1:192.168.7.10 ms-dns 1.1.1.1 ms-dns 1.0.0.1 connect "echo '{\"type\":\"serial\",\"device\":\"uart1\"}'" nodetach debug local persist silent noproxyarp noauth
  ```

- Build and flash this program to mlogv32, then start the processor.
- Run `ping 192.168.7.10` to ping the processor.
