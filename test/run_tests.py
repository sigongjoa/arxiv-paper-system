import os
import importlib.util
import sys
import unittest
import asyncio

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def run_specific_test(test_file):
    print(f"Running test from {test_file}...")
    try:
        module_name = os.path.basename(test_file).replace('.py', '')
        test_module = load_module_from_path(module_name, test_file)
        
        # Check if it's a unittest test case
        suite = unittest.TestSuite()
        found_tests = False
        for name in dir(test_module):
            obj = getattr(test_module, name)
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                suite.addTest(unittest.makeSuite(obj))
                found_tests = True

        if found_tests:
            runner = unittest.TextTestRunner(verbosity=2)
            runner.run(suite)
        elif hasattr(test_module, 'main') and callable(test_module.main):
            # Handle async main functions
            if asyncio.iscoroutinefunction(test_module.main):
                asyncio.run(test_module.main())
            else:
                test_module.main()
        else:
            print(f"No unittest.TestCase or 'main' function found in {test_file}. Skipping.")

    except Exception as e:
        print(f"Error running test from {test_file}: {e}")

def main():
    test_files = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all test_*.py files in the current directory
    for f in os.listdir(current_dir):
        if f.startswith('test_') and f.endswith('.py'):
            test_files.append(os.path.join(current_dir, f))
    
    if not test_files:
        print("No test files found in this directory.")
        return

    while True:
        print("\n--- Select a Test to Run ---")
        for i, test_file in enumerate(test_files):
            print(f"{i + 1}. {os.path.basename(test_file)}")
        print(f"{len(test_files) + 1}. Run All Tests")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == '0':
            print("Exiting test runner.")
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(test_files):
                run_specific_test(test_files[idx])
            elif idx == len(test_files):
                print("\nRunning all tests...")
                for test_file in test_files:
                    run_specific_test(test_file)
            else:
                print("Invalid choice. Please try again.")
        else:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main() 