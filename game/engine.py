import random

symbol_count = {"A": 2, "B": 4, "C": 6, "D": 8, "W": 1}
symbol_value = {"A": 5, "B": 4, "C": 3, "D": 2, "W": 10}

def check_winnings(columns,lines,bet,values):
    winnings=0
    winning_lines=[]
    jackpot_multiplier={"D":2,"C":3,"B":4,"A":5,"W":10}
    all_lines=[
        [columns[0][0],columns[1][0],columns[2][0]],
        [columns[0][1],columns[1][1],columns[2][1]],
        [columns[0][2],columns[1][2],columns[2][2]],
        [columns[0][0],columns[1][1],columns[2][2]],
        [columns[0][2],columns[1][1],columns[2][0]]
    ]
    for line_number in range(lines):
        current_line=all_lines[line_number]
        non_wild=[s for s in current_line if s!="W"]
        if len(non_wild)==0 or len(set(non_wild))==1:
            symbol_to_use="W" if len(non_wild)==0 else non_wild[0]
            win=values[symbol_to_use]*bet
            multiplier=jackpot_multiplier[symbol_to_use]
            win*=multiplier
            winning_lines.append((f"Line {line_number+1}",multiplier,True))
            winnings+=win
    return winnings,winning_lines


def get_slot_machine_spin(rows, cols, symbols):
    all_symbols = []
    for symbol, count in symbols.items():
        for _ in range(count):
            all_symbols.append(symbol)
    columns = []
    for _ in range(cols):
        col = []
        temp = all_symbols[:]
        for _ in range(rows):
            s = random.choice(temp)
            temp.remove(s)
            col.append(s)
        columns.append(col)
    return columns