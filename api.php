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
$action = $_GET['action'] ?? '';
$allowedActions = ['chat', 'stt', 'tts', 'save_reservation', 'log_call', 'get_stats'];
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !in_array($action, $allowedActions, true)) {
    abortJson('Invalid action', 400);
}
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true) ?? [];

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
}

header('Content-Type: application/json');
echo json_encode(["status" => "ok", "version" => "3.5", "engine" => "Standalone-SOTA-Metrics"]);
?>