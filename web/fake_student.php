<?php
require "database.php";

$conn->query("TRUNCATE TABLE student");

$names = ["ivan", "Alexy", "Maria", "Dmitriy", "Anna", "Sergay"];
$surnames = ["Ivanov", "Petrov", "Sidorov", "Mirage"];
$cities = ["kazan", "Samara"];
$faculties = ["IT"];
$departments = ["Programmist"];
$workplaces = ["Яндекс", "Сбер", "VK", "Тинькофф", "Ozon"];
$statuses_list = ["Intern","Junior","Middle","Senior"];

for ($i = 0; $i < 228; $i++) {

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