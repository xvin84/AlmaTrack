<?php
require "database.php";

$result = $conn->query("SELECT COUNT(*) as total_students FROM student");
$row = $result->fetch_assoc();
$total_students = $row['total_students'];

$result = $conn->query("
    SELECT work_mesto, COUNT(*) as cnt
    FROM student
    WHERE work_mesto IS NOT NULL AND work_mesto != ''
    GROUP BY work_mesto
    ORDER BY cnt DESC
    LIMIT 10
");
$employers = [];
$employers_count = [];
while($row = $result->fetch_assoc()) {
    $employers[] = $row['work_mesto'];
    $employers_count[] = $row['cnt'];
}

$result = $conn->query("
    SELECT status, COUNT(*) as cnt
    FROM student
    WHERE status IS NOT NULL AND status != ''
    GROUP BY status
");
$statuses = [];
$statuses_count = [];
while($row = $result->fetch_assoc()) {
    $statuses[] = $row['status'];
    $statuses_count[] = $row['cnt'];
}

$result = $conn->query("
    SELECT city, COUNT(*) as cnt
    FROM student
    WHERE city IS NOT NULL AND city != ''
    GROUP BY city
    ORDER BY cnt DESC
    LIMIT 7
");
$cities = [];
$cities_count = [];
while($row = $result->fetch_assoc()) {
    $cities[] = $row['city'];
    $cities_count[] = $row['cnt'];
}
?>

<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AlmaTrack - Дашборд</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50 font-sans text-gray-800">

<nav class="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
    <div class="font-bold text-xl text-blue-600">AlmaTrack</div>
    <div class="space-x-4">
        <a href="dashboard.php" class="text-blue-600 font-medium">Дашборд</a>
        <a href="alumni.php" class="text-gray-500 hover:text-gray-800">Выпускники</a>
        <a href="login.php" class="text-gray-500 hover:text-red-500">Выход</a>
    </div>
</nav>

<div class="container mx-auto px-6 py-8">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6 flex items-center justify-between border-l-4 border-blue-500">
            <div>
                <p class="text-sm text-gray-500 mb-1">Всего студентов</p>
                <h3 class="text-3xl font-bold"><?php echo $total_students; ?></h3>
            </div>
            <div class="text-3xl">📊</div>
        </div>
        <div class="bg-white rounded-lg shadow p-6 flex items-center justify-between border-l-4 border-green-500">
            <div>
                <p class="text-sm text-gray-500 mb-1">Компаний-работодателей</p>
                <h3 class="text-3xl font-bold"><?php echo count($employers); ?></h3>
            </div>
            <div class="text-3xl">🏢</div>
        </div>
        <div class="bg-white rounded-lg shadow p-6 flex items-center justify-between border-l-4 border-purple-500">
            <div>
                <p class="text-sm text-gray-500 mb-1">Охвачено городов</p>
                <h3 class="text-3xl font-bold"><?php echo count($cities); ?></h3>
            </div>
            <div class="text-3xl">🌍</div>
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white p-6 rounded-lg shadow">
            <h4 class="text-lg font-semibold mb-4 text-gray-700">Топ-10 работодателей</h4>
            <canvas id="employersChart" height="200"></canvas>
        </div>

        <div class="bg-white p-6 rounded-lg shadow">
            <h4 class="text-lg font-semibold mb-4 text-gray-700">Уровни (Intern/Jr/Mid/Sr)</h4>
            <div class="relative h-64 w-full flex justify-center">
                <canvas id="levelsChart"></canvas>
            </div>
        </div>

        <div class="bg-white p-6 rounded-lg shadow">
            <h4 class="text-lg font-semibold mb-4 text-gray-700">Карьерный рост по годам выпуска</h4>
            <canvas id="growthChart" height="200"></canvas>
        </div>

        <div class="bg-white p-6 rounded-lg shadow">
            <h4 class="text-lg font-semibold mb-4 text-gray-700">Топ-7 городов</h4>
            <canvas id="citiesChart" height="200"></canvas>
        </div>
    </div>
</div>

<script>
Chart.defaults.font.family = 'Inter, sans-serif';
Chart.defaults.color = '#6b7280';

new Chart(document.getElementById('employersChart'), {
    type: 'bar',
    data: {
        labels: <?php echo json_encode($employers); ?>,
        datasets: [{ label: 'Студентов', data: <?php echo json_encode($employers_count); ?>, backgroundColor: '#3b82f6' }]
    },
    options: { indexAxis: 'y', responsive: true }
});

new Chart(document.getElementById('levelsChart'), {
    type: 'doughnut',
    data: {
        labels: <?php echo json_encode($statuses); ?>,
        datasets: [{ data: <?php echo json_encode($statuses_count); ?>, backgroundColor: ['#9ca3af','#60a5fa','#34d399','#f87171'] }]
    },
    options: { responsive:true, maintainAspectRatio:false }
});

new Chart(document.getElementById('growthChart'), {
    type: 'line',
    data: {
        labels: ['2020', '2021', '2022', '2023', '2024'],
        datasets: [
            { label: 'Месяцев до Junior', data: [12,10,8,7,6], borderColor:'#3b82f6', tension:0.3 },
            { label: 'Месяцев до Middle', data: [24,22,18,16,null], borderColor:'#10b981', tension:0.3 }
        ]
    },
    options: { responsive:true }
});

new Chart(document.getElementById('citiesChart'), {
    type: 'bar',
    data: {
        labels: <?php echo json_encode($cities); ?>,
        datasets: [{ label:'Студентов', data: <?php echo json_encode($cities_count); ?>, backgroundColor:'#8b5cf6' }]
    },
    options: { indexAxis:'y', responsive:true }
});
</script>

</body>
</html>