"use client";
import { useEffect, useMemo, useState } from 'react';

export default function AskPage() {
  const [apiBase, setApiBase] = useState<string>(process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000');
  const [q, setQ] = useState('What is new on the AI Google Blog?');
  const [answer, setAnswer] = useState<string | null>(null);
  const [facts, setFacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('geo_api');
      if (saved) setApiBase(saved);
    }
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null); setAnswer(''); setFacts([]); setSelectedIdx(null); setHoveredIdx(null);
    try {
      const res = await fetch(`${apiBase}/ask/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, max_facts: 8 })
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const reader = res.body?.getReader();
      if (!reader) throw new Error('No stream');
      const decoder = new TextDecoder();
      let gotHeader = false;
      let buffer = '';
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
              if (Array.isArray(j.facts)) setFacts(j.facts);
            } catch {}
            gotHeader = true;
            buffer = buffer.slice(nl + 1);
          } else {
            continue;
          }
        }
        if (buffer) {
          setAnswer(prev => (prev || '') + buffer);
          buffer = '';
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed');
    } finally {
      setLoading(false);
    }
  }

  const renderedAnswer = useMemo(() => {
    if (!answer) return null;
    // Wrap [n] markers in spans for hover highlight
    const parts: (string | JSX.Element)[] = [];
    const regex = /\[(\d+)\]/g;
    let lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = regex.exec(answer)) !== null) {
      const idx = parseInt(m[1], 10);
      parts.push(answer.slice(lastIndex, m.index));
      parts.push(
        <button
          key={`cit-${m.index}`}
          type="button"
          className={`px-1 rounded border ${hoveredIdx === idx || selectedIdx === idx ? 'bg-cyan-800/40 text-cyan-200 border-cyan-500' : 'bg-slate-800 text-slate-200 border-transparent'}`}
          onMouseEnter={() => setHoveredIdx(idx)}
          onMouseLeave={() => setHoveredIdx(null)}
          onClick={() => {
            setSelectedIdx(idx);
            const el = document.getElementById(`fact-${idx}`);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }}
        >
          [{idx}]
        </button>
      );
      lastIndex = m.index + m[0].length;
    }
    parts.push(answer.slice(lastIndex));
    return parts;
  }, [answer, hoveredIdx]);

  return (
    <main className="max-w-4xl mx-auto px-6 py-10">
      <div className="mb-6 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Ask</h1>
        <div className="flex items-center gap-2 text-sm">
          <label htmlFor="apiBase" className="text-slate-400">API</label>
          <input
            id="apiBase"
            className="w-72 bg-slate-900 border border-slate-800 rounded px-2 py-1"
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
            onBlur={() => { try { localStorage.setItem('geo_api', apiBase); } catch {} }}
            placeholder="http://localhost:8000"
          />
        </div>
      </div>
      <form onSubmit={onSubmit} className="flex gap-2 mb-6">
        <input value={q} onChange={e => setQ(e.target.value)}
          className="flex-1 bg-slate-900 border border-slate-800 rounded px-3 py-2"
          placeholder="Ask a question..." />
  <button disabled={loading} className="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded">
          {loading ? 'Thinking…' : 'Ask'}
        </button>
      </form>
      {error && <div className="text-red-400 mb-4">{error}</div>}
      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="h-20 bg-slate-800/50 rounded" />
          <div className="h-8 bg-slate-800/50 rounded" />
          <div className="h-8 bg-slate-800/50 rounded" />
        </div>
      )}
      {!loading && !answer && (
        <div className="text-sm text-slate-400">Ask a question to see an answer with citations.</div>
      )}
      {answer && (
        <div className="space-y-4">
          <div className="bg-slate-900 rounded p-4 leading-relaxed">{renderedAnswer}</div>
          <div className="space-y-2">
            {facts.map((f, i) => {
              const idx = f.idx || i + 1;
              const active = hoveredIdx === idx;
              return (
                <div
                  key={i}
                  id={`fact-${idx}`}
                  className={`bg-slate-900 rounded p-3 border ${active || selectedIdx === idx ? 'border-cyan-400' : 'border-slate-800'}`}
                  onMouseEnter={() => setHoveredIdx(idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                >
                  <b>[{idx}] {f.predicate}</b> {f.subject} → {f.object}
                  <div className="text-sm text-slate-400 mt-1">
                    {f.source_url && <a className="underline" href={f.source_url} target="_blank" rel="noreferrer">source</a>}
                    {typeof f.score === 'number' && <span> • score {Number(f.score).toFixed(2)}</span>}
                    {f.trust_score != null && <span> • trust {Number(f.trust_score).toFixed(2)}</span>}
                    {f.corroboration_count != null && <span> • corr {f.corroboration_count}</span>}
                    {f.recency_weight != null && <span> • rec {Number(f.recency_weight).toFixed(2)}</span>}
                    {f.ts && <span> • {f.ts}</span>}
                  </div>
                  {f.trust_explain && <div className="text-xs text-slate-500 mt-1">{f.trust_explain}</div>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </main>
  );
}
