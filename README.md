# Cogntiv Exercise

### Implementation notes:

##### General

- The transport method implemented is a simple socket connection with a simple binary protocol
- "Mobile device" consideration that were taken is to try to be as memory and CPU efficient as possible

##### Server

- Implemented 2 data producers, the requested standard normal distribution producer and a test producer
for easy testing of the client functionality.
- Implemented server using asyncio TCP server
- Implemented 2 ways to keep a constant rate of 1000 Hz, selected using the `HIGH_ACCURACY` constant
    - using simple asyncio.sleep(delay). On windows this has resolution of ~16 milli-sec so it's not 
    for the required resolution
    - using a busy loop with asyncio.sleep(0). This may consume more CPU but proved to be more accurate

##### Client

- Implemented again using asyncio TCP client
- Implemented 2 ways of tracking the rate of data arrival
    - Using a simple deque of the samples (not memory efficient)
    - Using a rolling stream calculation that uses O(1) memory
- Assumed the data arrival rate stats are reported at the same cadence as the vector data - every 100 samples
- Output to a csv file of this format:  
  `<rate mean>,<rate std>,<50 mean values of data>... ,<50 std values of the data>...`

### Running

Server:  
`python server_main.py [address] [port]`

Client:  
`python client_main.py [address] [port]`

### Testing

- Tested on Windows with Python 3.11
- Tested on Linux with WSL2 with Python 3.10

Typical data arrival rate stats:
```
2023-04-23 23:58:21,417: data rate of last 100: 1009.89 Hz  std:131.99 Hz
2023-04-23 23:58:21,517: data rate of last 100: 1006.57 Hz  std:108.35 Hz
2023-04-23 23:58:21,618: data rate of last 100: 1002.72 Hz  std:97.00 Hz
2023-04-23 23:58:21,718: data rate of last 100: 1003.52 Hz  std:95.56 Hz
2023-04-23 23:58:21,819: data rate of last 100: 1009.57 Hz  std:133.04 Hz
```

- Tested manually using test data producer to make sure data stats are on the temporal axis
- Added unit-test for the 2 rate trackers to make sure they do the same thing 

- I tried using some socket options like `TCP_NODELAY`, `SO_SNDBUF` to make the networking 
faster and more predictable but that did not have any effect

