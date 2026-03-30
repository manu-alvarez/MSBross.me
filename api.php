<?php
/**
 * MSBross Multi-LLM Gateway v3.5 - STANDALONE METRICS & MEMORY
 * Serverless API — runs on Nominalia shared hosting (PHP + cURL)
 * Zero VPS dependency. All LLM providers configured.
 */

// ── CORS & SECURITY HEADERS ──────────────────────────────────────
$allowedOrigin = getenv('CORS_ALLOWED_ORIGIN') ?: 'https://msbross.me';
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin && in_array($origin, [$allowedOrigin, 'https://www.msbross.me'], true)) {
    header('Access-Control-Allow-Origin: ' . $origin);
} else {
    header('Access-Control-Allow-Origin: ' . $allowedOrigin);
}
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Security Headers (SOTA Cleanup)
header('X-Frame-Options: SAMEORIGIN');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: strict-origin-when-cross-origin');
header("Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://msbross.me; connect-src 'self' https://api.groq.com https://api.openai.com https://api.anthropic.com https://api.openrouter.ai https://generativelanguage.googleapis.com https://speech.googleapis.com;");
header('Permissions-Policy: geolocation=(), camera=(), microphone=()');
header('Strict-Transport-Security: max-age=31536000; includeSubDomains; preload');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

function getEnvKey($name) {
    return getenv(strtoupper($name) . '_API_KEY') ?: getenv(strtoupper($name));
}

function requiredEnvKey($name) {
    $key = getEnvKey($name);
    if (!$key) {
        error_log("[SECURITY] Missing API key for provider: $name");
    }
    return $key;
}

// ── RATE LIMITING (SQLite) ─────────────────────────────────────────
function checkRateLimit($action) {
    // Only rate limit costly actions
    $costlyActions = ['chat', 'stt', 'tts'];
    if (!in_array($action, $costlyActions, true)) return;

    try {
        $dbFile = __DIR__ . '/rate_limit.sqlite';
        $pdo = new PDO('sqlite:' . $dbFile);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->exec("CREATE TABLE IF NOT EXISTS requests (ip TEXT, timestamp INTEGER)");

        $ip = $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1';
        $now = time();
        $window = 60; // 60 seconds window
        $limit = 30; // 30 reqs per minute limit for costly operations

        $stmt = $pdo->prepare("DELETE FROM requests WHERE timestamp < ?");
        $stmt->execute([$now - $window]);

        $stmt = $pdo->prepare("SELECT COUNT(*) FROM requests WHERE ip = ?");
        $stmt->execute([$ip]);
        $count = $stmt->fetchColumn();

        if ($count >= $limit) {
            abortJson('Rate limit exceeded. Please try again later.', 429);
        }

        $stmt = $pdo->prepare("INSERT INTO requests (ip, timestamp) VALUES (?, ?)");
        $stmt->execute([$ip, $now]);
    } catch (Exception $e) {
        // Fail open if SQLite throws an error (e.g. permissions) to not break prod
        error_log("[SECURITY-RATE-LIMIT] Error: " . $e->getMessage());
    }
}

// ── API KEYS (SECURED) ─────────────────────────────────────────────
$KEYS = [
    'google' => requiredEnvKey('google'),
    'groq' => requiredEnvKey('groq'),
    'openrouter' => requiredEnvKey('openrouter'),
    'openai' => requiredEnvKey('openai'),
    'anthropic' => requiredEnvKey('anthropic'),
    'opencode' => requiredEnvKey('opencode'),
    'odds_api' => requiredEnvKey('odds_api')
];

function abortJson($message, $code = 400) {
    http_response_code($code);
    header('Content-Type: application/json');
    echo json_encode(['error' => true, 'message' => $message]);
    exit();
}


// ── PROVIDER FUNCTIONS ──────────────────────────────────────────────
function postCURL($url, $data, $key, $extraHeaders = [], $timeout = 120) {
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    $headers = array_merge(["Content-Type: application/json"], $extraHeaders);
    if ($key) $headers[] = "Authorization: Bearer " . $key;
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return ["code" => $http_code, "body" => $response];
}

