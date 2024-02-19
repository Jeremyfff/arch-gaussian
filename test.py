import sys
for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
    ascii_value = ord(char)
    padded_number = str(ascii_value).zfill(2)
    value = float(padded_number[-1:]) / 10
    print(value)
