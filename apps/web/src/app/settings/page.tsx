"use client";
import { useState, useEffect } from 'react';

export default function SettingsPage() {
  const [api, setApi] = useState('http://localhost:8000');
  useEffect(() => {
    const saved = localStorage.getItem('geo_api');
    if (saved) setApi(saved);
  }, []);
  function save() {
    localStorage.setItem('geo_api', api);
    alert('Saved');
  }
  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold mb-6">Settings</h1>
      <div className="space-y-4">
        <label className="block text-sm text-slate-300">API Base URL</label>
        <input value={api} onChange={e=>setApi(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2" />
        <button onClick={save} className="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded">Save</button>
      </div>
    </main>
  );
}
