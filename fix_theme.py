import os
import re

TEMPLATES_DIR = '/home/xvin/Projects/Hakaton/AlmaTrack/web/templates'

for filename in os.listdir(TEMPLATES_DIR):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(TEMPLATES_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Clean up body classes
    content = re.sub(r'<body id="body" class=".*?"', '<body id="body" class="bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 font-sans transition-colors duration-300"', content)

    # Clean up card classes to be consistent
    # Find all instances of "card bg-white..." and ensure they have dark:bg-gray-800 dark:border-gray-700
    content = re.sub(r'\bcard bg-white\b(.*?dark:bg-gray-800)?', 'card bg-white dark:bg-gray-800 dark:border-gray-700', content)
    
    # Clean up tables
    content = re.sub(r'\bbg-gray-50\b(.*?dark:bg-gray-700/50)?', 'bg-gray-50 dark:bg-gray-800', content)
    content = re.sub(r'\btext-gray-500\b(.*?dark:text-gray-400)?', 'text-gray-500 dark:text-gray-400', content)
    content = re.sub(r'\btext-gray-900\b(.*?dark:text-gray-100)?', 'text-gray-900 dark:text-gray-100', content)
    content = re.sub(r'\btext-gray-700\b(.*?dark:text-gray-300)?', 'text-gray-700 dark:text-gray-300', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Theme fixed!")
