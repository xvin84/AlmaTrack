<?php
require "database.php";

$result = $conn->query("
    SELECT full_name, facultet, graduation_year, status, work_mesto, department
    FROM student
    ORDER BY graduation_year DESC
");

$students = [];
while ($row = $result->fetch_assoc()) {
    $students[] = $row;
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AlmaTrack - Выпускники</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body, .card, table, th, td, nav, input {
    transition: background-color 0.3s, color 0.3s;
}
</style>
</head>
<body id="body" class="bg-gray-50 text-gray-800 font-sans">

<button id="themeToggle"
    class="fixed bottom-6 left-6 w-14 h-14 flex items-center justify-center 
           rounded-full shadow-xl bg-white text-yellow-500
           transition-all duration-300 hover:scale-110 z-50 text-xl">
    <span id="themeIcon">🌙</span>
</button>

<nav id="navbar" class="bg-white shadow-sm px-6 py-4 flex justify-between items-center mb-8">
    <div class="font-bold text-xl text-blue-600">AlmaTrack</div>
    <div class="space-x-4">
        <a href="dashboard.php" class="text-gray-500 hover:text-gray-800">Дашборд</a>
        <a href="alumni.php" class="text-blue-600 font-medium">Выпускники</a>
        <a href="requests.php" class="text-gray-500 hover:text-gray-800">Заявки</a>
        <a href="login.php" class="text-gray-500 hover:text-red-500">Выход</a>
    </div>
</nav>

<div class="container mx-auto px-6">
    <div class="card bg-white shadow rounded-lg overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 class="text-lg font-semibold text-gray-800">Реестр студентов и выпускников</h2>
            <input type="text" id="searchInput" placeholder="Поиск по имени или компании..." class="border rounded px-3 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500">
        </div>
        
        <div class="overflow-x-auto">
            <table class="w-full whitespace-nowrap" id="studentsTable">
                <thead id="tableHead" class="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    <tr>
                        <th class="px-6 py-3">ФИО</th>
                        <th class="px-6 py-3">Факультет</th>
                        <th class="px-6 py-3">Год выпуска</th>
                        <th class="px-6 py-3">Уровень</th>
                        <th class="px-6 py-3">Компания</th>
                        <th class="px-6 py-3">Должность</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 text-sm">
                    <?php foreach($students as $s): ?>
                        <tr class="hover:bg-gray-50 transition">
                            <td class="px-6 py-4 font-medium"><?php echo htmlspecialchars($s['full_name']); ?></td>
                            <td class="px-6 py-4"><?php echo htmlspecialchars($s['facultet']); ?></td>
                            <td class="px-6 py-4">
                                <?php echo ($s['graduation_year'] > date('Y')) ? $s['graduation_year']." (студент)" : $s['graduation_year']; ?>
                            </td>
                            <td class="px-6 py-4">
                                <span class="px-2 py-1 rounded-full text-xs <?php
                                    $colors = ['Intern'=>'bg-gray-100 text-gray-800','Junior'=>'bg-blue-100 text-blue-800','Middle'=>'bg-yellow-100 text-yellow-800','Senior'=>'bg-green-100 text-green-800'];
                                    echo isset($colors[$s['status']]) ? $colors[$s['status']] : 'bg-gray-100 text-gray-800';
                                ?>">
                                <?php echo htmlspecialchars($s['status']); ?>
                                </span>
                            </td>
                            <td class="px-6 py-4"><?php echo htmlspecialchars($s['work_mesto']); ?></td>
                            <td class="px-6 py-4"><?php echo htmlspecialchars($s['department']); ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
const body = document.getElementById("body");
const navbar = document.getElementById("navbar");
const cards = document.querySelectorAll(".card");
const table = document.getElementById("studentsTable");
const tableHead = document.getElementById("tableHead");
const rows = table.querySelectorAll("tbody tr");
const inputs = document.querySelectorAll("input");
const button = document.getElementById("themeToggle");
const icon = document.getElementById("themeIcon");

function setDark() {
    body.style.backgroundColor = "#111827";
    body.style.color = "#f3f4f6";
    navbar.style.backgroundColor = "#1f2937";
    button.style.backgroundColor = "#1f2937";
    button.style.color = "#facc15";
    cards.forEach(card => { card.style.backgroundColor = "#1f2937"; card.style.color = "#f3f4f6"; });
    table.style.backgroundColor = "#1f2937";
    tableHead.style.backgroundColor = "#1f2937";
    tableHead.style.color = "#f3f4f6";
    rows.forEach(r => { r.style.color = "#f3f4f6"; });
    inputs.forEach(input => { input.style.backgroundColor = "#374151"; input.style.color = "#f3f4f6"; input.style.borderColor = "#6b7280"; });
    icon.textContent = "☀️";
    localStorage.setItem("theme", "dark");
}

function setLight() {
    body.style.backgroundColor = "#f9fafb";
    body.style.color = "#111827";
    navbar.style.backgroundColor = "#ffffff";
    button.style.backgroundColor = "#ffffff";
    button.style.color = "#111827";
    cards.forEach(card => { card.style.backgroundColor = "#ffffff"; card.style.color = "#111827"; });
    table.style.backgroundColor = "#ffffff";
    tableHead.style.backgroundColor = "#f9fafb";
    tableHead.style.color = "#6b7280";
    rows.forEach(r => { r.style.color = "#111827"; });
    inputs.forEach(input => { input.style.backgroundColor = "#ffffff"; input.style.color = "#111827"; input.style.borderColor = "#d1d5db"; });
    icon.textContent = "🌙";
    localStorage.setItem("theme", "light");
}

if(localStorage.getItem("theme") === "dark") { setDark(); } else { setLight(); }

button.addEventListener("click", () => {
    if(localStorage.getItem("theme") === "dark") { setLight(); } else { setDark(); }
});

document.getElementById('searchInput').addEventListener('input', function(){
    let filter = this.value.toLowerCase();
    rows.forEach(row => {
        let text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
});
</script>

</body>
</html>