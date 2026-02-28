<?php
require "database.php";

if($_SERVER["REQUEST_METHOD"] == "POST") {
    $fio = $_POST['fio'];
    $faculty = $_POST['faculty'];
    $year = $_POST['year'];
    $status = $_POST['status'];
    $company = $_POST['company'];
    $city = $_POST['city'];
    $dolg = $_POST['dolg'];

    $stmt = $conn->prepare("INSERT INTO student_requests 
        (fio, faculty, year, status, company, city, dolg)
        VALUES (?, ?, ?, ?, ?, ?, ?)");

    $stmt->bind_param("ssissss", $fio, $faculty, $year, $status, $company, $city, $dolg);
    $stmt->execute();

    echo "Заявка отправлена!";
}
?>

<form method="POST">
    <input name="fio" placeholder="ФИО" required><br>
    <input name="faculty" placeholder="Факультет" required><br>
    <input name="year" type="number" placeholder="Год поступления" required><br>

    <select name="status">
        <option>Junior</option>
        <option>Middle</option>
        <option>Senior</option>
    </select><br>

    <input name="company" placeholder="Компания"><br>
    <input name="city" placeholder="Город"><br>
    <input name="dolg" placeholder="Должность"><br>
    
    <button type="submit">Отправить заявку</button>
</form>