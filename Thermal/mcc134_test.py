#!/usr/bin/env python3

from daqhats import hat_list, HatIDs, mcc134, TCType
import time

def detect_mcc134_boards():
    boards = []
    for entry in hat_list():
        if entry.id == HatIDs.MCC_134:
            print(f"[INFO] MCC 134 detected at address {entry.address}")
            boards.append(entry.address)
    if not boards:
        print("[ERROR] No MCC 134 boards found.")
    return boards

def initialize_board(address):
    board = mcc134(address)
    print(f"[INFO] Initializing MCC 134 at address {address}...")
    for ch in range(4):
        board.tc_type_write(ch, TCType.TYPE_K)
    return board

def read_temperatures(board):
    print("[INFO] Reading temperatures...")
    for ch in range(4):
        try:
            temp = board.a_in_read(ch)
            print(f"  Channel {ch}: {temp:.2f} °C")
        except Exception as e:
            print(f"  [ERROR] Channel {ch} read failed: {e}")

def main():
    addresses = detect_mcc134_boards()
    for addr in addresses:
        board = initialize_board(addr)
        read_temperatures(board)
        print()

if __name__ == "__main__":
    main()
