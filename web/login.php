<?php
require "database.php";

if ($_SERVER["REQUEST_METHOD"] == "POST") {

    $full_name = $_POST['full_name'];
    $password  = $_POST['password'];

    $sql = "SELECT * FROM moder WHERE full_name='$full_name' AND password='$password'";
    $result = $conn->query($sql);

    if ($result && $result->num_rows == 1) {
        header("Location: dashboard.php");
        exit();
    } else {
        echo "Неверный логин или пароль";
    }

} else {
    header("Location: index.html");
    exit();
}
?>