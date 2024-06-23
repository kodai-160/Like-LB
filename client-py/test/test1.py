import grpc
import os
import time
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from random import randint, seed
from itertools import cycle
from isPrime import isPrime_pb2, isPrime_pb2_grpc

# gRPCのログレベルを設定
os.environ["GRPC_VERBOSITY"] = "NONE"

def generate_random_numbers(num_count, random_seed):
    """10桁から11桁の疑似乱数を生成する"""
    seed(random_seed)  # シード値を設定
    return [randint(10**9, 10**11 - 1) for _ in range(num_count)]

def check_prime(server_address, number):
    """サーバーに素数判定をリクエストして、応答と処理時間を返す"""
    start_time = time.time()
    try:
        with grpc.insecure_channel(server_address) as channel:
            stub = isPrime_pb2_grpc.IsPrimeFuncStub(channel)
            response = stub.CheckPrime(isPrime_pb2.Value(Value=number))
        elapsed_time = time.time() - start_time
        return response.IsPrime, elapsed_time
    except grpc.RpcError as e:
        print(f"RPC Error: {e}")
        elapsed_time = time.time() - start_time
        return 'Error', elapsed_time

def process_numbers(servers, numbers, trial):
    """特定のトライアル用の番号リストを処理する"""
    results = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        server_cycle = cycle(servers)
        future_to_number = {executor.submit(check_prime, server, number): (server, number) for server, number in zip(server_cycle, numbers)}
        for future in as_completed(future_to_number):
            server, number = future_to_number[future]
            try:
                is_prime, response_time = future.result()
                results.append({
                    "Trial": trial,
                    "Number": number,
                    "IsPrime": 'T' if is_prime == True else 'F' if is_prime == False else 'Error',
                    "ResponseTime": response_time,
                    "Server": server
                })
                print(f"Trial {trial}, Number: {number}, Prime: {'T' if is_prime == True else 'F' if is_prime == False else 'Error'}, Time: {response_time:.4f}s, Server: {server}")
            except Exception as e:
                print(f"Trial {trial}, Number: {number}, Error: {e}")
                results.append({
                    "Trial": trial,
                    "Number": number,
                    "IsPrime": 'N/A',
                    "ResponseTime": 'N/A',
                    "Server": server
                })
    return results

def main():
    parser = argparse.ArgumentParser(description="Run prime number checks with a gRPC server.")
    parser.add_argument('trials', type=int, help="Number of trials to run.")
    parser.add_argument('numbers_per_trial', type=int, help="Number of numbers to check per trial.")
    parser.add_argument('ip_addresses', type=str, help="Comma-separated list of server IP addresses.")
    parser.add_argument('--seed', type=int, default=42, help="Seed value for random number generator.")
    args = parser.parse_args()

    trials = args.trials
    numbers_per_trial = args.numbers_per_trial
    random_seed = args.seed
    servers = [ip.strip() + ":9000" for ip in args.ip_addresses.split(',')]

    all_trials_results = []
    for trial in range(1, trials + 1):
        numbers = generate_random_numbers(numbers_per_trial, random_seed)
        results = process_numbers(servers, numbers, trial)
        all_trials_results.extend(results)

    df = pd.DataFrame(all_trials_results)
    average_response_times = df.groupby(['Trial'])['ResponseTime'].mean().reset_index()
    filename = f'prime_checks_trials_{trials}_numbers_{numbers_per_trial}.xlsx'
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        average_response_times.to_excel(writer, sheet_name='Average Response Times', index=False)

if __name__ == "__main__":
    main()
