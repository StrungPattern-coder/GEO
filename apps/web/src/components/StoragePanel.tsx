"use client";
import { useState, useEffect } from 'react';
import { storage } from '@/lib/accountFreeStorage';

interface StoragePanelProps {
  onClose: () => void;
}

export function StoragePanel({ onClose }: StoragePanelProps) {
  const [storageUsage, setStorageUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [anonymousId, setAnonymousId] = useState<string>('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const usage = await storage.getStorageUsage();
      setStorageUsage(usage);
      const id = storage.getAnonymousId();
      setAnonymousId(id);
    } catch (err) {
      console.error('Failed to load storage data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const handleExport = async () => {
    await storage.exportAllData();
  };

  const handleClearAll = async () => {
    if (confirm('⚠️ Delete ALL stored data? This cannot be undone.\n\nThis will delete:\n- All conversation history\n- All preferences\n- All search history\n\nYou can export your data first if needed.')) {
      await storage.clearAllData();
      await loadData();
      window.location.reload();
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await storage.importData(file);
      await loadData();
      alert('✅ Data imported successfully! Refresh the page to see your conversations.');
    } catch (err) {
      alert('❌ Failed to import data. Make sure the file is a valid GEO export.');
      console.error('Import error:', err);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-white dark:bg-slate-900 rounded-lg p-6 max-w-lg w-full mx-4 shadow-2xl">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-1/2"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-slate-900 rounded-lg p-6 max-w-2xl w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800 max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            📊 Account-Free Storage
          </h2>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Privacy Notice */}
        <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
            🔒 100% Private & Local
          </h3>
          <p className="text-sm text-green-800 dark:text-green-200">
            All your data is stored <strong>only in your browser</strong>. Nothing is sent to any server.
            You control your data completely. No account required, ever.
          </p>
        </div>

        {/* Storage Usage */}
        {storageUsage && (
          <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">
              💾 Storage Usage
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-slate-600 dark:text-slate-400">Conversations:</span>
                <span className="font-mono text-slate-900 dark:text-slate-100">
                  {formatBytes(storageUsage.conversations)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600 dark:text-slate-400">Preferences:</span>
                <span className="font-mono text-slate-900 dark:text-slate-100">
                  {formatBytes(storageUsage.preferences)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600 dark:text-slate-400">Search History:</span>
                <span className="font-mono text-slate-900 dark:text-slate-100">
                  {formatBytes(storageUsage.history)}
                </span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-slate-300 dark:border-slate-600 font-semibold">
                <span className="text-slate-900 dark:text-slate-100">Total:</span>
                <span className="font-mono text-slate-900 dark:text-slate-100">
                  {formatBytes(storageUsage.total)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Anonymous ID */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
            🆔 Device Identifier
          </h3>
          <p className="text-xs text-blue-700 dark:text-blue-300 mb-2">
            This anonymous ID helps maintain continuity across sessions without an account.
            It's generated from your device characteristics (not tracked, not sent anywhere).
          </p>
          <code className="text-xs font-mono bg-blue-100 dark:bg-blue-950 text-blue-900 dark:text-blue-100 p-2 rounded block break-all">
            {anonymousId}
          </code>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">
            ⚙️ Data Management
          </h3>
          
          {/* Export */}
          <button
            onClick={handleExport}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            <span>💾</span>
            <span>Export All Data (JSON)</span>
          </button>
          <p className="text-xs text-slate-500 dark:text-slate-400 -mt-2 ml-1">
            Download all conversations, preferences, and history as a JSON file
          </p>

          {/* Import */}
          <div>
            <label className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium cursor-pointer">
              <span>📥</span>
              <span>Import Data</span>
              <input
                type="file"
                accept=".json"
                onChange={handleImport}
                className="hidden"
              />
            </label>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 ml-1">
              Restore conversations from a previously exported JSON file
            </p>
          </div>

          {/* Clear All */}
          <button
            onClick={handleClearAll}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
          >
            <span>🔥</span>
            <span>Delete All Data</span>
          </button>
          <p className="text-xs text-red-500 dark:text-red-400 -mt-2 ml-1">
            ⚠️ Permanently delete all stored data. This cannot be undone!
          </p>
        </div>

        {/* GDPR Notice */}
        <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-800">
          <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
            <strong>GDPR Compliant:</strong> Your data never leaves your device.
            Export, import, or delete anytime. No tracking, no analytics, no surveillance.
          </p>
        </div>
      </div>
    </div>
  );
}
