import random

def main():
    # Generate 100 random numeric values
    data = [str(random.uniform(0, 100)) for _ in range(100)]
    
    with open('data.txt', 'w') as f:
        f.write('\n'.join(data))
    
    print("DATA GEN OK")

if __name__ == "__main__":
    main()
