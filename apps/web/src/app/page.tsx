"use client";
import Link from 'next/link';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function Page() {
  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-10">
        <h1 className="text-2xl font-semibold">GEO</h1>
        <div className="flex items-center gap-3">
          <nav className="text-sm text-slate-600 dark:text-slate-300 space-x-4">
            <Link href="/ask" className="hover:text-slate-900 dark:hover:text-slate-100">Ask</Link>
            <Link href="/admin" className="hover:text-slate-900 dark:hover:text-slate-100">Admin</Link>
            <Link href="/settings" className="hover:text-slate-900 dark:hover:text-slate-100">Settings</Link>
            <a href="/api/health" className="opacity-60 hover:opacity-100">API</a>
          </nav>
          <ThemeToggle />
        </div>
      </header>
      <section className="space-y-4">
        <h2 className="text-xl font-medium">Generative Engine</h2>
        <p className="text-slate-600 dark:text-slate-300">Trustworthy answers with inline citations. Start with Ask.</p>
        <div>
          <Link href="/ask" className="inline-block bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 px-4 py-2 rounded transition-colors">
            Open Ask →
          </Link>
        </div>
      </section>
    </main>
  );
}
