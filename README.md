# Cogntiv Exercise

### Implementation Notes:

##### General

- The transport method implemented is a simple socket connection with a simple binary protocol.

##### Server

- Implemented 2 data producers:
    - the requested standard normal distribution producer and 
    - a test producer
for easy testing of the client functionality.
- Implemented server using asyncio TCP server
- Implemented 2 ways to keep a constant rate of 1000 Hz, selected using the `HIGH_ACCURACY` constant:
    - using simple `asyncio.sleep(delay)`. On windows this has resolution of ~16 milli-sec so it's not 
    fit for the required resolution.
    - using a busy loop with `asyncio.sleep(0)`.` This may consume more CPU but proved to be more accurate.
- known issue: exceptions are not propogated

##### Python Client

- Implemented again using asyncio TCP client.
- Implemented 2 ways of tracking the rate of data arrival, selected usng the `USE_ROLLING_RATE_TRACKER` constant:
    - Using a simple deque of the samples (not memory efficient)
    - Using a rolling stream calculation that uses O(1) memory
- Assumed the data arrival rate stats are reported at the same cadence as the vector data - every 100 samples.
- Results matrices in the client are not saved after the data analytics of a matrix was written to the output
- Output file is saved in the working directory to a csv file with lines of this format:  
  `<100 raw rate values>... ,<rate mean>,<rate std>,<50 mean values of data>... ,<50 std values of the data>...`
- the raw rate values are written to the output only if the simple deque tracker is being used since the rolling
  tracker does not save all the rates.
  
##### C++ client

- Implemented using boost::asio
- Implementation closely follows the Python client functionality
- Client "mobile device" consideration that were taken:
    - try to be as memory and CPU efficient as possible.
        - Best effort to do all memory allocation is done on startup
    - Handling an external signal that happens just before the process is killed to close the process in a graceful way
  
### Building

##### Windows: 

- Download boost and unzip somewhere, set the envar `BOOST_ROOT` to the root where boost is. 
No need to build boost binaries, only header lib is used.
- Visual Studio 2022 is required, some C++20 features are used
- Open cogntiv_cpp.sln in Visual Studio, build the project

##### Linux
TBA  
  
### Running

Server:  
```
> cd python
> python server_main.py [address] [port]
```

Python Client:
```
> cd python  
> python client_main.py [address] [port]
```

C++ Client
```
> cd cpp\x64_Debug
> cpp_client.exe [address] [port]
```

### Testing

- Tested on Windows with Python 3.11
- Tested on Linux with WSL2 with Python 3.10
- Tested with 3 concurrent clients with no reduced rate accuracy

Typical data arrival rate stats:
```
2023-04-23 23:58:21,417: data rate of last 100: 1009.89 Hz  std:131.99 Hz
2023-04-23 23:58:21,517: data rate of last 100: 1006.57 Hz  std:108.35 Hz
2023-04-23 23:58:21,618: data rate of last 100: 1002.72 Hz  std:97.00 Hz
2023-04-23 23:58:21,718: data rate of last 100: 1003.52 Hz  std:95.56 Hz
2023-04-23 23:58:21,819: data rate of last 100: 1009.57 Hz  std:133.04 Hz
```

- Tested manually that data stats are measured on the temporal axis using test data producer.
- Added unit-test for the 2 rate trackers to make sure they do the same thing.
- I tried using some socket options like `TCP_NODELAY`, `SO_SNDBUF` to make the networking 
faster and more predictable but that did not have any effect.

