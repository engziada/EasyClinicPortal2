import os

print("Current directory:", os.getcwd())
print("\nDirectories and files in current directory:")
for item in os.listdir():
    print(f"- {item} ({'directory' if os.path.isdir(item) else 'file'})")

# Check if mlmodel directory exists
if os.path.exists('mlmodel'):
    print("\nContents of mlmodel directory:")
    for item in os.listdir('mlmodel'):
        print(f"- {item} ({'directory' if os.path.isdir(os.path.join('mlmodel', item)) else 'file'})")
else:
    print("\nmlmodel directory not found in current directory")
    
    # Try to find it
    print("\nSearching for mlmodel directory...")
    for root, dirs, files in os.walk('.'):
        if 'mlmodel' in dirs:
            print(f"Found mlmodel directory at: {os.path.join(root, 'mlmodel')}")
            print("Contents:")
            for item in os.listdir(os.path.join(root, 'mlmodel')):
                print(f"- {item}")
            break
