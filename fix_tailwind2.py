import glob

files = glob.glob('web/templates/*.html')
correct = """    <script>
        tailwind.config = { darkMode: 'class' }
    </script>
    <script src="https://cdn.tailwindcss.com"></script>"""

for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    # Tailwind CDN absolutely requires `tailwind.config` to be defined BEFORE the script SRC
    content = content.replace("<script src=\"https://cdn.tailwindcss.com\"></script>\n    <script>\n        tailwind.config = { darkMode: 'class' }\n    </script>", correct)
    
    with open(f, 'w') as file:
        file.write(content)

print("Done")
