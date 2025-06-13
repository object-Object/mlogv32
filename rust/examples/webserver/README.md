# webserver

Runs a simple webserver using [Embassy](https://embassy.dev/) and [picoserve](https://docs.rs/picoserve/latest/picoserve/).

Steps:

- Set up the processor and memory as per the `src/config/webserver.mlog` config.
- Start the mlogv32-utils socket server.
- Create a file called `config` with the following contents:

  ```
  192.168.7.1:192.168.7.10
  ms-dns 8.8.4.4
  ms-dns 8.8.8.8
  nodetach
  debug
  local
  persist
  silent
  noproxyarp
  noauth
  socket 127.0.0.1:5000
  connect "echo '{\"type\":\"serial\",\"device\":\"uart1\",\"stopOnHalt\":false,\"overrun\":false}'"
  ```

- Run each of these commands in separate terminals (tested on WSL2 with [mirrored mode networking](https://learn.microsoft.com/en-us/windows/wsl/networking#mirrored-mode-networking)):

  ```sh
  # connect pppd to uart1
  sudo pppd 38400 file config

  # forward requests from localhost port 8080 to mlogv32 port 8080
  socat -v tcp-listen:8080,reuseaddr,fork tcp:192.168.7.10:8080
  ```

- Build and flash this program to mlogv32, then start the processor.
- Visit http://localhost:8080.
