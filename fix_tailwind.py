import glob

files = glob.glob('web/templates/*.html')
script_wrong = """    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = { darkMode: 'class' }
    </script>"""
script_correct = """    <script>
        tailwind.config = { darkMode: 'class' }
    </script>
    <script src="https://cdn.tailwindcss.com"></script>"""

for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    content = content.replace(script_wrong, script_correct)
    
    with open(f, 'w') as file:
        file.write(content)

print("Done")
