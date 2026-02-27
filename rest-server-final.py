#!/usr/bin/env python3

## REST == Representational State Transfer
## Started with provided rest-server.py code
## Updated the blocks below for 
## @app.route('/api/dotproduct', methods=['POST'])
## @app.route('/api/jsonimage', methods=['POST'])

##
## Sample Flask REST server implementing two methods
##
## Endpoint /api/image is a POST method taking a body containing an image
## It returns a JSON document providing the 'width' and 'height' of the
## image that was provided. The Python Image Library (pillow) is used to
## process the image
##
## Endpoint /api/add/X/Y is a post or get method returns a JSON body
## containing the sum of 'X' and 'Y'. The body of the request is ignored
##
##
from flask import Flask, request, Response
import jsonpickle
from PIL import Image # Using pillow
import base64
import io

# Initialize the Flask application
app = Flask(__name__)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

@app.route('/api/add/<int:a>/<int:b>', methods=['GET', 'POST'])
def add(a,b):
    response = {'sum' : str( a + b)}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")

# route http posts to this method
@app.route('/api/rawimage', methods=['POST'])
def rawimage():
    r = request
    # convert the data to a PIL image type so we can extract dimensions
    try:
        ioBuffer = io.BytesIO(r.data)
        img = Image.open(ioBuffer)
    # build a response dict to send back to client
        response = {
            'width' : img.size[0],
            'height' : img.size[1]
            }
    except:
        response = { 'width' : 0, 'height' : 0}
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")

# @app.route(...) is the decorator. It tells Flask - when a request comes to /api/dotproduct
# using POST, run this function.
@app.route('/api/dotproduct', methods=['POST'])
# def dotproduct() is the function that handles the request.
def dotproduct():
    try:
        # request is the incoming HTTP request - expects JSON body.
        # .get_json() parses the body as JSON and returns it as a Python dict.
        # force=True means “try to parse JSON even if the Content-Type header 
        # isn’t set to application/json”
        # Pull out the two vectors from the JSON body.
        # If the keys don’t exist, .get() returns None.
        data = request.get_json(force=True)  
        a = data.get('a')
        b = data.get('b')

        # basic validation - both a and b must be Python lists of the same length
        # If validation fails, we return a JSON response with dotproduct = 0 and an error message.        
        if not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b):
            response = {'dotproduct': 0, 'error': 'a and b must be lists of same length'}
        else:
            # compute dot product (cast to float to handle ints/floats)
            # zip(a, b) pairs up elements: (a[0], b[0]), (a[1], b[1]), ...
            # For each pair, multiply them: float(x) * float(y)
            # sum(...) adds them all up → dot product.
            # We return the dot product in response.
            dp = sum(float(x) * float(y) for x, y in zip(a, b))
            response = {'dotproduct': dp}

    except Exception as e:
        response = {'dotproduct': 0, 'error': str(e)}

    # Convert the Python dict to a JSON string using jsonpickle.
    response_pickled = jsonpickle.encode(response)
    # Build the HTTP response
    return Response(response=response_pickled, status=200, mimetype="application/json")

# This endpoint listens for POST requests at /api/jsonimage.
@app.route('/api/jsonimage', methods=['POST'])
def jsonimage():
    try:
        # Parse the request body JSON into a Python dict.
        data = request.get_json(force=True)

        # Pull out the field named "image" from the JSON body.
        # We expect it to be a base64-encoded string of the JPG bytes - 
        # something like: {"image": "<base64_string>"}
        b64 = data.get('image')

        # Validate that the "image" field exists and is a string.
        #If it isn’t, return width/height = 0 and an error message.
        if not isinstance(b64, str):
            response = {'width': 0, 'height': 0, 'error': 'missing "image" base64 string'}

        # Convert the base64 string back into raw bytes (the actual JPG file bytes).
        # io.BytesIO() wraps the raw bytes in an in-memory “file-like object”.
        # Python Image Library (PIL) replaced with pillow, but still called PIL
        # PIL's Image.open() expects a file path or a file-like object.
        else:
            img_bytes = base64.b64decode(b64)
            ioBuffer = io.BytesIO(img_bytes)
            img = Image.open(ioBuffer) # PIL reads the image from the in-memory buffer and 
                                       # creates an Image object.
            # After the image is loaded read its dimensions.
            response = {
                'width': img.size[0],
                'height': img.size[1]
            }

    except Exception as e:
        response = {'width': 0, 'height': 0, 'error': str(e)}

    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")

# start flask app. REST uses port 5000
app.run(host="0.0.0.0", port=5000)