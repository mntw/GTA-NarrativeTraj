import os

target_subtitle = "I'll do it. I'll do it... Oh God."
txt_folder = 'cutscenes'

print(f"Searching for: '{target_subtitle}'")

for filename in os.listdir(txt_folder):
    if filename.endswith(".txt"):
        filepath = os.path.join(txt_folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if target_subtitle in content:
                    print(f"\nFound match in: {filename}")
                    # Print the first few lines to see the header
                    f.seek(0)
                    print("Header lines:")
                    for _ in range(3):
                        print(f.readline().strip())
        except Exception as e:
            print(f"Error reading {filename}: {e}")
