/* ============================================
   LAST MILE PLATFORM - AI CHAT WIDGET
   Professional floating chat component
   ============================================ */

class AIChat {
  constructor(options = {}) {
    this.panel = options.panel || 'support'; // tenant|support|admin
    this.position = options.position || 'bottom-right';
    this.theme = 'dark';
    this.isOpen = false;
    this.messages = [];
    this.isLoading = false;
    this.apiBase = options.apiBase || (window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin);
    
    this.init();
  }
  
  init() {
    this.theme = document.documentElement.getAttribute('data-theme') || 'dark';
    this.createWidget();
    this.bindEvents();
    
    // Listen for theme changes
    window.addEventListener('themechange', (e) => {
      this.theme = e.detail.theme;
      this.updateTheme();
    });
  }
  
  createWidget() {
    // Container
    this.container = document.createElement('div');
    this.container.className = `ai-chat-container ai-chat-${this.position}`;
    this.container.innerHTML = `
      <!-- Toggle Button -->
      <button class="ai-chat-toggle" id="aiChatToggle">
        <i class="fas fa-robot"></i>
        <span class="ai-chat-badge" style="display:none;">1</span>
      </button>
      
      <!-- Chat Window -->
      <div class="ai-chat-window" id="aiChatWindow">
        <!-- Header -->
        <div class="ai-chat-header">
          <div class="ai-chat-header-info">
            <div class="ai-chat-avatar">
              <i class="fas fa-robot"></i>
            </div>
            <div>
              <div class="ai-chat-title">Asistente Last Mile</div>
              <div class="ai-chat-status">
                <span class="ai-status-dot online"></span>
                En linea
              </div>
            </div>
          </div>
          <div class="ai-chat-header-actions">
            <button class="ai-chat-theme-toggle" id="aiChatTheme">
              <i class="fas fa-sun"></i>
            </button>
            <button class="ai-chat-close" id="aiChatClose">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        
        <!-- Messages -->
        <div class="ai-chat-messages" id="aiChatMessages">
          <div class="ai-chat-welcome">
            <div class="ai-chat-welcome-icon">
              <i class="fas fa-robot"></i>
            </div>
            <h4>Hola! Soy tu asistente de Last Mile</h4>
            <p>Puedo ayudarte con tracking, consultas de negocio, soporte y mas.</p>
            <div class="ai-chat-suggestions" id="aiChatSuggestions"></div>
          </div>
        </div>
        
        <!-- Input -->
        <div class="ai-chat-input-area">
          <div class="ai-chat-input-wrapper">
            <input type="text" id="aiChatInput" placeholder="Escribe tu pregunta..." autocomplete="off">
            <button class="ai-chat-send" id="aiChatSend">
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
          <div class="ai-chat-input-hint">
            Enter para enviar | Powered by Last Mile AI
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.container);
    
    // Cache elements
    this.toggleBtn = document.getElementById('aiChatToggle');
    this.window = document.getElementById('aiChatWindow');
    this.messagesEl = document.getElementById('aiChatMessages');
    this.input = document.getElementById('aiChatInput');
    this.sendBtn = document.getElementById('aiChatSend');
    this.closeBtn = document.getElementById('aiChatClose');
    this.suggestionsEl = document.getElementById('aiChatSuggestions');
    this.themeBtn = document.getElementById('aiChatTheme');
    this.badge = this.container.querySelector('.ai-chat-badge');
    
    // Load suggestions
    this.loadSuggestions();
  }
  
  bindEvents() {
    this.toggleBtn.addEventListener('click', () => this.toggle());
    this.closeBtn.addEventListener('click', () => this.close());
    this.sendBtn.addEventListener('click', () => this.sendMessage());
    this.themeBtn.addEventListener('click', () => {
      if (typeof ThemeManager !== 'undefined') ThemeManager.toggle();
    });
    
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }
  
  toggle() {
    this.isOpen = !this.isOpen;
    this.window.classList.toggle('active', this.isOpen);
    this.toggleBtn.classList.toggle('active', this.isOpen);
    
    if (this.isOpen) {
      this.input.focus();
      this.badge.style.display = 'none';
      // Scroll to bottom
      setTimeout(() => this.scrollToBottom(), 100);
    }
  }
  
  close() {
    this.isOpen = false;
    this.window.classList.remove('active');
    this.toggleBtn.classList.remove('active');
  }
  
  updateTheme() {
    // Theme is handled by CSS variables, just update icon
    const icon = this.themeBtn.querySelector('i');
    icon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  }
  
  async loadSuggestions() {
    try {
      const resp = await fetch(`${this.apiBase}/api/ai/suggestions?panel=${this.panel}`);
      const data = await resp.json();
      if (data.success && data.data) {
        this.renderSuggestions(data.data);
      }
    } catch {
      // Fallback suggestions
      const defaults = this.panel === 'support' 
        ? [
            { icon: '📍', text: 'Rastrear mi pedido', query: 'donde esta mi pedido' },
            { icon: '❌', text: 'Cómo cancelo?', query: 'como cancelar pedido' },
            { icon: '💳', text: 'Métodos de pago', query: 'como pagar' },
          ]
        : [
            { icon: '📦', text: 'Envíos de hoy', query: 'cuantos envios hoy' },
            { icon: '💰', text: 'Revenue del mes', query: 'revenue este mes' },
            { icon: '🚚', text: 'Mejor chofer', query: 'mejor chofer' },
          ];
      this.renderSuggestions(defaults);
    }
  }
  
  renderSuggestions(suggestions) {
    this.suggestionsEl.innerHTML = suggestions.map(s => 
      `<button class="ai-suggestion-btn" onclick="window.aiChat.sendSuggestion('${s.query || s.text}')">
        <span class="ai-suggestion-icon">${s.icon}</span>
        <span>${s.text}</span>
      </button>`
    ).join('');
  }
  
  sendSuggestion(text) {
    this.input.value = text;
    this.sendMessage();
  }
  
  async sendMessage() {
    const message = this.input.value.trim();
    if (!message || this.isLoading) return;
    
    // Add user message
    this.addMessage(message, 'user');
    this.input.value = '';
    this.isLoading = true;
    this.showTyping();
    
    try {
      const resp = await fetch(`${this.apiBase}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          panel: this.panel,
          chat_history: this.messages.slice(-10).map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      });
      
      const data = await resp.json();
      
      this.hideTyping();
      
      if (data.success && data.data) {
        this.addMessage(data.data.response, 'assistant', {
          type: data.data.type,
          quickReplies: data.data.quick_replies
        });
      } else {
        this.addMessage('Lo siento, hubo un error. Intenta de nuevo.', 'assistant');
      }
    } catch (err) {
      this.hideTyping();
      this.addMessage('No pude conectar con el servidor. Intenta de nuevo.', 'assistant');
    }
    
    this.isLoading = false;
  }
  
  addMessage(content, role, meta = {}) {
    const msg = { role, content, ...meta, timestamp: new Date() };
    this.messages.push(msg);
    
    const div = document.createElement('div');
    div.className = `ai-chat-message ${role}`;
    
    if (role === 'user') {
      div.innerHTML = `<div class="ai-msg-bubble">${this.escapeHtml(content)}</div>`;
    } else {
      let html = `<div class="ai-msg-avatar"><i class="fas fa-robot"></i></div>`;
      html += `<div class="ai-msg-content">`;
      html += `<div class="ai-msg-bubble">${this.formatMessage(content)}</div>`;
      
      // Quick replies
      if (meta.quickReplies && meta.quickReplies.length > 0) {
        html += `<div class="ai-msg-quick-replies">`;
        meta.quickReplies.forEach(qr => {
          html += `<button class="ai-quick-reply" onclick="window.aiChat.sendSuggestion('${this.escapeHtml(qr)}')">${qr}</button>`;
        });
        html += `</div>`;
      }
      
      html += `</div>`;
      div.innerHTML = html;
    }
    
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  }
  
  showTyping() {
    const div = document.createElement('div');
    div.className = 'ai-chat-message assistant ai-typing';
    div.id = 'aiTyping';
    div.innerHTML = `
      <div class="ai-msg-avatar"><i class="fas fa-robot"></i></div>
      <div class="ai-msg-content">
        <div class="ai-msg-bubble">
          <span class="ai-typing-dot"></span>
          <span class="ai-typing-dot"></span>
          <span class="ai-typing-dot"></span>
        </div>
      </div>
    `;
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  }
  
  hideTyping() {
    const el = document.getElementById('aiTyping');
    if (el) el.remove();
  }
  
  scrollToBottom() {
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
  }
  
  formatMessage(text) {
    // Simple markdown: **bold**, *italic*, newlines
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
      .replace(/`(.*?)`/g, '<code>$1</code>');
  }
  
  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}

// Auto-create based on page
document.addEventListener('DOMContentLoaded', () => {
  // Determine panel type from page
  const path = window.location.pathname;
  let panel = 'support';
  
  if (path.includes('panel-tenant')) panel = 'tenant';
  else if (path.includes('panel-admin')) panel = 'admin';
  else if (path.includes('panel-operacion')) panel = 'operacion';
  else if (path.includes('tracking')) panel = 'support';
  else if (path.includes('ayuda')) panel = 'support';
  
  // Only create widget on pages that have the chat
  if (path.includes('tracking') || path.includes('ayuda') || 
      path.includes('panel-tenant') || path.includes('panel-admin')) {
    window.aiChat = new AIChat({ panel });
  }
});