function callProvider($provider, $messages, $model = null, $temperature = 0.2, $isJson = true) {
    global $KEYS;
    switch ($provider) {
        case 'openai': return postCURL("https://api.openai.com/v1/chat/completions", ["model" => $model ?? 'gpt-4o', "messages" => $messages, "temperature" => $temperature], $KEYS['openai']);
        case 'anthropic':
            $system = ''; $msgs = [];
            foreach ($messages as $m) if ($m['role'] === 'system') $system = $m['content']; else $msgs[] = ["role" => $m['role'] === 'user' ? 'user' : 'assistant', "content" => $m['content']];
            $ch = curl_init("https://api.anthropic.com/v1/messages");
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type: application/json", "x-api-key: " . $KEYS['anthropic'], "anthropic-version: 2023-06-01"]);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(["model" => $model ?? 'claude-3-5-sonnet-20241022', "messages" => $msgs, "system" => $system, "temperature" => $temperature]));
            $res = curl_exec($ch); $code = curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
            return ["code" => $code, "body" => $res];
        case 'gemini':
            $url = "https://generativelanguage.googleapis.com/v1beta/models/" . ($model ?? 'gemini-2.5-flash-native-audio-latest') . ":generateContent?key=" . $KEYS['google'];
            $sys = null; $cont = [];
            foreach ($messages as $m) {
                if ($m['role'] === 'system') { $sys = $m['content']; continue; }
                $part = ["text" => $m['content']];
                if (isset($m['image'])) {
                    $imgParts = explode(',', $m['image']); $mime = str_replace(['data:', ';base64'], '', explode(':', $imgParts[0])[1]);
                    $cont[] = ["role" => "user", "parts" => [["inline_data" => ["mime_type" => $mime, "data" => $imgParts[1]]], ["text" => $m['content']]]];
                } else $cont[] = ["role" => $m['role'] === 'user' ? 'user' : 'model', "parts" => [["text" => $m['content']]]];
            }
            $data = ["contents" => $cont, "generationConfig" => ["temperature" => $temperature, "responseMimeType" => ($isJson ? "application/json" : "text/plain")]];
            if ($sys) $data["systemInstruction"] = ["parts" => [["text" => $sys]]];
            return postCURL($url, $data, '');
        default: return postCURL("https://api.groq.com/openai/v1/chat/completions", ["model" => $model ?? 'llama-3.3-70b-versatile', "messages" => $messages, "temperature" => $temperature], $KEYS['groq']);
    }
}

function extractResult($res) {
    if ($res['code'] >= 400) return ["error" => true, "text" => "API Error: " . $res['code']];
    $body = json_decode($res['body'], true);
    return ["error" => false, "text" => $body['choices'][0]['message']['content'] ?? $body['content'][0]['text'] ?? $body['candidates'][0]['content']['parts'][0]['text'] ?? ''];
}

