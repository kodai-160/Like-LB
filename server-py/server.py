from concurrent import futures
import grpc
import isPrime.isPrime_pb2 as isPrime_pb2
import isPrime.isPrime_pb2_grpc as isPrime_pb2_grpc


class IsPrimeFuncServicer(isPrime_pb2_grpc.IsPrimeFuncServicer):
    def CheckPrime(self, request, context):
        number = request.Value
        print(number)
        # 素数判定アルゴリズム
        if number > 1:
            for i in range(2, int(number**0.5) + 1):
                if (number % i) == 0:
                    return isPrime_pb2.IsPrimeResponse(IsPrime=False)
            return isPrime_pb2.IsPrimeResponse(IsPrime=True)
        return isPrime_pb2.IsPrimeResponse(IsPrime=False)


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)  # 最大10スレッドで動作
    )
    isPrime_pb2_grpc.add_IsPrimeFuncServicer_to_server(IsPrimeFuncServicer(), server)
    server.add_insecure_port("[::]:9000")  # 暗号化してない
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    print("Python gRPC Prime judgement server!")
    serve()
