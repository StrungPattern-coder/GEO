"use client";
import { useState } from 'react';

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="text-xs px-2 py-1 rounded bg-slate-700 dark:bg-slate-800 hover:bg-slate-600 dark:hover:bg-slate-700 transition-colors"
      title={label}
    >
      {copied ? '✓ Copied!' : '📋 ' + label}
    </button>
  );
}