// ── MAIN ROUTING ──────────────────────────────────────────────────
$allowedActions = [
    'chat', 'stt', 'tts', 'save_reservation', 'log_call', 'get_stats', 'traductor', 
    'get_tasks', 'add_task', 'update_task', 'delete_task', 'save_timer',
    'get_family_tasks', 'update_family_task', 'get_shopping_list', 'update_shopping_item',
    'combipro'
];
if ($_SERVER['REQUEST_METHOD'] === 'GET' && in_array($action, ['get_tasks', 'get_stats', 'get_family_tasks', 'get_shopping_list'])) {
    // GET actions allowed
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST' && !in_array($action, $allowedActions, true)) {
    abortJson('Invalid action', 400);
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    // Döhler & TaskFlow Helpers
    if ($action === 'get_tasks') {
        $file = 'dohler_tasks.json';
        echo file_exists($file) ? file_get_contents($file) : json_encode([]);
        exit();
    }
    if ($action === 'get_family_tasks') {
        $file = 'family_tasks.json';
        if (!file_exists($file)) {
            $default = [
                ["id" => 1, "time" => "07:30", "title" => "Despertador & Desayuno", "done" => false, "category" => "Rutina"],
                ["id" => 2, "time" => "08:30", "title" => "Colegio / Actividades Niños", "done" => false, "category" => "Niños"],
                ["id" => 3, "time" => "14:00", "title" => "Comida Familiar", "done" => false, "category" => "Comida"],
                ["id" => 4, "time" => "20:30", "title" => "Duchas & Pijamas", "done" => false, "category" => "Hogar"],
                ["id" => 5, "time" => "21:30", "title" => "Hora de Dormir", "done" => false, "category" => "Descanso"]
            ];
            file_put_contents($file, json_encode($default));
        }
        echo file_get_contents($file);
        exit();
    }
    if ($action === 'get_shopping_list') {
        $file = 'shopping_list.json';
        if (!file_exists($file)) {
            $default = [
                ["id" => 1, "name" => "Leche", "bought" => false, "category" => "Lácteos"],
                ["id" => 2, "name" => "Fruta Temporada", "bought" => false, "category" => "Fruta"],
                ["id" => 3, "name" => "Pan", "bought" => false, "category" => "Panadería"]
            ];
            file_put_contents($file, json_encode($default));
        }
        echo file_get_contents($file);
        exit();
    }
    if ($action === 'get_stats') {
        $file = 'dohler_stats.json';
        echo file_exists($file) ? file_get_contents($file) : json_encode(["total_pomodoros" => 0, "completed_tasks" => 0]);
        exit();
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    checkRateLimit($action);
    $input = json_decode(file_get_contents('php://input'), true) ?? [];

    if ($action === 'update_family_task') {
        $file = 'family_tasks.json';
        $tasks = json_decode(file_get_contents($file), true);
        foreach ($tasks as &$t) {
            if ($t['id'] == $input['id']) {
                if (isset($input['done'])) $t['done'] = $input['done'];
                if (isset($input['title'])) $t['title'] = $input['title'];
            }
        }
        file_put_contents($file, json_encode($tasks, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode(["status" => "updated"]);
        exit();
    }

    if ($action === 'update_shopping_item') {
        $file = 'shopping_list.json';
        $list = json_decode(file_get_contents($file), true);
        if (isset($input['add'])) {
            $list[] = ["id" => time(), "name" => $input['name'], "bought" => false, "category" => $input['category'] ?? "General"];
        } elseif (isset($input['delete'])) {
            $list = array_values(array_filter($list, fn($i) => $i['id'] != $input['id']));
        } else {
            foreach ($list as &$item) {
                if ($item['id'] == $input['id']) {
                    if (isset($input['bought'])) $item['bought'] = $input['bought'];
                }
            }
        }
        file_put_contents($file, json_encode($list, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode($list);
        exit();
    }

    if ($action === 'add_task') {
        $file = 'dohler_tasks.json';
        $tasks = file_exists($file) ? json_decode(file_get_contents($file), true) : [];
        $newTask = [
            'id' => time() . rand(100, 999),
            'title' => $input['title'] ?? 'Nueva Tarea',
            'completed' => false,
            'checklist' => $input['checklist'] ?? [],
            'created_at' => date('Y-m-d H:i:s')
        ];
        $tasks[] = $newTask;
        file_put_contents($file, json_encode($tasks, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode($newTask);
        exit();
    }

    if ($action === 'update_task') {
        $file = 'dohler_tasks.json';
        if (!file_exists($file)) abortJson('No tasks found', 404);
        $tasks = json_decode(file_get_contents($file), true);
        foreach ($tasks as &$t) {
            if ($t['id'] == $input['id']) {
                if (isset($input['completed'])) $t['completed'] = $input['completed'];
                if (isset($input['checklist'])) $t['checklist'] = $input['checklist'];
                if (isset($input['title'])) $t['title'] = $input['title'];
            }
        }
        file_put_contents($file, json_encode($tasks, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode(["status" => "updated"]);
        exit();
    }

    if ($action === 'delete_task') {
        $file = 'dohler_tasks.json';
        if (!file_exists($file)) abortJson('No tasks found', 404);
        $tasks = json_decode(file_get_contents($file), true);
        $tasks = array_values(array_filter($tasks, fn($t) => $t['id'] != $input['id']));
        file_put_contents($file, json_encode($tasks, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode(["status" => "deleted"]);
        exit();
    }

    if ($action === 'save_timer') {
        $file = 'dohler_stats.json';
        $stats = file_exists($file) ? json_decode(file_get_contents($file), true) : ["total_pomodoros" => 0, "completed_tasks" => 0];
        $stats['total_pomodoros'] += 1;
        file_put_contents($file, json_encode($stats, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode($stats);
        exit();
    }

    if ($action === 'traductor') {
        $modo = $input['modo'] ?? 'traducir_resumir';
        $texto = $input['texto'] ?? '';
        $destino = $input['destino'] ?? 'es';
        
        $system = "Eres un asistente experto en traducción y resumen. Devuelves SIEMPRE un JSON válido: {\"traduccion\": \"...\", \"resumen\": \"...\"}. Tarea: $modo hacia $destino.";
        $messages = [
            ["role" => "system", "content" => $system],
            ["role" => "user", "content" => $texto]
        ];
        
        $res = callProvider('groq', $messages, 'llama-3.3-70b-versatile', 0.2, true);
        $result = extractResult($res);
        echo json_encode(json_decode($result['text'], true) ?: ["traduccion" => $result['text'], "resumen" => ""]);
        exit();
    }

    if ($action === 'chat') {
        $res = callProvider($input['provider'] ?? 'groq', $input['messages'] ?? [], $input['model'] ?? null, $input['temperature'] ?? 0.7, false);
        $result = extractResult($res);
        echo json_encode(["content" => $result['text'], "error" => $result['error']]);
        exit();
    }

    if ($action === 'stt') {
        global $KEYS;
        if (empty($input['audio'])) {
            abortJson('Missing audio content', 400);
        }
        $data = ["config" => ["encoding" => "WEBM_OPUS", "sampleRateHertz" => 16000, "languageCode" => "es-ES"], "audio" => ["content" => $input['audio']]];
        $res = postCURL("https://speech.googleapis.com/v1/speech:recognize?key=" . $KEYS['google'], $data, '');
        $body = json_decode($res['body'], true);
        echo json_encode(["text" => $body['results'][0]['alternatives'][0]['transcript'] ?? '', "error" => $res['code'] >= 400]);
        exit();
    }

    if ($action === 'tts') {
        global $KEYS;
        if (empty($input['text'])) {
            abortJson('Missing text for TTS', 400);
        }
        $data = ["input" => ["text" => $input['text']], "voice" => ["languageCode" => "es-ES", "name" => "es-ES-Standard-A"], "audioConfig" => ["audioEncoding" => "MP3"]];
        $res = postCURL("https://texttospeech.googleapis.com/v1/text:synthesize?key=" . $KEYS['google'], $data, '');
        $body = json_decode($res['body'], true);
        echo json_encode(["audio" => $body['audioContent'] ?? '', "error" => $res['code'] >= 400]);
        exit();
    }

    if ($action === 'save_reservation') {
        $reservation = $input['reservation'] ?? null;
        if (!$reservation) {
            abortJson('Missing reservation object', 400);
        }
        $file = 'reservations.json';
        $data = file_exists($file) ? json_decode(file_get_contents($file), true) : [];
        $reservation['id'] = time();
        $reservation['timestamp'] = date('Y-m-d H:i:s');
        $data[] = $reservation;
        file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode(["status" => "ok"]);
        exit();
    }

    if ($action === 'log_call') {
        $file = 'calls_log.json'; $data = file_exists($file) ? json_decode(file_get_contents($file), true) : [];
        $data[] = ["timestamp" => date('Y-m-d H:i:s'), "event" => $input['event'] ?? 'interaction'];
        file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT), LOCK_EX);
        echo json_encode(["status" => "ok"]); exit();
    }

    if ($action === 'get_stats') {
        $res = file_exists('reservations.json') ? json_decode(file_get_contents('reservations.json'), true) : [];
        $calls = file_exists('calls_log.json') ? json_decode(file_get_contents('calls_log.json'), true) : [];
        echo json_encode(["reservations" => $res, "calls_count" => count($calls)]); exit();
    }
    if ($action === 'combipro') {
        global $KEYS;
        $sport = $input['sport'] ?? 'soccer_uefa_champs_league';
        $region = $input['regions'] ?? 'eu';
        $markets = $input['markets'] ?? 'h2h';
        $oddsFormat = $input['oddsFormat'] ?? 'decimal';
        $dateFormat = $input['dateFormat'] ?? 'iso';

        $url = "https://api.the-odds-api.com/v4/sports/$sport/odds/?apiKey=" . $KEYS['odds_api'] . "&regions=$region&markets=$markets&oddsFormat=$oddsFormat&dateFormat=$dateFormat";
        
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $headers = curl_getinfo($ch);
        
        // Extract quota headers
        $remaining = null; $used = null;
        if (isset($_SERVER['HTTP_X_REQUESTS_REMAINING'])) $remaining = $_SERVER['HTTP_X_REQUESTS_REMAINING'];
        // Re-fetching headers from the actual response for quota
        $header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
        // We need the headers to get the quota
        curl_setopt($ch, CURLOPT_HEADER, true);
        $response_with_headers = curl_exec($ch);
        $header_text = substr($response_with_headers, 0, $header_size);
        preg_match('/x-requests-remaining: (\d+)/i', $header_text, $match_rem);
        preg_match('/x-requests-used: (\d+)/i', $header_text, $match_used);
        $remaining = $match_rem[1] ?? null;
        $used = $match_used[1] ?? null;
        curl_close($ch);

        if ($http_code >= 400) {
            echo json_encode(["events" => [], "error" => "API Error $http_code", "quota" => ["remaining" => $remaining, "used" => $used]]);
        } else {
            $events = json_decode($response, true);
            echo json_encode(["events" => $events, "quota" => ["remaining" => $remaining, "used" => $used]]);
        }
        exit();
    }
}

header('Content-Type: application/json');
echo json_encode(["status" => "ok", "version" => "3.5", "engine" => "Standalone-SOTA-Metrics"]);
?>