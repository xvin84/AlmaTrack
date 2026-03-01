import glob
import re

files = glob.glob('web/templates/*.html')

theme_script = """        function getRows() {
            const table = document.querySelector("table");
            if (!table) return [];
            return table.querySelectorAll("tbody tr:not(#emptyRow)");
        }
        function getCards() {
            return document.querySelectorAll(".card");
        }
        function getInputs() {
            return document.querySelectorAll("input");
        }

        const button = document.getElementById("themeToggle");
        const icon = document.getElementById("themeIcon");

        if (button && icon) {
            function setDark() {
                document.body.style.backgroundColor = "#111827";
                document.body.style.color = "#f3f4f6";
                const navbar = document.getElementById("navbar");
                if(navbar) navbar.style.backgroundColor = "#1f2937";
                button.style.backgroundColor = "#1f2937";
                button.style.color = "#facc15";
                getCards().forEach(card => { card.style.backgroundColor = "#1f2937"; card.style.color = "#f3f4f6"; });
                
                const table = document.querySelector("table");
                if (table) table.style.backgroundColor = "#1f2937";
                const thead = document.querySelector("thead");
                if (thead) {
                    thead.style.backgroundColor = "#1f2937";
                    thead.style.color = "#f3f4f6";
                }
                getRows().forEach(r => { r.style.color = "#f3f4f6"; });
                getInputs().forEach(input => { input.style.backgroundColor = "#374151"; input.style.color = "#f3f4f6"; input.style.borderColor = "#6b7280"; });
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
                document.body.style.backgroundColor = "#f9fafb";
                document.body.style.color = "#111827";
                const navbar = document.getElementById("navbar");
                if(navbar) navbar.style.backgroundColor = "#ffffff";
                button.style.backgroundColor = "#ffffff";
                button.style.color = "#111827";
                getCards().forEach(card => { card.style.backgroundColor = "#ffffff"; card.style.color = "#111827"; });
                
                const table = document.querySelector("table");
                if (table) table.style.backgroundColor = "#ffffff";
                const thead = document.querySelector("thead");
                if (thead) {
                    thead.style.backgroundColor = "#f9fafb";
                    thead.style.color = "#6b7280";
                }
                getRows().forEach(r => { r.style.color = "#111827"; });
                getInputs().forEach(input => { input.style.backgroundColor = "#ffffff"; input.style.color = "#111827"; input.style.borderColor = "#d1d5db"; });
                
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

for file in files:
    if "login.html" in file:
        continue
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove all dark: tailwind classes
    content = re.sub(r'\s*dark:[a-zA-Z0-9\-\/]+', '', content)
    
    # Replace the JS dark mode toggle block
    content = re.sub(r'const button = document.getElementById\("themeToggle"\);[\s\S]*?\}\);[\s\S]*?\}', theme_script.strip(), content)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Processed UI colors")
