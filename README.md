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

- Implemented using boost::asio for networking and fmt for logging
- External dependencies are found using simple environment variables. In a non-exercise code base a real package
  manager like conan should be used.
- Implementation closely follows the Python client functionality.
- Client "mobile device" consideration that were taken:
    - try to be as memory and CPU efficient as possible.
        - Best effort to do all memory allocation on startup.
    - Handling an external signal that happens just before the process is killed to close the process in a graceful manner.
  
### Building

- Install boost headers
    - Download from https://boostorg.jfrog.io/artifactory/main/release/1.82.0/source/boost_1_82_0.zip
    - unzip and set the envar `BOOST_ROOT` to the root of where it was unzipped  
    - No need to build boost binaries, only header lib is used.    
- Install fmt headers
    - Download from https://github.com/fmtlib/fmt/releases/download/9.1.0/fmt-9.1.0.zip
    - unzip and set envar `FMT_ROOT` to the root where it was unzipped    

##### Windows: 

- Visual Studio 2022 is required, some C++20 features are used.
- Open cogntiv_cpp.sln in Visual Studio, select a configuration, build the project.

##### Linux

- Install cmake if not already installed: `sudo apt install cmake` in Ubuntu
- Install g++-11 (For C++20), see https://lindevs.com/install-gcc-on-ubuntu
```
> sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
> sudo apt install -y g++-11
```
- Run the following commands from the project root:
```
> cd cpp
> mkdir build
> cd build
> cmake ..
> make
```
  
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

C++ Client Windows
```
> cd cpp\x64_Debug
> cpp_client.exe [address] [port]
```

C++ Client Linux
```
> cd cpp\build
> cpp_client [address] [port]
```


### Testing

- Tested on Windows with Python 3.11
- Tested on Linux with WSL2 with Python 3.10
- Tested with 3 concurrent clients with no reduced rate accuracy
- Tested the C++ client produces the same results as the Python client (up to the last 2 least significant digits)

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
- I tried playing with the server process priority to try to make the send rate more predictable
but that also had no effect.

