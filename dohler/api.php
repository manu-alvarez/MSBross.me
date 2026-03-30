<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization");
header("Content-Type: application/json");

// Manejo de pre-flight CORS
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit;
}

$dataFile = 'data.json';

// Inicializar archivo si no existe
if (!file_exists($dataFile)) {
    file_put_contents($dataFile, json_encode([
        'tasks' => [],
        'stats' => [
            'total_pomodoros' => 0,
            'completed_tasks' => 0
        ]
    ]));
}

$action = $_GET['action'] ?? '';
$input = json_decode(file_get_contents('php://input'), true);

function getData() {
    global $dataFile;
    return json_decode(file_get_contents($dataFile), true);
}

function saveData($data) {
    global $dataFile;
    file_put_contents($dataFile, json_encode($data, JSON_PRETTY_PRINT));
}

switch ($action) {
    case 'get_tasks':
        $data = getData();
        echo json_encode($data['tasks']);
        break;

    case 'add_task':
        $data = getData();
        $newTask = $input;
        $newTask['id'] = $newTask['id'] ?? uniqid();
        $data['tasks'][] = $newTask;
        saveData($data);
        echo json_encode($newTask);
        break;

    case 'update_task':
        $data = getData();
        $taskId = $input['id'] ?? '';
        foreach ($data['tasks'] as &$task) {
            if ($task['id'] == $taskId) {
                $task = array_merge($task, $input);
                break;
            }
        }
        saveData($data);
        echo json_encode(['status' => 'success']);
        break;

    case 'delete_task':
        $data = getData();
        $taskId = $input['id'] ?? '';
        $data['tasks'] = array_filter($data['tasks'], function($t) use ($taskId) {
            return $t['id'] != $taskId;
        });
        $data['tasks'] = array_values($data['tasks']);
        saveData($data);
        echo json_encode(['status' => 'success']);
        break;

    case 'get_stats':
        $data = getData();
        echo json_encode($data['stats']);
        break;

    case 'save_timer':
        $data = getData();
        $duration = $input['duration'] ?? 25;
        $data['stats']['total_pomodoros']++;
        $data['stats']['completed_tasks'] = count(array_filter($data['tasks'], function($t) { return $t['completed']; }));
        saveData($data);
        echo json_encode(['status' => 'success', 'stats' => $data['stats']]);
        break;

    default:
        echo json_encode(['error' => 'Invalid action']);
        break;
}
