import grpc
import os
import time
import pandas as pd
from isPrime import isPrime_pb2, isPrime_pb2_grpc

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["NO_PROXY"] = "192.168.100.2,192.168.100.3"

def generate_fixed_number(num_count, fixed_number):
    """固定された数を含むリストを生成する"""
    return [fixed_number] * num_count

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
    numbers_per_trial = 50
    servers = ["192.168.100.2:9000", "192.168.100.3:9000"]
    fixed_number = 100000000000031  # 15桁の素数
    all_trials_results = []

    for trial in range(trials):
        results = []
        numbers = generate_fixed_number(numbers_per_trial, fixed_number)
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
    with pd.ExcelWriter('prime_checks_fixed_number15-1.xlsx') as writer:
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        average_response_times.to_excel(writer, sheet_name='Average Response Times', index=False)

if __name__ == "__main__":
    main()
