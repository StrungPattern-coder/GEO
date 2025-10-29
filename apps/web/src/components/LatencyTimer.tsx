"use client";
import { useEffect, useState } from 'react';

interface LatencyTimerProps {
  startTime: number | null;
  endTime: number | null;
  phases?: {
    retrieval?: number;
    generation?: number;
  };
}

export function LatencyTimer({ startTime, endTime, phases }: LatencyTimerProps) {
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    if (startTime && !endTime) {
      setIsRunning(true);
      const interval = setInterval(() => {
        setElapsed(Date.now() - startTime);
      }, 100);
      return () => clearInterval(interval);
    } else if (startTime && endTime) {
      setIsRunning(false);
      setElapsed(endTime - startTime);
    } else {
      setElapsed(0);
      setIsRunning(false);
    }
  }, [startTime, endTime]);

  if (!startTime) return null;

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
      <div className="flex items-center gap-2">
        <span className={isRunning ? 'animate-pulse' : ''}>⏱️</span>
        <span className="font-medium">
          {isRunning ? 'Thinking...' : 'Completed in'} {formatTime(elapsed)}
        </span>
      </div>
      
      {phases && !isRunning && (
        <div className="pl-5 space-y-0.5">
          {phases.retrieval != null && (
            <div>Retrieval: {formatTime(phases.retrieval)}</div>
          )}
          {phases.generation != null && (
            <div>Generation: {formatTime(phases.generation)}</div>
          )}
        </div>
      )}
    </div>
  );
}
