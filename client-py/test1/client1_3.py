import grpc
import os
import time
import random
import pandas as pd
from isPrime import isPrime_pb2, isPrime_pb2_grpc

# ログを非表示にする。詳細なログが必要な場合は"NONE"を"DEBUG"に変更
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["NO_PROXY"] = "192.168.100.3"

def generate_numbers(num_count):
    """指定された数のランダムな整数リストを生成"""
    return [random.randint(100001, 1000000) for _ in range(num_count)]

def check_prime(server_address, number):
    """サーバーに素数判定をリクエストして、応答と処理時間を返す"""
    start_time = time.time()
    with grpc.insecure_channel(server_address) as channel:
        stub = isPrime_pb2_grpc.IsPrimeFuncStub(channel)
        response = stub.CheckPrime(isPrime_pb2.Value(Value=number))
    elapsed_time = time.time() - start_time
    return response.IsPrime, elapsed_time

def main():
    trials = 10  # 試行回数
    numbers_per_trial = 100
    server = "192.168.100.3:9000"  # 唯一のサーバーアドレス
    all_trials_results = []

    for trial in range(trials):
        results = []
        numbers = generate_numbers(numbers_per_trial)
        for number in numbers:
            is_prime, response_time = check_prime(server, number)
            results.append({
                "Trial": trial + 1,
                "Number": number,
                "IsPrime": 'T' if is_prime else 'F',
                "ResponseTime": response_time,
                "Server": server,
                "Level": 3
            })
            print(f"Trial {trial + 1}, Number: {number}, Prime: {'T' if is_prime else 'F'}, Time: {response_time:.4f}s, Server: {server}")

        # この試行の結果を追加
        all_trials_results.extend(results)

    # データをDataFrameに変換
    df = pd.DataFrame(all_trials_results)
    # 平均応答時間を計算
    average_response_times = df.groupby(['Trial', 'Server'])['ResponseTime'].mean().reset_index()
    print(average_response_times)

    # データと平均応答時間をExcelファイルに保存
    with pd.ExcelWriter('prime_checks_trials_single_server2-3.xlsx') as writer:
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        average_response_times.to_excel(writer, sheet_name='Average Response Times', index=False)

if __name__ == "__main__":
    main()
