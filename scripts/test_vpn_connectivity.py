import subprocess

def ping(target):
    result = subprocess.run(["ping", "-c", "3", target])
    if result.returncode == 0:
        print(f"[PASS] {target}")
    else:
        print(f"[FAIL] {target}")

print("Testing VPN connectivity...\n")

ping("169.254.1.2")
ping("192.168.1.10")