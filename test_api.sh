#!/bin/bash
echo "=== TEST API ===" 
echo ""
echo "1. Health Check:"
curl -s "https://msbross.me/api.php" | head -c 200
echo ""
echo ""
echo "2. Test Chat Groq:"
curl -s -X POST "https://msbross.me/api.php?action=chat" \
  -H "Content-Type: application/json" \
  -d '{"provider":"groq","messages":[{"role":"user","content":"Di solo: OK"}]}' | head -c 300
echo ""
echo ""
echo "3. Test TTS:"
curl -s -X POST "https://msbross.me/api.php?action=tts" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola","lang":"es-ES"}' | head -c 200
echo ""
echo "=== DONE ==="