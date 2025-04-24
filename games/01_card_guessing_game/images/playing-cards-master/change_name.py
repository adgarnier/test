import os

i = 2
while i < 11:
    try:
        old_name = f"spades_{i}.png"
        new_name = f"Spades_{i}.png"
        os.rename(old_name, new_name)
        i += 1
    except Exception as e:
        print(e)
        i += 1