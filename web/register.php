<?php
require "database.php";

if ($_SERVER["REQUEST_METHOD"] == "POST") {

    $full_name = $_POST['full_name'];
    $email     = $_POST['email'];
    $password  = $_POST['password'];

    $check = $conn->query("SELECT * FROM moder WHERE full_name='$full_name'");

    if ($check->num_rows > 0) {
        echo "Пользователь уже существует";
        exit();
    }

    $sql = "INSERT INTO moder (full_name, email, password)
            VALUES ('$full_name', '$email', '$password')";

    if ($conn->query($sql) === TRUE) {
        echo "Регистрация успешна! <a href='index.html'>Войти</a>";
    } else {
        echo "Ошибка регистрации";
    }
}
?>