import os
import re

TEMPLATES_DIR = 'web/templates'

js_theme_logic = """
        const body = document.getElementById("body");
        const navbar = document.getElementById("navbar");
        const cards = document.querySelectorAll(".card");
        const button = document.getElementById("themeToggle");
        const icon = document.getElementById("themeIcon");

        if (button && icon) {
            function setDark() {
                body.style.backgroundColor = "#111827";
                body.style.color = "#f3f4f6";
                if(navbar) navbar.style.backgroundColor = "#1f2937";
                button.style.backgroundColor = "#1f2937";
                button.style.color = "#facc15";
                cards.forEach(card => {
                    card.style.backgroundColor = "#1f2937";
                    card.style.color = "#f3f4f6";
                });
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
                body.style.backgroundColor = "#f9fafb";
                body.style.color = "#111827";
                if(navbar) navbar.style.backgroundColor = "#ffffff";
                button.style.backgroundColor = "#ffffff";
                button.style.color = "#111827";
                cards.forEach(card => {
                    card.style.backgroundColor = "#ffffff";
                    card.style.color = "#111827";
                });
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
                for (let id in Chart.instances) {
                    Chart.instances[id].update();
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

for filename in os.listdir(TEMPLATES_DIR):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(TEMPLATES_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove dark: classes
    content = re.sub(r'\bdark:bg-\S+', '', content)
    content = re.sub(r'\bdark:text-\S+', '', content)
    content = re.sub(r'\bdark:border-\S+', '', content)
    content = re.sub(r'\bdark:hover:\S+', '', content)
    content = re.sub(r'\bdark:divide-\S+', '', content)
    # clean up multiple spaces created by replacements
    content = re.sub(r' +', ' ', content)
    content = content.replace('class=" "', '')

    # 2. Replace the JS
    js_pattern = r'const button = document.getElementById\("themeToggle"\);[\s\S]*?(?=\s*</script>)'
    
    if re.search(js_pattern, content):
        content = re.sub(js_pattern, js_theme_logic.strip(), content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Theme reverted!")
