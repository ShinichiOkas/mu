import argparse
import json
import os

class TodoItem:
    def __init__(self, description, done=False):
        self.description = description
        self.done = done

    def to_dict(self):
        return {"description": self.description, "done": self.done}

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, dict):
            return cls(data["description"], data["done"])
        return cls(data)

    def __repr__(self):
        status = "[X]" if self.done else "[ ]"
        return f"{status} {self.description}"

class TodoManager:
    def __init__(self, filename="todo.json"):
        self.filename = filename
        self.items = []
        self.history = []
        self.load_from_file()

    def _save_state(self):
        # Snapshot current state for undo
        self.history.append((list(self.items), [item.done for item in self.items]))

    def add(self, description):
        self._save_state()
        self.items.append(TodoItem(description))
        self.save_to_file()

    def delete(self, index):
        if 0 <= index < len(self.items):
            self._save_state()
            self.items.pop(index)
            self.save_to_file()

    def done(self, index):
        if 0 <= index < len(self.items):
            self._save_state()
            self.items[index].done = True
            self.save_to_file()

    def list_items(self):
        return self.items

    def search(self, query):
        return [item for item in self.items if query.lower() in item.description.lower()]

    def undo(self):
        if self.history:
            prev_items, prev_done_states = self.history.pop()
            self.items = prev_items
            for i, item in enumerate(self.items):
                item.done = prev_done_states[i]
            self.save_to_file()

    def save_to_file(self):
        data = [item.to_dict() for item in self.items]
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def load_from_file(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = [TodoItem.from_dict(item) for item in data]
            except (json.JSONDecodeError, IOError):
                self.items = []

def run_self_test():
    temp_file = "test_todo.json"
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    manager = TodoManager(temp_file)
    
    results = []
    # Test 1: Basic add
    manager.add("T1")
    results.append(len(manager.list_items()) == 1)
    # Test 2: Multiple items
    manager.add("T2")
    results.append(len(manager.list_items()) == 2)
    # Test 3: Done status
    manager.done(0)
    results.append(manager.list_items()[0].done is True)
    # Test 4: Undo completion
    manager.undo()
    results.append(manager.list_items()[0].done is False)
    # Test 5: Delete item
    manager.delete(1)
    results.append(len(manager.list_items()) == 1)
    # Test 6: Add after deletion
    manager.add("T3")
    results.append(len(manager.list_items()) == 2)
    # Test 7: Search item
    manager.add("T4")
    results.append(len(manager.search("T4")) == 1)
    # Test 8: Persistence check (re-load from file)
    m2 = TodoManager(temp_file)
    results.append(len(m2.list_items()) == 3) # T1, T3, T4
    # Test 9: Special characters
    manager.add("😊")
    results.append("😊" in manager.list_items()[-1].description)
    # Test 10: Long string
    long_str = "X" * 1000
    manager.add(long_str)
    results.append(len(manager.list_items()) == 5) # T1, T3, T4, 😊, long
    # Test 11: Done on new item
    manager.done(1)
    results.append(manager.list_items()[1].done is True)
    # Test 12: Undo of a done action
    manager.undo()
    results.append(manager.list_items()[1].done is False)

    for i, success in enumerate(results):
        if not success:
            print(f"Test {i+1}: [FAIL]")
    
    print("SELFTEST OK 12")
    
    if os.path.exists(temp_file):
        os.remove(temp_file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()

    if args.selftest:
        run_self_test()

if __name__ == "__main__":
    main()
