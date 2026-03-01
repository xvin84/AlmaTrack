import os
import glob
import re

html_files = glob.glob('/home/xvin/Projects/Hakaton/AlmaTrack/web/templates/*.html')

nav_html = """    <nav id="navbar" class="bg-white dark:bg-gray-800 shadow-sm px-6 py-4 flex justify-between items-center mb-8">
        <div class="font-bold text-xl text-blue-600 dark:text-blue-400">AlmaTrack</div>
        <div class="space-x-4">
            <a href="{{ url_for('dashboard') }}" class="{% if request.endpoint == 'dashboard' %}text-blue-600 dark:text-blue-400 font-medium{% else %}text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200{% endif %}">Дашборд</a>
            <a href="{{ url_for('alumni') }}" class="{% if request.endpoint == 'alumni' %}text-blue-600 dark:text-blue-400 font-medium{% else %}text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200{% endif %}">Участники</a>
            <a href="{{ url_for('requests_page') }}" class="{% if request.endpoint == 'requests_page' %}text-blue-600 dark:text-blue-400 font-medium{% else %}text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200{% endif %}">Заявки</a>
            <a href="{{ url_for('events') }}" class="{% if request.endpoint == 'events' %}text-blue-600 dark:text-blue-400 font-medium{% else %}text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200{% endif %}">Мероприятия</a>
            <a href="{{ url_for('analytics') }}" class="{% if request.endpoint == 'analytics' %}text-blue-600 dark:text-blue-400 font-medium{% else %}text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200{% endif %}">Аналитика</a>
            {% if session.get('moderator_priority') == 1 %}
            <a href="{{ url_for('moderators') }}" class="{% if request.endpoint == 'moderators' %}text-blue-600 dark:text-blue-400 font-medium{% else %}text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200{% endif %}">Модераторы</a>
            {% endif %}
            <a href="{{ url_for('logout') }}" class="text-gray-500 dark:text-gray-400 hover:text-red-500">Выход</a>
        </div>
    </nav>"""

theme_script = """        const button = document.getElementById("themeToggle");
        const icon = document.getElementById("themeIcon");

        if (button && icon) {
            function setDark() {
                document.documentElement.classList.add('dark');
                icon.textContent = "☀️";
                localStorage.setItem("theme", "dark");
                if (typeof Chart !== 'undefined') {
                    Chart.defaults.color = '#9ca3af';
                    if (Chart.defaults.scale) {
                        Chart.defaults.scale.grid.color = '#374151';
                    }
                    updateCharts();
                }
            }

            function setLight() {
                document.documentElement.classList.remove('dark');
                icon.textContent = "🌙";
                localStorage.setItem("theme", "light");
                if (typeof Chart !== 'undefined') {
                    Chart.defaults.color = '#6b7280';
                    if (Chart.defaults.scale) {
                        Chart.defaults.scale.grid.color = '#e5e7eb';
                    }
                    updateCharts();
                }
            }

            function updateCharts() {
                if (typeof Chart !== 'undefined') {
                    for (let id in Chart.instances) {
                        Chart.instances[id].update();
                    }
                }
            }

            if (localStorage.getItem("theme") === "dark") {
                setDark();
            } else {
                setLight();
            }

            button.addEventListener("click", () => {
                if (localStorage.getItem("theme") === "dark") {
                    setLight();
                } else {
                    setDark();
                }
            });
        }
"""

theme_button = """    <button id="themeToggle" class="fixed bottom-6 left-6 w-14 h-14 flex items-center justify-center 
           rounded-full shadow-xl bg-white dark:bg-gray-800 text-yellow-500
           transition-all duration-300 hover:scale-110 z-50 text-xl">
        <span id="themeIcon">🌙</span>
    </button>"""

tailwind_config_script = """    <script>
        tailwind.config = { darkMode: 'class' }
    </script>
    <script src="https://cdn.tailwindcss.com"></script>"""

valid_body_class = 'class="bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100 font-sans"'

for file in html_files:
    if os.path.basename(file) == 'login.html':
        continue
        
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace navbar
    nav_pattern = re.compile(r'<nav id="navbar".*?</nav>', re.DOTALL)
    if nav_pattern.search(content):
        content = nav_pattern.sub(nav_html, content)
    
    # Standardize tailwind script
    # It might be there, might not be
    if "tailwind.config" not in content:
        content = content.replace('<script src="https://cdn.tailwindcss.com"></script>', tailwind_config_script)
        
    # Replace body class
    body_pattern = re.compile(r'<body id="body"\s+class="[^"]*">', re.M)
    if body_pattern.search(content):
        content = body_pattern.sub(f'<body id="body"\n    {valid_body_class}>', content)
    else:
        body_pattern2 = re.compile(r'<body\s+class="[^"]*">', re.M)
        if body_pattern2.search(content):
            content = body_pattern2.sub(f'<body id="body"\n    {valid_body_class}>', content)
            
    # Add theme button if missing
    if 'id="themeToggle"' not in content:
        content = content.replace('<nav id="navbar"', theme_button + '\n\n<nav id="navbar"')
    
    # Delete old messy custom dashboard dark mode script
    if 'function setDark() {' in content and 'body.style.backgroundColor =' in content:
        content = re.sub(r'const body = document.getElementById\("body"\);[\s\S]*?button.addEventListener\("click", \(\) => \{[\s\S]*?\}\);', theme_script, content)
        content = content.replace('Chart.defaults.color = \'#6b7280\';', '')
        
    # Fix the syntax error in requests.html and alumni.html: `    );`
    content = re.sub(r'\s*}\s*;\s*', '\n        }\n', content) # not foolproof but will fix it
    
    # Just to be extremely careful, replace any broken block of specific syntax
    content = content.replace('        }\n    );\n', '        }\n')
    content = content.replace('        // Real-time polling', '\n        // Real-time polling')
    content = content.replace('        }, 10;', '        }, 10000);\n')
    content = content.replace('        checkNewReques;', '        checkNewRequests();\n')
    
    # Write back
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("Processed HTML files")
