import subprocess

cmd = [
    "/opt/homebrew/opt/openjdk@25/bin/java", "-jar", "freerouting.jar",
    "--help"
]
try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print("Return code:", res.returncode)
    print("Stdout:", res.stdout[:200])
    print("Stderr:", res.stderr[:200])
except subprocess.TimeoutExpired:
    print("Timed out!")
