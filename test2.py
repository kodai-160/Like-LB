import grpc
import os
import time
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from isPrime import isPrime_pb2, isPrime_pb2_grpc

# gRPCのログレベルを設定
os.environ["GRPC_VERBOSITY"] = "NONE"

def generate_fixed_number(num_count, fixed_number):
    """固定された数を含むリストを生成する"""
    return [fixed_number] * num_count

def check_prime(server_address, number):
    """サーバーに素数判定をリクエストして、応答と処理時間を返す"""
    start_time = time.time()
    try:
        # gRPCチャネルを作成してサーバーに接続
        with grpc.insecure_channel(server_address) as channel:
            stub = isPrime_pb2_grpc.IsPrimeFuncStub(channel)
            # 素数判定のRPCを実行
            response = stub.CheckPrime(isPrime_pb2.Value(Value=number))
        elapsed_time = time.time() - start_time
        return response.IsPrime, elapsed_time
    except grpc.RpcError as e:
        # gRPCエラーが発生した場合の処理
        print(f"RPC Error: {e}")
        elapsed_time = time.time() - start_time
        return 'Error', elapsed_time

def process_numbers(servers, numbers, trial):
    """特定のトライアル用の番号リストを処理する"""
    results = []
    # スレッドプールを最大100スレッドで初期化
    with ThreadPoolExecutor(max_workers=100) as executor:
        # 各サーバーと番号の組み合わせに対して非同期で素数判定を実行
        future_to_number = {executor.submit(check_prime, server, number): (server, number) for server in servers for number in numbers}
        # 完了した順に結果を処理するループ
        for future in as_completed(future_to_number):
            server, number = future_to_number[future]
            try:
                # 各タスクの結果を取得
                is_prime, response_time = future.result()
                # 結果を辞書形式でresultsに追加
                results.append({
                    "Trial": trial,
                    "Number": number,
                    "IsPrime": 'T' if is_prime == True else 'F' if is_prime == False else 'Error',
                    "ResponseTime": response_time,
                    "Server": server
                })
                # 結果をコンソールに出力
                print(f"Trial {trial}, Number: {number}, Prime: {'T' if is_prime == True else 'F' if is_prime == False else 'Error'}, Time: {response_time:.4f}s, Server: {server}")
            except Exception as e:
                # エラーが発生した場合はエラーメッセージを出力して、エラー結果をresultsに追加
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
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="Run prime number checks with a gRPC server.")
    parser.add_argument('trials', type=int, help="Number of trials to run.")
    parser.add_argument('numbers_per_trial', type=int, help="Number of numbers to check per trial.")
    parser.add_argument('ip_addresses', type=str, help="Comma-separated list of server IP addresses.")
    args = parser.parse_args()

    trials = args.trials
    numbers_per_trial = args.numbers_per_trial
    fixed_number = 100000000000031  # 15桁の素数

    # サーバーのアドレスをリストに変換
    servers = [ip.strip() + ":9000" for ip in args.ip_addresses.split(',')]

    all_trials_results = []

    # 各トライアルごとに処理を実行
    for trial in range(1, trials + 1):
        # 固定数のリストを生成
        numbers = generate_fixed_number(numbers_per_trial, fixed_number)
        # 素数判定を実行し結果を取得
        results = process_numbers(servers, numbers, trial)
        # 結果を全体のリストに追加
        all_trials_results.extend(results)

    # 結果をDataFrameに変換
    df = pd.DataFrame(all_trials_results)
    # トライアルごとの平均応答時間を計算
    average_response_times = df.groupby(['Trial'])['ResponseTime'].mean().reset_index()
    # 結果をExcelファイルに書き込み
    filename = f'prime_checks_trials_{trials}_numbers_{numbers_per_trial}.xlsx'
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        average_response_times.to_excel(writer, sheet_name='Average Response Times', index=False)

if __name__ == "__main__":
    main()