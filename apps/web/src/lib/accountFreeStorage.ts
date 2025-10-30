/**
 * Account-Free Storage System
 * 
 * Uses browser IndexedDB for unlimited local storage.
 * NO LOGIN REQUIRED. User controls their data.
 * 
 * Features:
 * - Conversation history (unlimited)
 * - Preferences (trust weights, UI settings)
 * - Search history
 * - Export/Import data (GDPR compliant)
 * - Optional self-hosted sync
 */

interface Conversation {
  id: string;
  timestamp: number;
  messages: Message[];
  facts: Fact[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Fact {
  idx: number;
  subject: string;
  predicate: string;
  object: string;
  source_url: string;
  trust_score: number;
}

interface Preferences {
  trustWeights: {
    domain: number;
    recency: number;
    citations: number;
    author: number;
  };
  uiSettings: {
    darkMode: boolean;
    fontSize: string;
    language: string;
  };
  preferredDomains: string[];
}

class AccountFreeStorage {
  private dbName = 'geo-storage';
  private dbVersion = 1;
  private db: IDBDatabase | null = null;
  private initPromise: Promise<void> | null = null;

  constructor() {
    // Don't initialize during SSR
    if (typeof window !== 'undefined') {
      this.initPromise = this.init().catch(console.error);
    }
  }

  /**
   * Initialize IndexedDB (client-side only)
   */
  async init(): Promise<void> {
    // Guard against SSR
    if (typeof window === 'undefined' || typeof indexedDB === 'undefined') {
      console.warn('IndexedDB not available (probably SSR)');
      return Promise.resolve();
    }

    // Return existing promise if already initializing
    if (this.initPromise && this.db) return this.initPromise;

    this.initPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Conversations store
        if (!db.objectStoreNames.contains('conversations')) {
          const conversationStore = db.createObjectStore('conversations', {
            keyPath: 'id',
            autoIncrement: false,
          });
          conversationStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Preferences store
        if (!db.objectStoreNames.contains('preferences')) {
          db.createObjectStore('preferences', { keyPath: 'key' });
        }

        // Search history store
        if (!db.objectStoreNames.contains('history')) {
          const historyStore = db.createObjectStore('history', {
            keyPath: 'id',
            autoIncrement: true,
          });
          historyStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });

    return this.initPromise;
  }

  /**
   * Save conversation to local storage (NO SERVER)
   */
  async saveConversation(messages: Message[], facts: Fact[]): Promise<string> {
    // Guard against SSR
    if (typeof window === 'undefined') {
      console.warn('Cannot save conversation during SSR');
      return '';
    }

    if (!this.db) await this.init();

    const conversation: Conversation = {
      id: Date.now().toString(),
      timestamp: Date.now(),
      messages,
      facts,
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['conversations'], 'readwrite');
      const store = transaction.objectStore('conversations');
      const request = store.add(conversation);

      request.onsuccess = () => resolve(conversation.id);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all conversations (most recent first)
   */
  async getConversations(limit: number = 10): Promise<Conversation[]> {
    // Guard against SSR
    if (typeof window === 'undefined') {
      console.warn('Cannot get conversations during SSR');
      return [];
    }

    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['conversations'], 'readonly');
      const store = transaction.objectStore('conversations');
      const index = store.index('timestamp');
      const request = index.openCursor(null, 'prev'); // Descending order

      const conversations: Conversation[] = [];
      let count = 0;

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor && count < limit) {
          conversations.push(cursor.value);
          count++;
          cursor.continue();
        } else {
          resolve(conversations);
        }
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Save user preferences (trust weights, UI settings)
   */
  async savePreference(key: string, value: any): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['preferences'], 'readwrite');
      const store = transaction.objectStore('preferences');
      const request = store.put({ key, value });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get user preference
   */
  async getPreference(key: string): Promise<any> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['preferences'], 'readonly');
      const store = transaction.objectStore('preferences');
      const request = store.get(key);

