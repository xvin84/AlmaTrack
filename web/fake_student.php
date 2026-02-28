<?php
require "database.php";

$conn->query("TRUNCATE TABLE student");

$names = [
    "Ivan", "Alexey", "Maria", "Dmitriy", "Anna", "Sergey",
    "Olga", "Nikita", "Vladimir", "Elena", "Artem", "Sofia",
    "Mikhail", "Alina", "Kirill", "Tatiana", "Roman", "Victoria"
];

$surnames = [
    "Ivanov", "Petrov", "Sidorov", "Smirnov", "Kuznetsov",
    "Popov", "Sokolov", "Lebedev", "Kozlov", "Novikov",
    "Morozov", "Volkov", "Fedorov", "Mikhailov"
];

$cities = [
    "Moscow", "Saint Petersburg", "Kazan", "Samara",
    "Novosibirsk", "Yekaterinburg", "Nizhny Novgorod",
    "Chelyabinsk", "Omsk", "Rostov-on-Don",
    "Ufa", "Krasnodar", "Perm", "Voronezh"
];

$faculties = [
    "IT", "Computer Science", "Software Engineering",
    "Cybersecurity", "Data Science",
    "Artificial Intelligence", "Applied Mathematics",
    "Information Systems"
];

$departments = [
    "Programmer", "Backend Developer", "Frontend Developer",
    "Mobile Developer", "DevOps Engineer",
    "QA Engineer", "System Analyst",
    "Data Analyst", "Machine Learning Engineer",
    "Database Administrator"
];

$workplaces = [
    "Yandex", "Sber", "VK", "Tinkoff", "Ozon",
    "Google", "Amazon", "Microsoft",
    "EPAM", "Kaspersky",
    "Avito", "Wildberries",
    "Mail.ru Group", "JetBrains"
];

$statuses_list = [
    "Intern",
    "Junior",
    "Middle",
    "Senior"
];

for ($i = 0; $i < 6; $i++) {

    $name = $names[array_rand($names)];
    $surname = $surnames[array_rand($surnames)];
    $full_name = $surname . " " . $name;

    $username = strtolower($surname . rand(10,99));
    $telegram = "@".$username;

    $faculty = $faculties[array_rand($faculties)];
    $department = $departments[array_rand($departments)];
    $city = $cities[array_rand($cities)];

    $enrollment_year = rand(2018, 2023);
    $graduation_year = $enrollment_year + 4;
    $is_alumni = (date("Y") > $graduation_year) ? 1 : 0;

    $created_at = date("Y-m-d H:i:s");
    $last_active = date("Y-m-d H:i:s");

	$work_mesto = $workplaces[array_rand($workplaces)];
	$status = $statuses_list[array_rand($statuses_list)];

	$sql = "INSERT INTO student 
	(telegram, username, full_name, facultet, enrollment_year, graduation_year, is_alumni, city, department, created_at, last_active, work_mesto, status)
	VALUES 
	('$telegram', '$username', '$full_name', '$faculty', $enrollment_year, $graduation_year, $is_alumni, '$city', '$department', '$created_at', '$last_active', '$work_mesto', '$status')";

    $conn->query($sql);
}

echo "6 студентов успешно добавлены!";
?>