### Lab 6 Solution 

For this lab, Local and Same-Zone outputs were measured for 1000 repetitions. The average time per operation in ms is provided in Table 1 for each output using REST and gRPC. Different Region outputs were measured for 100 repetitions, and the average time is provided (Table 1). Additionally, for Local, Same-Zone and Different Region clients the basic latency using the `ping` command was measured and reported.

**Table 1.** 

| Method          | Local    | Same-Zone | Different Region |
| --------------- | -------- | --------- | ---------------- |
| REST add        | 2.6997   | 3.4219    | 262.2627         |
| gRPC add        | 0.6894   | 1.2047    | 118.8540         |
| REST rawimg     | 5.4294   | 17.9634   | 1044.9162        |
| gRPC rawimg     | 7.7657   | 14.2434   | 149.1883         |
| REST dotproduct | 3.0420   | 4.0175    | 267.4184         |
| gRPC dotproduct | 0.7568   | 1.0594    | 116.0066         |
| REST jsonimg    | 179.8279 | 59.3527   | 1092.3245        |
| gRPC jsonimg    | 18.5638  | 44.4825   | 160.2922         |
| PING            | 0.0500   | 0.4930    | 116.5570         |


We know from the class notes and our lab files that REST is likely to take longer when there are many repetitions because REST makes a new TCP connection for each request. For example, for the Local and Same-Zone tests we used 1000 repetitions. This means that REST issued 1000 HTTP requests for each operation. Conversely, gRPC maintains a persistent TCP connection for all queries. By keeping the communication channel open between the server and the client, we would expect gRPC to be faster than REST. In Table 1 we see that REST and gRPC performed as expected. In every case, under gRPC the tasks completed faster than under REST. We also see a pattern were the time increases from Local to Same-Zone for all outputs, and becomes much worse for Different Region. For example, adding takes 100 times longer for REST on Different Region, and over 170 times longer for gRPC. The time required for PING helps to explain this. Pinging the local machine took 0.05 ms on average, while pinging the Different Region machine took 116.56 ms, which reflects much higher network latency between regions. 






