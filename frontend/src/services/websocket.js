class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectInterval = 5000;
    this.listeners = new Map();
    this.pingInterval = null;
  }

  connect(clientId = 'dashboard_client') {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    console.log(`🔌 Connecting to WebSocket as ${clientId}...`);
    this.ws = new WebSocket(`ws://127.0.0.1:8000/ws/${clientId}`);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected successfully');
      this.notifyListeners('connected', true);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📩 WebSocket message received:', data);
        this.notifyListeners('message', data);

        // Handle specific message types
        if (data.type === 'threat_alert') {
          this.notifyListeners('threat', data.threat);
          this.showBrowserNotification(data.threat);
        } else if (data.type === 'risk_change') {
          this.notifyListeners('risk_change', data);
        } else if (data.type === 'pong') {
          console.log('🏓 Pong received - connection alive');
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this.notifyListeners('error', error);
    };

    this.ws.onclose = () => {
      console.log('🔌 WebSocket disconnected. Reconnecting in 5s...');
      this.notifyListeners('connected', false);
      
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
      
      setTimeout(() => this.connect(clientId), this.reconnectInterval);
    };

    // Keep-alive ping every 30 seconds
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  disconnect() {
    console.log('🔌 Disconnecting WebSocket...');
    
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.listeners.clear();
  }

  send(message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('⚠️ WebSocket not connected. Cannot send message.');
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  notifyListeners(event, data) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }

  showBrowserNotification(threat) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`🚨 THREAT DETECTED: ${threat.threat_type || 'Unknown'}`, {
        body: `Risk: ${threat.risk_score} | User: ${threat.user_id || 'Unknown'} | Action: ${threat.action || 'N/A'}`,
        icon: '🛡️',
        tag: 'ignisyl-threat',
        requireInteraction: false,
      });
    }
  }
}

// Export singleton instance
export default new WebSocketService();
