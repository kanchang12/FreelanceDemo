#!/usr/bin/env python3
"""
WORKING Real Estate AI Demo for Koyeb Deployment
This actually works - auto-chat starts immediately!
"""

from flask import Flask, render_template_string, request, jsonify
import json
import re
import random
import time
import os
from datetime import datetime
import threading

# Try Google AI import
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

app = Flask(__name__)

# ================================
# SIMPLE WORKING AI AGENTS
# ================================

class WorkingMonitorAgent:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.has_api = False
        
        if self.api_key and GOOGLE_AI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.has_api = True
                print("✅ Google AI Connected")
            except Exception as e:
                print(f"⚠️ Google AI Error: {e}")
                self.has_api = False
        else:
            print("⚠️ No Google API key or library - using fallback")
    
    def should_respond(self, message):
        """Decide if AI should respond"""
        msg_lower = message.lower()
        
        # High priority - always respond
        if any(word in msg_lower for word in ['urgent credit', 'need verification', 'screen tenant']):
            return {"should_respond": True, "confidence": 0.95, "reason": "Urgent request"}
        
        # Complete tenant data
        has_name = bool(re.search(r'name[:\s]+[a-zA-Z\s]{3,}', message, re.IGNORECASE))
        has_phone = bool(re.search(r'phone[:\s]*[0-9\-\s]{8,}', message, re.IGNORECASE))
        has_salary = bool(re.search(r'salary[:\s]*[0-9,]+', message, re.IGNORECASE))
        
        if sum([has_name, has_phone, has_salary]) >= 2:
            return {"should_respond": True, "confidence": 0.85, "reason": "Complete tenant data"}
        
        # Credit check requests
        if 'credit' in msg_lower and ('check' in msg_lower or 'verify' in msg_lower):
            return {"should_respond": True, "confidence": 0.80, "reason": "Credit check request"}
        
        # Default: don't respond to casual chat
        return {"should_respond": False, "confidence": 0.90, "reason": "Casual conversation"}

class WorkingDataExtractor:
    def extract(self, message):
        """Extract data from message"""
        tenant = {}
        
        # Extract name
        name_match = re.search(r'name[:\s]+([a-zA-Z\s]{3,30})', message, re.IGNORECASE)
        if name_match:
            tenant['name'] = name_match.group(1).strip()
        
        # Extract phone
        phone_match = re.search(r'phone[:\s]*([0-9\-\s]{8,20})', message, re.IGNORECASE)
        if phone_match:
            tenant['phone'] = phone_match.group(1).strip()
        
        # Extract salary
        salary_match = re.search(r'salary[:\s]*([0-9,]+)', message, re.IGNORECASE)
        if salary_match:
            tenant['salary'] = salary_match.group(1)
        
        # Extract email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', message)
        if email_match:
            tenant['email'] = email_match.group(1)
        
        count = len([v for v in tenant.values() if v])
        
        return {
            "tenant": tenant,
            "extracted_count": count
        }

class WorkingResponseAgent:
    def respond(self, message, extracted_data):
        """Generate response"""
        tenant = extracted_data.get('tenant', {})
        
        if tenant.get('name') and tenant.get('salary'):
            return f"✅ Processing {tenant['name']}'s application with {tenant['salary']} NIS salary. Credit check starting now - results in 1-2 hours!"
        
        elif 'credit' in message.lower():
            return "🚀 Starting credit verification process. Need tenant's full details for complete background check."
        
        else:
            return "👋 Hi! I handle tenant screening and credit checks. How can I help?"

# ================================
# BROKER MESSAGE GENERATOR
# ================================

