#!/usr/bin/env python3

from concurrent import futures
import time
import base64
import io

import grpc
from PIL import Image

import grpc_service_pb2
import grpc_service_pb2_grpc

# To generate the files from the .proto file, ran:
# python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. grpc_service.proto


class gRPCService(grpc_service_pb2_grpc.gRPCServiceServicer):
    def Add(self, request, context):
        # request.a and request.b are int32
        s = request.a + request.b
        return grpc_service_pb2.addReply(sum=s)

    def RawImage(self, request, context):
        # request.img is bytes
        try:
            io_buf = io.BytesIO(request.img)
            img = Image.open(io_buf)
            width, height = img.size
        except Exception:
            width, height = 0, 0

        return grpc_service_pb2.imageReply(width=width, height=height)

    def DotProduct(self, request, context):
        # request.a and request.b are repeated float
        try:
            a = list(request.a)
            b = list(request.b)

            if len(a) != len(b):
                dp = 0.0
            else:
                dp = 0.0
                for x, y in zip(a, b):
                    dp += float(x) * float(y)
        except Exception:
            dp = 0.0

        return grpc_service_pb2.dotProductReply(dotproduct=dp)

    def JsonImage(self, request, context):
        # request.img is a base64 string (for consistency with REST jsonimage)
        try:
            img_bytes = base64.b64decode(request.img)
            io_buf = io.BytesIO(img_bytes)
            img = Image.open(io_buf)
            width, height = img.size
        except Exception:
            width, height = 0, 0

        return grpc_service_pb2.imageReply(width=width, height=height)

# REST uses port 5000. gRPC typically uses 50051
def serve(host="0.0.0.0", port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grpc_service_pb2_grpc.add_gRPCServiceServicer_to_server(gRPCServiceServicer(), server)

    server.add_insecure_port(f"{host}:{port}")
    server.start()
    print(f"gRPC server listening on {host}:{port}")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop(0)


if __name__ == "__main__":
    serve()