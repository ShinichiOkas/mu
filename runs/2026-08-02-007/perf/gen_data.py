import random

def generate_data():
    with open('data.txt', 'w') as f:
        for _ in range(1000000):
            f.write(f"{random.randint(0, 99999)}\n")

if __name__ == "__main__":
    generate_data()
