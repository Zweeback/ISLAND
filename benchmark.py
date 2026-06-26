import time
import subprocess
from unittest.mock import patch

# Mock subprocess.check_output to simulate Windows netstat output with ~1000 lines
MOCK_OUTPUT = "\n".join([f"  TCP    0.0.0.0:{p}           0.0.0.0:0              LISTENING       {1000+p}" for p in range(1000, 2000)]).encode()

def mock_check_output(cmd, *args, **kwargs):
    time.sleep(0.05) # Simulate expensive subprocess call
    if "findstr :" in cmd:
        port = cmd.split("findstr :")[-1]
        lines = [line for line in MOCK_OUTPUT.decode().splitlines() if f":{port}" in line]
        return "\n".join(lines).encode()
    return MOCK_OUTPUT

def get_pid_by_port_original(port: int) -> int | None:
    try:
        output = subprocess.check_output(f'netstat -ano | findstr LISTENING | findstr :{port}', shell=True).decode()
        for line in output.splitlines():
            parts = line.strip().split()
            if parts and parts[1].endswith(f":{port}"):
                return int(parts[-1])
    except:
        pass
    return None

_PORT_TO_PID_CACHE = None

def get_pid_by_port_optimized(port: int) -> int | None:
    global _PORT_TO_PID_CACHE
    if _PORT_TO_PID_CACHE is None:
        _PORT_TO_PID_CACHE = {}
        try:
            output = subprocess.check_output('netstat -ano | findstr LISTENING', shell=True).decode()
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5:
                    address = parts[1]
                    if ":" in address:
                        p_str = address.rsplit(":", 1)[1]
                        try:
                            p = int(p_str)
                            if p not in _PORT_TO_PID_CACHE:
                                _PORT_TO_PID_CACHE[p] = int(parts[-1])
                        except ValueError:
                            pass
        except:
            pass
    return _PORT_TO_PID_CACHE.get(port)

def benchmark():
    ports_to_check = [1050, 1100, 1500, 1999, 8421, 8766]

    with patch('subprocess.check_output', side_effect=mock_check_output):
        # Baseline
        start = time.time()
        for p in ports_to_check:
            get_pid_by_port_original(p)
        end = time.time()
        baseline_time = end - start

        # Optimized
        global _PORT_TO_PID_CACHE
        _PORT_TO_PID_CACHE = None
        start = time.time()
        for p in ports_to_check:
            get_pid_by_port_optimized(p)
        end = time.time()
        optimized_time = end - start

        print(f"Baseline Time (Original): {baseline_time:.4f} seconds")
        print(f"Optimized Time: {optimized_time:.4f} seconds")
        if baseline_time > 0:
            print(f"Speedup: {baseline_time / optimized_time:.2f}x")

if __name__ == '__main__':
    benchmark()
