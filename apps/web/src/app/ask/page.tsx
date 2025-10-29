"use client";
import { useEffect, useMemo, useState, useRef } from 'react';
import Link from 'next/link';
import { ThemeToggle } from '@/components/ThemeToggle';
import { CopyButton } from '@/components/CopyButton';
import { ExportButton } from '@/components/ExportButton';
import { LatencyTimer } from '@/components/LatencyTimer';
import { useToast } from '@/components/ToastProvider';

interface ChatMessage {
  id: string;
  query: string;
  answer: string;
  facts: any[];
  startTime: number;
  endTime: number;
  error?: string;
}

export default function AskPage() {
  const [apiBase, setApiBase] = useState<string>(process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000');
  const [q, setQ] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentAnswer, setCurrentAnswer] = useState<string>('');
  const [currentFacts, setCurrentFacts] = useState<any[]>([]);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const { showToast } = useToast();
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('geo_api');
      if (saved) setApiBase(saved);
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, currentAnswer]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    
    const messageId = Date.now().toString();
    const start = Date.now();
    const query = q.trim();
    
    setQ(''); // Clear input immediately
    setLoading(true);
    setCurrentAnswer('');
    setCurrentFacts([]);
    setSelectedIdx(null);
    setHoveredIdx(null);
    
    try {
      const res = await fetch(`${apiBase}/ask/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_facts: 8 })
      });
      
      if (!res.ok) throw new Error(`API ${res.status}`);
      
      const reader = res.body?.getReader();
      if (!reader) throw new Error('No stream');
      
      const decoder = new TextDecoder();
      let gotHeader = false;
      let buffer = '';
      let accumulatedAnswer = '';
      let facts: any[] = [];
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        if (!gotHeader) {
          const nl = buffer.indexOf('\n');
          if (nl !== -1) {
            const header = buffer.slice(0, nl);
            try {
              const j = JSON.parse(header);
              if (Array.isArray(j.facts)) {
                facts = j.facts;
                setCurrentFacts(facts);
                showToast(`Found ${facts.length} relevant sources`, 'success');
              }
            } catch {}
            gotHeader = true;
            buffer = buffer.slice(nl + 1);
          } else {
            continue;
          }
        }
        
        if (buffer) {
          accumulatedAnswer += buffer;
          setCurrentAnswer(accumulatedAnswer);
          buffer = '';
        }
      }
      
      const end = Date.now();
      
      // Add to chat history
      setChatHistory(prev => [...prev, {
        id: messageId,
        query,
        answer: accumulatedAnswer,
        facts,
        startTime: start,
        endTime: end
      }]);
      
      // Clear current state
      setCurrentAnswer('');
      setCurrentFacts([]);
      
    } catch (err: any) {
      const end = Date.now();
      showToast(err.message || 'Failed to get answer', 'error');
      
      // Add error message to history
      setChatHistory(prev => [...prev, {
        id: messageId,
        query,
        answer: '',
        facts: [],
        startTime: start,
        endTime: end,
        error: err.message || 'Failed'
      }]);
    } finally {
      setLoading(false);
    }
  }

  // Render answer with citations
  const renderAnswer = (answer: string, messageId: string) => {
    if (!answer) return null;
    
    const parts: (string | JSX.Element)[] = [];
    const regex = /\[(\d+)\]/g;
    let lastIndex = 0;
    let m: RegExpExecArray | null;
    
    while ((m = regex.exec(answer)) !== null) {
      const idx = parseInt(m[1], 10);
      parts.push(answer.slice(lastIndex, m.index));
      parts.push(
        <button
          key={`cit-${messageId}-${m.index}`}
          type="button"
          className={`
            px-1 rounded border transition-all
            ${hoveredIdx === idx || selectedIdx === idx 
              ? 'bg-cyan-100 dark:bg-cyan-800/40 text-cyan-800 dark:text-cyan-200 border-cyan-500' 
              : 'bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-transparent hover:border-slate-400 dark:hover:border-slate-600'
            }
          `}
          onMouseEnter={() => setHoveredIdx(idx)}
          onMouseLeave={() => setHoveredIdx(null)}
          onClick={() => {
            setSelectedIdx(idx);
            const el = document.getElementById(`fact-${messageId}-${idx}`);
            if (el) {
              el.scrollIntoView({ behavior: 'smooth', block: 'center' });
              showToast(`Scrolled to source [${idx}]`, 'info');
            }
          }}
          aria-label={`View source ${idx}`}
        >
          [{idx}]
        </button>
      );
      lastIndex = m.index + m[0].length;
    }
    parts.push(answer.slice(lastIndex));
    return parts;
  };

  return (
    <main className="min-h-screen flex flex-col max-w-6xl mx-auto px-4 sm:px-6 py-6">
      {/* Header */}
      <header className="mb-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-semibold">GEO Chat</h1>
          <Link 
            href="/" 
            className="text-sm text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            ← Home
          </Link>
          {chatHistory.length > 0 && (
            <button
              onClick={() => setChatHistory([])}
              className="text-sm text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
            >
              🗑️ Clear Chat
            </button>
          )}
        </div>
        
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 w-full lg:w-auto">
          <div className="flex items-center gap-2 text-sm w-full sm:w-auto">
            <label htmlFor="apiBase" className="text-slate-600 dark:text-slate-400 whitespace-nowrap">
              API
            </label>
            <input
              id="apiBase"
              className="flex-1 sm:w-72 bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              onBlur={() => {
                try {
                  localStorage.setItem('geo_api', apiBase);
                  showToast('API endpoint saved', 'success');
                } catch {}
              }}
              placeholder="http://localhost:8000"
            />
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-6">
        {chatHistory.length === 0 && !loading && (
          <div className="text-center py-12">
            <p className="text-slate-600 dark:text-slate-400 text-lg mb-2">
              💡 Start a conversation with GEO
            </p>
            <p className="text-slate-500 dark:text-slate-500 text-sm">
              Ask anything and get answers with real-time web sources
            </p>
          </div>
        )}

        {chatHistory.map((msg) => (
          <div key={msg.id} className="space-y-3">
            {/* User Query */}
            <div className="flex justify-end">
              <div className="bg-cyan-600 text-white rounded-lg px-4 py-2 max-w-[80%]">
                <p className="text-sm font-medium">{msg.query}</p>
              </div>
            </div>

            {/* AI Response */}
            <div className="flex justify-start">
              <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-800 max-w-[90%] w-full">
                {msg.error ? (
                  <div className="text-red-600 dark:text-red-400">
                    ⚠️ {msg.error}
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        ⏱️ {((msg.endTime - msg.startTime) / 1000).toFixed(1)}s
                      </div>
                      <CopyButton text={msg.answer} label="Copy" />
                    </div>
                    
                    <div className="leading-relaxed text-slate-800 dark:text-slate-200 mb-4">
                      {renderAnswer(msg.answer, msg.id)}
                    </div>

                    {/* Sources */}
                    {msg.facts.length > 0 && (
                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm font-semibold text-slate-700 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-400">
                          📚 {msg.facts.length} Sources
                        </summary>
                        <div className="mt-3 space-y-2">
                          {msg.facts.map((f: any, i: number) => {
                            const idx = f.idx || i + 1;
                            const active = hoveredIdx === idx || selectedIdx === idx;
                            
                            return (
                              <div
                                key={i}
                                id={`fact-${msg.id}-${idx}`}
                                className={`
                                  text-sm bg-white dark:bg-slate-800 rounded p-3 border transition-all
                                  ${active 
                                    ? 'border-cyan-500 shadow-md' 
                                    : 'border-slate-200 dark:border-slate-700'
                                  }
                                `}
                                onMouseEnter={() => setHoveredIdx(idx)}
                                onMouseLeave={() => setHoveredIdx(null)}
                              >
                                <div className="font-medium text-xs mb-1">
                                  <span className="text-cyan-600 dark:text-cyan-400">[{idx}]</span>{' '}
                                  {f.predicate}
                                </div>
                                
                                {f.source_url && (
                                  <a 
                                    href={f.source_url} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline flex items-center gap-1"
                                  >
                                    🔗 {new URL(f.source_url).hostname}
                                  </a>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </details>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Current loading state */}
        {loading && (
          <>
            {/* User Query */}
            <div className="flex justify-end">
              <div className="bg-cyan-600 text-white rounded-lg px-4 py-2 max-w-[80%]">
                <p className="text-sm font-medium">{chatHistory[chatHistory.length]?.query || 'Searching...'}</p>
              </div>
            </div>

            {/* Loading Response */}
            <div className="flex justify-start">
              <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-800 max-w-[90%] w-full">
                {currentAnswer ? (
                  <div className="leading-relaxed text-slate-800 dark:text-slate-200">
                    {renderAnswer(currentAnswer, 'current')}
                    <span className="inline-block w-2 h-4 bg-cyan-600 animate-pulse ml-1" />
                  </div>
                ) : (
                  <div className="space-y-2 animate-pulse">
                    <div className="h-4 bg-slate-200 dark:bg-slate-800/50 rounded w-3/4" />
                    <div className="h-4 bg-slate-200 dark:bg-slate-800/50 rounded w-full" />
                    <div className="h-4 bg-slate-200 dark:bg-slate-800/50 rounded w-2/3" />
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Form - Fixed at bottom */}
      <form onSubmit={onSubmit} className="flex gap-2 p-4 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 sticky bottom-0">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          disabled={loading}
          className="flex-1 bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg px-4 py-3 focus:ring-2 focus:ring-cyan-500 focus:border-transparent disabled:opacity-50"
          placeholder="Ask anything..."
          aria-label="Query input"
        />
        <button
          type="submit"
          disabled={loading || !q.trim()}
          className="bg-cyan-600 hover:bg-cyan-700 text-white px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap font-medium"
          aria-label="Submit query"
        >
          {loading ? '🤔' : '🚀'}
        </button>
      </form>
    </main>
  );
}
