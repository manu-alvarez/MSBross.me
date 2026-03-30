#!/bin/bash
# Script de testeo de API con logging detallado
LOGFILE="/Users/manu/Desktop/msbross.me/api_test_log.txt"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOGFILE"
}

log "=== INICIANDO TEST DE API msbross.me ==="

# Test 1: Health Check
log "TEST 1: Health Check"
curl -s "https://msbross.me/api.php" >> "$LOGFILE" 2>&1
HEALTH=$?
log "Exit code: $HEALTH"
log ""

# Test 2: Chat Groq
log "TEST 2: Chat Groq"
curl -s -X POST "https://msbross.me/api.php?action=chat" \
  -H "Content-Type: application/json" \
  -d '{"provider":"groq","messages":[{"role":"user","content":"Di solo OK"}],"temperature":0.1}' \
  >> "$LOGFILE" 2>&1
log "Exit code: $?"
log ""

# Test 3: Chat Gemini
log "TEST 3: Chat Gemini"
curl -s -X POST "https://msbross.me/api.php?action=chat" \
  -H "Content-Type: application/json" \
  -d '{"provider":"gemini","messages":[{"role":"user","content":"Di solo OK"}],"temperature":0.1}' \
  >> "$LOGFILE" 2>&1
log "Exit code: $?"
log ""

# Test 4: TTS
log "TEST 4: TTS Google"
curl -s -X POST "https://msbross.me/api.php?action=tts" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola","lang":"es-ES"}' \
  >> "$LOGFILE" 2>&1
log "Exit code: $?"
log ""

# Test 5: STT (simulado con audio vacío)
log "TEST 5: STT Google"
curl -s -X POST "https://msbross.me/api.php?action=stt" \
  -H "Content-Type: application/json" \
  -d '{"audio":"UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="}' \
  >> "$LOGFILE" 2>&1
log "Exit code: $?"
log ""

log "=== TESTS COMPLETADOS ==="
log "Revisa el archivo: $LOGFILE"