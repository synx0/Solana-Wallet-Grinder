import os
import multiprocessing
import time
from collections import deque
from solders.keypair import Keypair
import base58

# Optimize for High-Core Servers
NUM_PROCESSES = min(multiprocessing.cpu_count(), 64)  # Use up to 64 cores
BATCH_SIZE = 50_000  # Increase batch size for better CPU utilization
ROLLING_WINDOW = 10  # Seconds for rolling speed window

# Use Unsigned 64-bit Integer to Prevent Overflow
attempts_counter = multiprocessing.RawValue('L', 0)  # Total attempts
found_counter = multiprocessing.Value('i', 0)  # Use Value for process-safe counter
counter_lock = multiprocessing.Lock()

# Event for process synchronization
shutdown_flag = multiprocessing.Value('i', 0)  # Shared flag to stop processes

# Tracking recent attempts for rolling speed calculation
attempts_history = deque(maxlen=ROLLING_WINDOW)
time_history = deque(maxlen=ROLLING_WINDOW)

# Track start time for overall stats
start_time = time.time()

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_wallet():
    """Generates a Solana wallet and returns the public and private keys."""
    keypair = Keypair()
    public_key = keypair.pubkey()
    private_key = base58.b58encode(keypair.to_bytes()).decode('utf-8')  # Correct private key encoding
    return str(public_key), private_key

def find_vanity_address(prefix, process_id, case_sensitive):
    """
    Generates addresses in batches until a match is found.
    """
    local_attempts = 0
    last_update_time = time.time()

    while shutdown_flag.value == 0:  # Ensure process stops when flag is set
        matches = []

        for _ in range(BATCH_SIZE):
            public_key, private_key = generate_wallet()
            local_attempts += 1

            # Match case-sensitive or case-insensitive based on user input
            if case_sensitive:
                if public_key.startswith(prefix):
                    matches.append((public_key, private_key))
            else:
                if public_key.lower().startswith(prefix.lower()):
                    matches.append((public_key, private_key))

            if matches:
                with counter_lock:
                    found_counter.value += 1  # Increment found counter safely
                    if shutdown_flag.value == 0:
                        shutdown_flag.value = 1  # Ensure shutdown is triggered only once
                break  # Stop early if match is found

        # Update attempts counter safely
        with counter_lock:
            attempts_counter.value += local_attempts

        # Track recent attempts for rolling speed
        now = time.time()
        attempts_history.append(attempts_counter.value)
        time_history.append(now)

        # Calculate speed over the last 10 seconds
        if len(time_history) > 1:
            time_span = time_history[-1] - time_history[0]
            rolling_speed = (attempts_history[-1] - attempts_history[0]) / time_span if time_span > 0 else 0
        else:
            rolling_speed = 0

        # Print progress every 1 second
        if time.time() - last_update_time > 1:
            last_update_time = time.time()
            clear_screen()
            print(f"\n🌟 Solana Vanity Address Generator (Optimized) 🌟")
            print(f"🔍 Searching for prefix: '{prefix}'")
            print(f"🖥 Using {NUM_PROCESSES} CPU cores with {BATCH_SIZE:,} batch size.\n")
            print(f"⏳ Total attempts: {attempts_counter.value:,}")
            print(f"⚡ Speed (Last {ROLLING_WINDOW} sec): {rolling_speed:,.2f} addresses/sec")
            print(f"🏆 Vanity Addresses Found: {found_counter.value}")

        # Save match and exit cleanly
        if matches:
            public_key, private_key = matches[0]
            save_wallet_details(public_key, private_key)
            print(f"\n🚀 [Process {process_id}] FOUND MATCH! 🚀")
            print(f"🎯 Wallet Address: {public_key}")
            print(f"🔑 Private Key: {private_key}")
            print("\n✅ Wallet details saved to solana_wallet.txt\n")
            return  # Exit naturally without crashing other processes

def save_wallet_details(public_key, private_key):
    """Saves wallet details to a file."""
    wallet_info = f"""
🚀 Solana Wallet Found! 🚀

🎯 Wallet Address: {public_key}
🔑 Private Key: {private_key}
"""
    file_path = os.path.join(os.getcwd(), 'solana_wallet.txt')
    with open(file_path, 'a') as file:  # Append mode so multiple matches are saved
        file.write(wallet_info + "\n" + "="*50 + "\n")

def main():
    """Main function to manage multiprocessing."""
    global start_time
    start_time = time.time()  # Start timer for live stats

    prefix = input("🎯 Enter the desired wallet prefix: ").strip()
    case_input = input("🎯 Case-Sensitive? (yes/no): ").strip().lower()
    
    if case_input not in {"yes", "no"}:
        print("⚠️ Invalid input. Please enter 'yes' or 'no'.")
        return

    case_sensitive = case_input == "yes"

    print(f"\n🌟 Starting Solana Vanity Address Generator (Optimized) 🌟")
    print(f"🔍 Searching for prefix: '{prefix}' (Case-Sensitive: {case_sensitive})\n")
    print(f"🖥 Using {NUM_PROCESSES} CPU cores with {BATCH_SIZE:,} batch size.\n")

    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        try:
            pool.starmap(find_vanity_address, [(prefix, i, case_sensitive) for i in range(NUM_PROCESSES)])
        except KeyboardInterrupt:
            print("\n🛑 User interrupted. Stopping all processes...\n")
            shutdown_flag.value = 1  # Ensure all processes stop gracefully
            pool.terminate()
            pool.join()  # Graceful shutdown

    print("\n✅ All processes stopped successfully!\n")

# Ensure this runs correctly with multiprocessing
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Fix for Windows/macOS multiprocessing
    main()
