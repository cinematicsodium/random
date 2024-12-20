import time
import yaml

def log_prime_metrics_to_yaml(prime_index: int, total_primes: int, largest_prime: int, execution_time: str) -> None:
    with open('data.yaml', 'r+') as file:
        try:
            prime_metrics = yaml.safe_load(file)
            prime_metrics = {} if not prime_metrics else prime_metrics
        except yaml.YAMLError:
            prime_metrics = {}

    if not prime_metrics.get(prime_index):
        prime_metrics[prime_index] = {}
    prime_metrics[prime_index]['total_primes'] = total_primes
    prime_metrics[prime_index]['largest_prime'] = largest_prime
    prime_metrics[prime_index]['execution_time'] = execution_time

    with open('data.yaml','w') as file:
        yaml.safe_dump(prime_metrics, file, default_flow_style=False)

def is_prime(number: int) -> None:
    total_divisors = sum(1 for i in range(2,number) if number %i == 0)
    return total_divisors == 0

def calculate_prime_metrics(max_number: int) -> None:
    timer_start: float = time.time()
    prime_numbers: list[int] = [i for i in range(max_number) if is_prime(i)]
    timer_end: float = time.time()

    metrics_summary = {
        'total_primes':     len(prime_numbers),
        'largest_prime':    prime_numbers[-1],
        'execution_time':   f'{(timer_end-timer_start):.8f} sec.',
    }

    log_prime_metrics_to_yaml(
        prime_index=    max_number,
        total_primes=   metrics_summary['total_primes'],
        largest_prime=  metrics_summary['largest_prime'],
        execution_time= metrics_summary['execution_time']
    )

    padding_length = max(len(metric_name) for metric_name in metrics_summary) + 2
    formatted_metrics_output = (
        '\n'
        + '\n'.join(
            f'{str(metric_name + ":").ljust(padding_length)}{metric_value}'
            for metric_name, metric_value in metrics_summary.items()
    ))
    print(formatted_metrics_output)
    print('.'*50,'\n')


print()
print('calculating primes up to 10')
n = 10
calculate_prime_metrics(n)

print('calculating primes up to 100')
n = 100
calculate_prime_metrics(n)

print('calculating primes up to 1_000')
n = 1_000
calculate_prime_metrics(n)

print('calculating primes up to 10_000')
n = 10_000
calculate_prime_metrics(n)

print('calculating primes up to 100_000')
n = 100_000
calculate_prime_metrics(n)

print('calculating primes up to 1_000_000')
n = 1_000_000
calculate_prime_metrics(n)