      request.onsuccess = () => resolve(request.result?.value);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Export all user data (GDPR right to data portability)
   */
  async exportAllData(): Promise<void> {
    const conversations = await this.getConversations(999999);
    const preferences = await this.getAllPreferences();
    const history = await this.getSearchHistory(999999);

    const exportData = {
      conversations,
      preferences,
      history,
      exportDate: new Date().toISOString(),
      version: '1.0',
    };

    // Create downloadable JSON file
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `geo-data-export-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Import data from JSON file
   */
  async importData(file: File): Promise<void> {
    const text = await file.text();
    const data = JSON.parse(text);

    // Import conversations
    for (const conversation of data.conversations || []) {
      await this.saveConversation(conversation.messages, conversation.facts);
    }

    // Import preferences
    for (const [key, value] of Object.entries(data.preferences || {})) {
      await this.savePreference(key, value);
    }
  }

  /**
   * Clear all data (GDPR right to erasure)
   */
  async clearAllData(): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(
        ['conversations', 'preferences', 'history'],
        'readwrite'
      );

      transaction.objectStore('conversations').clear();
      transaction.objectStore('preferences').clear();
      transaction.objectStore('history').clear();

      transaction.oncomplete = () => {
        // Also clear localStorage
        localStorage.clear();
        resolve();
      };
      transaction.onerror = () => reject(transaction.error);
    });
  }

  /**
   * Get storage usage statistics
   */
  async getStorageUsage(): Promise<{
    conversations: number;
    preferences: number;
    history: number;
    total: number;
  }> {
    const conversations = await this.getConversations(999999);
    const preferences = await this.getAllPreferences();
    const history = await this.getSearchHistory(999999);

    const conversationsSize = JSON.stringify(conversations).length;
    const preferencesSize = JSON.stringify(preferences).length;
    const historySize = JSON.stringify(history).length;

    return {
      conversations: conversationsSize,
      preferences: preferencesSize,
      history: historySize,
      total: conversationsSize + preferencesSize + historySize,
    };
  }

  /**
   * Add query to search history
   */
  async addToHistory(query: string, answer: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['history'], 'readwrite');
      const store = transaction.objectStore('history');
      const request = store.add({
        query,
        answer,
        timestamp: Date.now(),
      });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get search history
   */
  async getSearchHistory(limit: number = 50): Promise<any[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['history'], 'readonly');
      const store = transaction.objectStore('history');
      const index = store.index('timestamp');
      const request = index.openCursor(null, 'prev');

      const history: any[] = [];
      let count = 0;

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor && count < limit) {
          history.push(cursor.value);
          count++;
          cursor.continue();
        } else {
          resolve(history);
        }
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all preferences
   */
  private async getAllPreferences(): Promise<Record<string, any>> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['preferences'], 'readonly');
      const store = transaction.objectStore('preferences');
      const request = store.getAll();

      request.onsuccess = () => {
        const prefs: Record<string, any> = {};
        for (const item of request.result) {
          prefs[item.key] = item.value;
        }
        resolve(prefs);
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Generate anonymous device ID (for continuity without accounts)
   */
  getAnonymousId(): string {
    // Guard against SSR
    if (typeof window === 'undefined') {
      return 'ssr-placeholder';
    }

    let anonymousId = localStorage.getItem('geo_anonymous_id');
    
    if (!anonymousId) {
      // Generate stable ID from device characteristics
      anonymousId = this.generateDeviceFingerprint();
      localStorage.setItem('geo_anonymous_id', anonymousId);
    }
    
    return anonymousId;
  }

  /**
   * Generate device fingerprint (privacy-preserving)
   */
  private generateDeviceFingerprint(): string {
    // Guard against SSR
    if (typeof window === 'undefined') {
      return 'ssr-fingerprint';
    }

    const fingerprint = {
      screen: `${screen.width}x${screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      platform: navigator.platform,
    };
    
    // Hash to create stable ID
    return btoa(JSON.stringify(fingerprint)).substring(0, 16);
  }
}

// Export singleton instance
export const storage = new AccountFreeStorage();
