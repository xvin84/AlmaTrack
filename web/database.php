<?php

$host = "sql313.infinityfree.com";
$user = "if0_41206634";
$pass = "bkZVInVSZO";
$db   = "if0_41206634_hackaton";

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
    die("Ошибка подключения к БД");
}

$conn->set_charset("utf8mb4");
?>