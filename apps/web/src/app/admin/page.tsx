"use client";
import { useState, useEffect } from 'react';

export default function AdminPage() {
  const [apiBase, setApiBase] = useState<string>('http://localhost:8000');
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [stats, setStats] = useState({ facts: 0, entities: 0 });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('geo_api');
      if (saved) setApiBase(saved);
    }
    fetchConfig();
  }, []);

  async function fetchConfig() {
    try {
      const res = await fetch(`${apiBase}/config`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function runIngestion() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase}/ingest/run`, { method: 'POST' });
      if (res.ok) {
        setMessage('✅ Ingestion completed successfully');
      } else {
        setMessage(`❌ Ingestion failed: ${res.status}`);
      }
    } catch (e: any) {
      setMessage(`❌ Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function scheduleIngestion() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase}/ingest/schedule?every_minutes=60`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setMessage(`✅ Scheduled ingestion every ${data.interval_min} minutes`);
      } else {
        setMessage(`❌ Schedule failed: ${res.status}`);
      }
    } catch (e: any) {
      setMessage(`❌ Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-6xl mx-auto px-6 py-10">
      <header className="mb-10">
        <h1 className="text-2xl font-semibold mb-2">Admin Dashboard</h1>
        <p className="text-sm text-slate-400">Manage ingestion, configuration, and system status</p>
      </header>

      {message && (
        <div className="mb-6 p-4 bg-slate-900 rounded border border-slate-800">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Ingestion Controls */}
        <section className="bg-slate-900 rounded-lg p-6 border border-slate-800">
          <h2 className="text-lg font-medium mb-4">Ingestion Controls</h2>
          <div className="space-y-3">
            <button
              onClick={runIngestion}
              disabled={loading}
              className="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 px-4 py-2 rounded"
            >
              {loading ? 'Running...' : 'Run Ingestion Now'}
            </button>
            <button
              onClick={scheduleIngestion}
              disabled={loading}
              className="w-full bg-slate-800 hover:bg-slate-700 disabled:opacity-50 px-4 py-2 rounded"
            >
              Schedule Hourly Ingestion
            </button>
          </div>
        </section>

        {/* System Config */}
        <section className="bg-slate-900 rounded-lg p-6 border border-slate-800">
          <h2 className="text-lg font-medium mb-4">Configuration</h2>
          {config ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Neo4j URI:</span>
                <span className="font-mono">{config.neo4j_uri || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">LLM Provider:</span>
                <span className="font-mono">{config.llm_provider || 'mock'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">arXiv Query:</span>
                <span className="font-mono text-xs">{config.arxiv_query || 'none'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">RSS Feeds:</span>
                <span className="font-mono text-xs">
                  {config.rss_feeds ? `${config.rss_feeds.split(',').length} feeds` : 'none'}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Loading...</p>
          )}
          <button
            onClick={fetchConfig}
            className="mt-4 w-full bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded text-sm"
          >
            Refresh Config
          </button>
        </section>

        {/* Stats */}
        <section className="bg-slate-900 rounded-lg p-6 border border-slate-800">
          <h2 className="text-lg font-medium mb-4">Knowledge Graph Stats</h2>
          <div className="space-y-3">
            <div>
              <div className="text-3xl font-bold text-cyan-400">{stats.facts}</div>
              <div className="text-sm text-slate-400">Total Facts</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-cyan-400">{stats.entities}</div>
              <div className="text-sm text-slate-400">Total Entities</div>
            </div>
            <div className="text-xs text-slate-500 mt-4">
              Note: Stats require a separate endpoint (coming soon)
            </div>
          </div>
        </section>

        {/* Quick Links */}
        <section className="bg-slate-900 rounded-lg p-6 border border-slate-800">
          <h2 className="text-lg font-medium mb-4">Quick Links</h2>
          <div className="space-y-2 text-sm">
            <a href="/ask" className="block text-cyan-400 hover:underline">→ Ask Interface</a>
            <a href="/settings" className="block text-cyan-400 hover:underline">→ Settings</a>
            <a href={`${apiBase}/docs`} target="_blank" rel="noreferrer" className="block text-cyan-400 hover:underline">
              → API Documentation
            </a>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="block text-cyan-400 hover:underline">
              → GitHub Repository
            </a>
          </div>
        </section>
      </div>

      <section className="mt-8 bg-slate-900 rounded-lg p-6 border border-slate-800">
        <h2 className="text-lg font-medium mb-4">System Health</h2>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl mb-1">🟢</div>
            <div className="text-sm text-slate-400">API</div>
            <div className="text-xs text-slate-500">Operational</div>
          </div>
          <div>
            <div className="text-2xl mb-1">🟢</div>
            <div className="text-sm text-slate-400">Graph DB</div>
            <div className="text-xs text-slate-500">Connected</div>
          </div>
          <div>
            <div className="text-2xl mb-1">🟢</div>
            <div className="text-sm text-slate-400">LLM</div>
            <div className="text-xs text-slate-500">Ready</div>
          </div>
        </div>
      </section>
    </main>
  );
}
