import os

search_strings = ["I'll do it", "PRO_FGAA"]
txt_folder = 'cutscenes'

print(f"Searching for: {search_strings}")

for filename in os.listdir(txt_folder):
    if filename.endswith(".txt"):
        filepath = os.path.join(txt_folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for s in search_strings:
                    if s.lower() in content.lower():
                        print(f"\nFound '{s}' in: {filename}")
                        # Print the first few lines to see the header
                        f.seek(0)
                        print("Header lines:")
                        for _ in range(3):
                            print(f.readline().strip())
        except Exception as e:
            print(f"Error reading {filename}: {e}")
