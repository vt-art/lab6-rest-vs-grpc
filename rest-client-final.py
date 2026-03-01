#!/usr/bin/env python3

import requests
import json
import time
import sys
import base64
import jsonpickle
import random

def doRawImage(addr, debug=False):
    # prepare headers for http request
    headers = {'content-type': 'image/png'}
    img = open('Flatirons_Winter_Sunrise_edit_2.jpg', 'rb').read()
    # send http request with image and receive response
    image_url = addr + '/api/rawimage'
    response = requests.post(image_url, data=img, headers=headers)
    if debug:
        # decode response
        print("Response is", response)
        print(json.loads(response.text))

def doAdd(addr, debug=False):
    headers = {'content-type': 'application/json'}
    # send http request with image and receive response
    add_url = addr + "/api/add/5/10"
    response = requests.post(add_url, headers=headers)
    if debug:
        # decode response
        print("Response is", response)
        print(json.loads(response.text))

# doDotProduct:
# Builds two lists
# Sends them as JSON
# POST to /api/dotproduct
def doDotProduct(addr, debug=False):
    headers = {'content-type': 'application/json'}

    # Create two random vectors of 100-elements.
    size = 100
    # Creates lists
    a = [random.random() for _ in range(size)]
    b = [random.random() for _ in range(size)]

    # Matches the server’s expected keys.
    payload = {'a': a, 'b': b}

    dot_url = addr + "/api/dotproduct"
    
    # Using json=payload automatically converts it to JSON.
    response = requests.post(dot_url, json=payload, headers=headers)

    if debug:
        print("Response is", response)
        print(json.loads(response.text))

# doJsonImage
# Reads image bytes
# Converts to base64
# Sends JSON
def doJsonImage(addr, debug=False):
    headers = {'content-type': 'application/json'}

    # Read in the image file provided with the assignment
    img = open('Flatirons_Winter_Sunrise_edit_2.jpg', 'rb').read()

    # Convert to base64 string - Converts binary image bytes into 
    # ASCII-safe string format.
    # Turns bytes into a Python string so it can go into JSON.
    img_b64 = base64.b64encode(img).decode('utf-8')

    payload = {'image': img_b64}

    json_url = addr + "/api/jsonimage"
    response = requests.post(json_url, json=payload, headers=headers)

    if debug:
        print("Response is", response)
        print(json.loads(response.text))

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <server ip> <cmd> <reps>")
    print(f"where <cmd> is one of add, rawImage, sum or jsonImage")
    print(f"and <reps> is the integer number of repititions for measurement")

# The following block of code:
# - Chooses which RPC to test
# - Executes it N times
# - Reports average latency per request

# pull off the arguments that are passed when calling the program
# For example, python rest-client.py localhost add 1000 results in:
# sys.argv[0] = "rest-client.py"
# host = sys.argv[1] = "localhost"
# cmd = sys.argv[2] = "add" <- our endpoint of interest
# reps = sys.argv[3] = "1000" <- number of HTTP requests

host = sys.argv[1]
cmd = sys.argv[2]
reps = int(sys.argv[3])

# Build the address and print what is happening
addr = f"http://{host}:5000"
print(f"Running {reps} reps against {addr}")

# cmd == <- subsets by which output we are interested in
# start = time.perf_counter() <- starts timing the operation
# delta = ((time.perf_counter() - start)/reps)*1000 <- calculates
# the average amount of time in ms per request
# The lab instructions say to measure multiple queries because each
# query is fairly short. So, the timing may bounce around a little
# from query to query.
if cmd == 'rawImage':
    start = time.perf_counter()
    for x in range(reps):
        doRawImage(addr)
    delta = ((time.perf_counter() - start)/reps)*1000
    print("Took", delta, "ms per operation")
elif cmd == 'add':
    start = time.perf_counter()
    for x in range(reps):
        doAdd(addr)
    delta = ((time.perf_counter() - start)/reps)*1000
    print("Took", delta, "ms per operation")
elif cmd == 'jsonImage':
    start = time.perf_counter()
    for x in range(reps):
        doJsonImage(addr, debug=False)
    delta = ((time.perf_counter() - start)/reps)*1000
    print("Took", delta, "ms per operation")
elif cmd == 'dotProduct':
    start = time.perf_counter()
    for x in range(reps):
        doDotProduct(addr, debug=False)
    delta = ((time.perf_counter() - start)/reps)*1000
    print("Took", delta, "ms per operation")
else:
    print("Unknown option", cmd)


# NOTES: Run the code with these commands for each output
# python rest-client.py localhost add 1000 <-- Client and server running on the same machine.
# python rest-client.py localhost rawImage 100
# python rest-client.py localhost jsonImage 100
# python rest-client.py localhost dotProduct 1000