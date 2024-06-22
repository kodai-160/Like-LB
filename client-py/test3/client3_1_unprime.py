import grpc
import os
import time
import random
import pandas as pd
from isPrime import isPrime_pb2, isPrime_pb2_grpc

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["NO_PROXY"] = "192.168.100.2,192.168.100.3"

def generate_numbers(num_count):
    """処理が重い数と一桁の数字を交互に生成する"""
    numbers = []
    for i in range(num_count // 2):
        heavy = random.randint(1_000_000, 10_000_000)  # 処理が重い大きな数
        light = random.randint(0, 9)  # 処理が軽い一桁の数字
        numbers.extend([heavy, light])
    return numbers

def check_prime(server_address, number):
    """サーバーに素数判定をリクエストして、応答と処理時間を返す"""
    start_time = time.time()
    with grpc.insecure_channel(server_address) as channel:
        stub = isPrime_pb2_grpc.IsPrimeFuncStub(channel)
        response = stub.CheckPrime(isPrime_pb2.Value(Value=number))
    elapsed_time = time.time() - start_time
    return response.IsPrime, elapsed_time

def main():
    trials = 10
    numbers_per_trial = 100
    servers = ["192.168.100.2:9000", "192.168.100.3:9000"]
    all_trials_results = []

    for trial in range(trials):
        results = []
        numbers = generate_numbers(numbers_per_trial)
        for i, number in enumerate(numbers):
            server = servers[i % 2]
            is_prime, response_time = check_prime(server, number)
            results.append({
                "Trial": trial + 1,
                "Number": number,
                "IsPrime": 'T' if is_prime else 'F',
                "ResponseTime": response_time,
                "Server": server
            })
            print(f"Trial {trial + 1}, Number: {number}, Prime: {'T' if is_prime else 'F'}, Time: {response_time:.4f}s, Server: {server}")
        all_trials_results.extend(results)

    df = pd.DataFrame(all_trials_results)
    average_response_times = df.groupby(['Trial', 'Server'])['ResponseTime'].mean().reset_index()
    with pd.ExcelWriter('prime_checks_interleaved_heavy_light.xlsx') as writer:
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        average_response_times.to_excel(writer, sheet_name='Average Response Times', index=False)

if __name__ == "__main__":
    main()
