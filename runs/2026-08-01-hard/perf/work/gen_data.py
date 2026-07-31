import random

def main():
    num_elements = 1000000
    filename = "data.txt"
    
    with open(filename, "w") as f:
        for _ in range(num_elements):
            f.write(f"{random.randint(0, 99999)}\n")
            
    print("Data generated")

if __name__ == "__main__":
    main()