class BrokerChatGenerator:
    def __init__(self):
        self.brokers = ["Sarah_TLV", "Avi_RG", "Maya_Herz", "David_Rental", "Rachel_Props"]
        
        self.messages = {
            'casual': [
                "Good morning everyone! ☀️",
                "How's everyone doing today?",
                "Coffee break time ☕",
                "Market is busy today!",
                "Hope everyone has a great day!",
                "Traffic was crazy this morning 🚗",
                "Beautiful weather for showings!",
                "Ready for lunch break 🍽️",
                "Productive morning so far",
                "Weekend plans anyone?"
            ],
            'business': [
                "Looking for reliable tenant in Tel Aviv",
                "Property available next month in Ramat Gan", 
                "Client needs 2BR apartment ASAP",
                "What's market rate in Herzliya now?",
                "New building opening soon",
                "Anyone have good maintenance contacts?",
                "Showing went well this morning",
                "Pet-friendly options needed"
            ],
            'tenant_app': [
                "New application: Name: David Cohen, Phone: 054-123-4567, Salary: 15000 NIS, Employment: tech company",
                "Tenant details - Sarah Levi, Contact: 052-987-6543, Monthly income: 18000 NIS, Works at bank",
                "Application received: Michael Rosen (053-555-1234), earns 20000 NIS monthly, government employee"
            ],
            'credit_req': [
                "Need urgent credit check for new applicant",
                "Can someone verify tenant background quickly?",
                "Looking for fast credit verification service",
                "Need comprehensive tenant screening today"
            ]
        }
    
    def get_message(self):
        """Get random broker message"""
        # Weight: 70% casual, 20% business, 8% tenant, 2% credit
        msg_type = random.choices(
            ['casual', 'business', 'tenant_app', 'credit_req'],
            weights=[70, 20, 8, 2]
        )[0]
        
        broker = random.choice(self.brokers)
        message = random.choice(self.messages[msg_type])
        
        return broker, message, msg_type

# ================================
# FLASK APP
# ================================

# Initialize components
monitor = WorkingMonitorAgent()
extractor = WorkingDataExtractor()
responder = WorkingResponseAgent()
chat_gen = BrokerChatGenerator()

