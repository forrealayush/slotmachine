from game.engine import get_slot_machine_spin,symbol_count,check_winnings,symbol_value
import os

MAX_LINES = 5
MAX_BET = 10000
MIN_BET = 500

ROWS = 3
COLS = 3



def color(text, c):
    return f"\033[{c}m{text}\033[0m"

RED = "31"
GREEN = "32"
YELLOW = "33"
CYAN = "36"

def clear():
    os.system("cls" if os.name == "nt" else "clear")






def print_slot_machine(columns):
    for r in range(ROWS):
        print(" | ".join(columns[c][r] for c in range(COLS)))

def deposit(minimum=MIN_BET):
    while True:
        amt = input("How much would you like to deposit? ₹")
        if amt.isdigit():
            amt = int(amt)
            if amt >= minimum:
                return amt
        print(f"Deposit must be at least ₹{minimum}.")

def get_number_of_lines():
    while True:
        lines = input("Enter the number of lines you want to bet on. (1-5)? ")
        if lines.isdigit():
            lines = int(lines)
            if 1 <= lines <= MAX_LINES:
                return lines
        print("Enter a valid number of lines!")

def get_bet():
    while True:
        amount = input("How much would you like to bet on each line? ₹")
        if amount.isdigit():
            amount = int(amount)
            if MIN_BET <= amount <= MAX_BET:
                return amount
        print(f"Amount must be between ₹{MIN_BET} - ₹{MAX_BET}.")

# Global stats
stats = {
    "spins": 0,
    "total_won": 0,
    "total_lost": 0,
    "max_win": 0,
    "max_loss": 0
}

def show_stats():
    net_profit = stats["total_won"] - stats["total_lost"]

    print("\n" + "=" * 35)
    print("           SESSION STATS")
    print("=" * 35)
    print(f"Spins:             {stats['spins']}")
    print(f"Total won:         +₹{stats['total_won']}")
    print(f"Total lost:        -₹{stats['total_lost']}")

    if net_profit > 0:
        print(color(f"Net P/L:           +₹{net_profit}", GREEN))
    elif net_profit < 0:
        print(color(f"Net P/L:           -₹{abs(net_profit)}", RED))
    else:
        print(color("Net P/L:            ₹0", CYAN))

    print(f"Best win:          +₹{stats['max_win']}")
    print(f"Worst loss:        -₹{stats['max_loss']}")
    print("=" * 35)

def spin_round(balance):
    while True:
        lines=get_number_of_lines()

        while True:
            bet=get_bet()
            total=bet*lines

            if total<=balance:
                break

            print("\nInsufficient balance!")
            print(f"Current balance: ₹{balance}")
            print(f"Your total bet: ₹{total}")
            print(f"Additional balance required: ₹{total-balance}")

            choice=input(
                "\nWhat would you like to do?\n"
                "1. Change number of lines\n"
                "2. Add balance\n"
                "3. Quit\n"
                "Choose an option: "
            )

            if choice=="1":
                break
            elif choice=="2":
                balance+=deposit(1)
                print(f"Balance updated to ₹{balance}.")
            elif choice=="3":
                return None
            else:
                print("Please choose 1, 2, or 3.")

        if total>balance:
            continue

        print(f"Your bet is ₹{bet} on {lines} lines. Total bet - ₹{total}")

        slots=get_slot_machine_spin(ROWS,COLS,symbol_count)
        print_slot_machine(slots)

        winnings,wins=check_winnings(
            slots,
            lines,
            bet,
            symbol_value
        )

        stats["spins"]+=1
        net_result=winnings-total

        if net_result>0:
            print(color(f"You won ₹{winnings}!",GREEN))
            print(color(f"Net winning: +₹{net_result}",GREEN))

            stats["total_won"]+=net_result

            if net_result>stats["max_win"]:
                stats["max_win"]=net_result

        elif net_result<0:
            print(color(f"Gross payout: ₹{winnings}",RED))
            print(color(f"Net loss: -₹{abs(net_result)}",RED))

            stats["total_lost"]+=abs(net_result)

            if abs(net_result)>stats["max_loss"]:
                stats["max_loss"]=abs(net_result)

        else:
            print(color("Break even!",CYAN))

        for line,mult,is_jackpot in wins:
            if is_jackpot:
                if mult==10:
                    print(color(f"{line} MEGA JACKPOT x{mult}!",YELLOW))
                else:
                    print(color(f"{line} JACKPOT x{mult}!",YELLOW))
            else:
                print(color(f"{line} win!",GREEN))

        show_stats()

        return winnings-total,balance

def ask_after_spin(balance):
    while True:
        print(color(f"Balance is now ₹{balance}.", CYAN))
        if balance == 0:
            choice = input("Your balance is ₹0. Add balance (A) or Quit (Q): ").lower()
            if choice == "a":
                return balance + deposit()
            elif choice == "q":
                return None
        else:
            choice = input("Continue (C), Add balance (A), or Quit (Q): ").lower()
            if choice == "c":
                return balance
            elif choice == "a":
                return balance + deposit()
            elif choice == "q":
                return None

def main():
    balance = deposit()
    while True:
        print(color(f"Current balance ₹{balance}", CYAN))
        result = spin_round(balance)
        if result is None:
            break
        change, balance = result
        balance += change
        balance = ask_after_spin(balance)
        if balance is None:
            break
    print(f"Remaining Balance  ₹{balance if balance is not None else 0}")
    print("\nYour session stats:")
    print(f"Total spins: {stats['spins']}")
    print(f"Total won: ₹{stats['total_won']}")
    print(f"Total lost: ₹{stats['total_lost']}")
    print(f"Max win: ₹{stats['max_win']}")
    print(f"Max loss: ₹{stats['max_loss']}")

#main()
if __name__=="__main__":
    main()

