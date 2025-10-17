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

if (!$data || !isset($data['action']) || $data['action'] !== 'cleanup') {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request']);
    exit;
}

// Run the cleanup script
$output = [];
$return_code = 0;

// Execute the Python cleanup script
$command = 'python3 cleanup_broken_links.py --backup 2>&1';
exec($command, $output, $return_code);

if ($return_code === 0) {
    // Parse the output to get the number of removed webinars
    $removed_count = 0;
    foreach ($output as $line) {
        if (preg_match('/Broken URLs: (\d+)/', $line, $matches)) {
            $removed_count = intval($matches[1]);
            break;
        }
    }
    
    echo json_encode([
        'success' => true,
        'message' => 'Cleanup completed successfully',
        'removed_count' => $removed_count,
        'output' => implode("\n", $output)
    ]);
} else {
    echo json_encode([
        'success' => false,
        'error' => 'Cleanup script failed',
        'output' => implode("\n", $output)
    ]);
}
?>