# Global data
chat_log = []
data_store = {}
stats = {"messages": 0, "responses": 0, "extractions": 0}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WORKING Real Estate AI Demo</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        
        .header { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 20px; color: white; text-align: center; }
        .header h1 { font-size: 2rem; margin-bottom: 10px; }
        .status { background: rgba(255,255,255,0.2); border-radius: 8px; padding: 8px; margin-top: 10px; }
        .status.working { background: rgba(76, 175, 80, 0.3); }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; display: flex; gap: 20px; }
        
        .chat-section { flex: 2; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); overflow: hidden; }
        .chat-header { background: linear-gradient(90deg, #25D366, #128C7E); color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
        .chat-status { font-size: 0.9rem; }
        
        .messages { height: 400px; overflow-y: auto; padding: 15px; background: #f0f0f0; }
        .message { margin: 10px 0; padding: 10px 15px; border-radius: 18px; max-width: 80%; word-wrap: break-word; animation: slideIn 0.3s ease; }
        .message.broker { background: #DCF8C6; margin-left: auto; }
        .message.user { background: #E1F5FE; margin-right: auto; }
        .message.ai { background: #FFE0B2; margin-right: auto; border-left: 4px solid #FF9800; }
        .message.system { background: #F3E5F5; margin-right: auto; font-style: italic; opacity: 0.8; }
        
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .msg-info { font-size: 0.8rem; font-weight: bold; margin-bottom: 5px; opacity: 0.7; }
        .msg-time { font-size: 0.7rem; opacity: 0.5; text-align: right; margin-top: 5px; }
        
        .input-area { padding: 15px; background: white; display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 12px 15px; border: 2px solid #e0e0e0; border-radius: 25px; outline: none; }
        .input-area input:focus { border-color: #25D366; }
        .input-area button { background: #25D366; color: white; border: none; padding: 12px 20px; border-radius: 25px; cursor: pointer; font-weight: bold; }
        .input-area button:hover { background: #128C7E; }
        
        .ai-panel { flex: 1; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); padding: 20px; }
        
        .ai-status { background: #E8F5E8; border-left: 4px solid #4CAF50; padding: 12px; border-radius: 8px; margin: 15px 0; }
        .ai-status.inactive { background: #f5f5f5; border-color: #999; }
        
        .data-section { background: #f8f9fa; border-radius: 8px; padding: 15px; margin-top: 15px; }
        .data-item { background: white; margin: 5px 0; padding: 8px; border-radius: 5px; border-left: 3px solid #4CAF50; font-size: 0.9rem; }
        
        .controls { text-align: center; padding: 15px; }
        .btn { background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); padding: 10px 15px; margin: 5px; border-radius: 20px; cursor: pointer; transition: all 0.3s; }
        .btn:hover { background: rgba(255,255,255,0.3); }
        .btn.active { background: #4CAF50; border-color: #4CAF50; }
        
        .live-indicator { display: inline-block; width: 8px; height: 8px; background: #4CAF50; border-radius: 50%; animation: pulse 1.5s infinite; margin-right: 8px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 WORKING Real Estate AI Demo</h1>
        <p>Multi-Agent System - Auto-Chat Starts Immediately!</p>
        <div class="status working" id="apiStatus">
            <span class="live-indicator"></span>System Ready - Chat Starting...
        </div>
    </div>
    
    <div class="container">
        <div class="chat-section">
            <div class="chat-header">
                <div>
                    <div>📱 Israeli Brokers Group - Live Chat</div>
                    <div class="chat-status">Sarah, Avi, Maya, David, Rachel + You</div>
                </div>
                <div class="chat-status">
                    <span class="live-indicator"></span>
                    <span id="autoStatus">Auto-Chat: Starting...</span>
                </div>
            </div>
            
            <div class="messages" id="messages"></div>
            
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <div class="ai-panel">
            <h3>🤖 AI Agent Status</h3>
            
            <div class="ai-status" id="aiStatus">
                <strong>Selective Monitor</strong><br>
                <span>Watching for business opportunities...</span>
            </div>
            
            <div class="data-section">
                <h4>📊 Extracted Data</h4>
                <div id="extractedData">No data extracted yet...</div>
            </div>
            
            <div class="data-section">
                <h4>📈 Live Stats</h4>
                <div>Messages: <span id="statMessages">0</span></div>
                <div>AI Responses: <span id="statResponses">0</span></div>
                <div>Data Extracted: <span id="statExtractions">0</span></div>
            </div>
        </div>
    </div>
    
    <div class="controls">
        <button class="btn active" id="autoChatBtn" onclick="toggleAutoChat()">⏸️ Auto-Chat ON</button>
        <button class="btn" onclick="sendTenantApp()">👤 Tenant App</button>
        <button class="btn" onclick="sendCreditReq()">💳 Credit Check</button>
        <button class="btn" onclick="clearChat()">🗑️ Clear</button>
    </div>

    <script>
        let autoChatActive = true;
        let messageCount = 0;
        
        function addMessage(content, sender, type) {
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${type}`;
            
            const time = new Date().toLocaleTimeString();
            div.innerHTML = `
                <div class="msg-info">${sender}</div>
                <div>${content}</div>
                <div class="msg-time">${time}</div>
            `;
            
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            messageCount++;
            
            document.getElementById('statMessages').textContent = messageCount;
        }
        
        function updateAIStatus(status, active = true) {
            const elem = document.getElementById('aiStatus');
            elem.className = active ? 'ai-status' : 'ai-status inactive';
            elem.innerHTML = `<strong>AI Monitor</strong><br><span>${status}</span>`;
        }
        
        function updateExtractedData(data) {
            const elem = document.getElementById('extractedData');
            if (Object.keys(data).length === 0) {
                elem.innerHTML = 'No data extracted yet...';
                return;
            }
            
            let html = '';
            Object.values(data).forEach(item => {
                if (item.data && item.data.extracted_count > 0) {
                    const tenant = item.data.tenant || {};
                    html += `<div class="data-item">`;
                    html += `<strong>${item.sender}:</strong> `;
                    if (tenant.name) html += `${tenant.name} `;
                    if (tenant.phone) html += `${tenant.phone} `;
                    if (tenant.salary) html += `${tenant.salary} NIS`;
                    html += `</div>`;
                }
            });
            elem.innerHTML = html || 'No business data yet...';
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'You', 'user');
            input.value = '';
            
            await processMessage(message, 'You');
        }
        
        async function processMessage(message, sender) {
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message, sender: sender})
                });
                
                const result = await response.json();
                
                updateAIStatus(result.status, result.decision.should_respond);
                
                if (result.ai_response) {
                    setTimeout(() => {
                        addMessage(result.ai_response, 'AI Assistant', 'ai');
                        document.getElementById('statResponses').textContent = result.stats.responses;
                    }, 1000);
                }
                
                updateExtractedData(result.data_store);
                document.getElementById('statExtractions').textContent = result.stats.extractions;
                
            } catch (error) {
                console.error('Error:', error);
                addMessage('❌ Connection error', 'System', 'system');
            }
        }
        
        async function generateBrokerMessage() {
            if (!autoChatActive) return;
            
            try {
                const response = await fetch('/simulate');
                const result = await response.json();
                
                addMessage(result.message, result.broker, 'broker');
                
                setTimeout(() => {
                    processMessage(result.message, result.broker);
                }, 800);
                
                // Schedule next message
                const delay = Math.random() * 3000 + 1500; // 1.5-4.5 seconds
                setTimeout(generateBrokerMessage, delay);
                
            } catch (error) {
                console.error('Auto-chat error:', error);
                setTimeout(generateBrokerMessage, 5000); // Retry in 5 seconds
            }
        }
        
        function toggleAutoChat() {
            const btn = document.getElementById('autoChatBtn');
            const status = document.getElementById('autoStatus');
            
            autoChatActive = !autoChatActive;
            
            if (autoChatActive) {
                btn.textContent = '⏸️ Auto-Chat ON';
                btn.classList.add('active');
                status.textContent = 'Auto-Chat: ACTIVE';
                generateBrokerMessage();
            } else {
                btn.textContent = '▶️ Auto-Chat OFF';
                btn.classList.remove('active');
                status.textContent = 'Auto-Chat: STOPPED';
            }
        }
        
        async function sendTenantApp() {
            const message = "New tenant application: Name: David Cohen, Phone: 054-123-4567, Salary: 15000 NIS, Employment: tech company";
            addMessage(message, 'Sarah_TLV', 'broker');
            setTimeout(() => processMessage(message, 'Sarah_TLV'), 500);
        }
        
        async function sendCreditReq() {
            const message = "Need urgent credit check for new applicant - can you help verify background?";
            addMessage(message, 'Avi_RG', 'broker');
            setTimeout(() => processMessage(message, 'Avi_RG'), 500);
        }
        
        function clearChat() {
            document.getElementById('messages').innerHTML = '';
            document.getElementById('extractedData').innerHTML = 'No data extracted yet...';
            document.getElementById('statMessages').textContent = '0';
            document.getElementById('statResponses').textContent = '0';
            document.getElementById('statExtractions').textContent = '0';
            messageCount = 0;
            updateAIStatus('Watching for business opportunities...');
        }
        
        // START IMMEDIATELY
        window.onload = function() {
            addMessage('🚀 Welcome! Auto-chat starting NOW...', 'System', 'system');
            addMessage('Watch AI respond ONLY to business messages, ignore casual chat!', 'System', 'system');
            
            // Start auto-chat immediately
            setTimeout(generateBrokerMessage, 1000);
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process_message():
    """Process message with AI"""
    global stats
    
    data = request.json
    message = data.get('message', '')
    sender = data.get('sender', 'Unknown')
    
    stats['messages'] += 1
    
    # Monitor decision
    decision = monitor.should_respond(message)
    
    ai_response = None
    extracted_data = {}
    
    if decision['should_respond']:
        # Extract data
        extracted_data = extractor.extract(message)
        if extracted_data.get('extracted_count', 0) > 0:
            stats['extractions'] += extracted_data['extracted_count']
            
            # Store data
            timestamp = datetime.now().isoformat()
            data_store[timestamp] = {
                'message': message,
                'sender': sender,
                'data': extracted_data
            }
        
        # Generate response
        ai_response = responder.respond(message, extracted_data)
        stats['responses'] += 1
        
        status = f"RESPONDED: {decision['reason']} (confidence: {decision['confidence']:.0%})"
    else:
        status = f"IGNORED: {decision['reason']} (confidence: {decision['confidence']:.0%})"
    
    return jsonify({
        'decision': decision,
        'ai_response': ai_response,
        'status': status,
        'data_store': data_store,
        'stats': stats
    })

@app.route('/simulate')
def simulate():
    """Generate broker message"""
    broker, message, msg_type = chat_gen.get_message()
    return jsonify({
        'broker': broker,
        'message': message,
        'type': msg_type
    })

@app.route('/health')
def health():
    """Health check for deployment"""
    return jsonify({
        'status': 'healthy',
        'google_ai': monitor.has_api,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 WORKING Real Estate AI Demo Starting...")
    print(f"🌐 Port: {port}")
    print(f"🔑 Google AI: {'✅ Connected' if monitor.has_api else '⚠️ Fallback'}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
