import time
import subprocess

def original_get_pid_by_port(port: int) -> int | None:
    try:
        # Mocking windows netstat call with a sleep to simulate delay
        output = subprocess.check_output(f'sleep 0.1 && echo "  TCP    127.0.0.1:{port}         0.0.0.0:0              LISTENING       1234"', shell=True).decode()
        for line in output.splitlines():
            parts = line.strip().split()
            if parts and parts[1].endswith(f":{port}"):
                return int(parts[-1])
    except Exception as e:
        pass
    return None

_pid_cache = None
def new_get_pid_by_port(port: int) -> int | None:
    global _pid_cache
    if _pid_cache is None:
        _pid_cache = {}
        try:
            # Mocking windows netstat call with a sleep to simulate delay
            output = subprocess.check_output(f'sleep 0.1 && echo "  TCP    127.0.0.1:8766         0.0.0.0:0              LISTENING       1234\n  TCP    127.0.0.1:8421         0.0.0.0:0              LISTENING       5678"', shell=True).decode()
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5:
                    local_addr = parts[1]
                    if ":" in local_addr:
                        try:
                            p = int(local_addr.rsplit(":", 1)[-1])
                            _pid_cache[p] = int(parts[-1])
                        except ValueError:
                            pass
        except Exception as e:
            pass
    return _pid_cache.get(port)

def run_benchmark():
    ports_to_check = [8766, 8421, 9000, 8080]

    start = time.time()
    for port in ports_to_check:
        original_get_pid_by_port(port)
    orig_time = time.time() - start
    print(f"Original implementation took: {orig_time:.4f} seconds")

    start = time.time()
    for port in ports_to_check:
        new_get_pid_by_port(port)
    new_time = time.time() - start
    print(f"New implementation took: {new_time:.4f} seconds")
    print(f"Improvement: {orig_time / new_time:.2f}x faster")

run_benchmark()
