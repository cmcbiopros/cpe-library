<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get the JSON data from the request body
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON data']);
    exit;
}

// Validate the data structure
if (!isset($data['webinars']) || !is_array($data['webinars'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid data structure']);
    exit;
}

// Create backup of current webinars.json
$backup_file = 'webinars_backup_' . date('Y-m-d_H-i-s') . '.json';
if (file_exists('webinars.json')) {
    copy('webinars.json', $backup_file);
}

// Save the updated data to webinars.json
$result = file_put_contents('webinars.json', json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

if ($result === false) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to save data']);
    exit;
}

// Clean up old backup files (keep only last 5)
$backup_files = glob('webinars_backup_*.json');
if (count($backup_files) > 5) {
    // Sort by modification time and remove oldest
    usort($backup_files, function($a, $b) {
        return filemtime($a) - filemtime($b);
    });
    
    $files_to_remove = array_slice($backup_files, 0, count($backup_files) - 5);
    foreach ($files_to_remove as $file) {
        unlink($file);
    }
}

echo json_encode(['success' => true, 'message' => 'Likes saved successfully']);
?>
