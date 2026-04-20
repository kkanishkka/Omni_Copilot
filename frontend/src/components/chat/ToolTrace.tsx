'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, CheckCircle, XCircle, Loader, Zap } from 'lucide-react';
import type { ToolTrace } from '@/hooks/useChat';

const TOOL_ICONS: Record<string, string> = {
  list_calendar_events: '📅',
  create_calendar_event: '📅',
  search_drive_files: '📁',
  get_drive_file_content: '📄',
  list_emails: '📧',
  get_email_content: '📧',
  send_email: '📤',
  search_notion_pages: '📓',
  get_notion_page: '📓',
  create_notion_page: '📓',
  append_to_notion_page: '📓',
};

interface ToolTraceProps {
  traces: ToolTrace[];
}

export default function ToolTraceView({ traces }: ToolTraceProps) {
  const [expanded, setExpanded] = useState(false);
  const [openSteps, setOpenSteps] = useState<Set<number>>(new Set());

  if (!traces || traces.length === 0) return null;

  const toggleStep = (i: number) => {
    setOpenSteps((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  const successCount = traces.filter((t) => t.status === 'success').length;
  const errorCount = traces.filter((t) => t.status === 'error').length;

  return (
    <div className="mt-2 mb-1">
      {/* Collapsed summary bar */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors group"
      >
        <Zap size={11} className="text-[var(--brand)]" />
        <span className="font-mono">
          {traces.length} tool{traces.length !== 1 ? 's' : ''} used
        </span>
        {successCount > 0 && (
          <span className="text-emerald-400/70">{successCount} ok</span>
        )}
        {errorCount > 0 && (
          <span className="text-red-400/70">{errorCount} err</span>
        )}
        <span className="text-[var(--brand)] group-hover:text-[var(--brand-light)] transition-colors">
          {expanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
        </span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1.5 border-l-2 border-[var(--border)] pl-3 ml-1">
              {traces.map((trace, i) => (
                <div key={i} className="rounded-md overflow-hidden">
                  {/* Step header */}
                  <button
                    onClick={() => toggleStep(i)}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md bg-[var(--bg-surface-2)] hover:bg-[var(--bg-surface-3)] transition-colors text-left"
                  >
                    <span className="text-sm leading-none">
                      {TOOL_ICONS[trace.tool_name] || '🔧'}
                    </span>
                    <span className="text-xs font-mono text-[var(--brand-light)] flex-1 truncate">
                      {trace.tool_name}
                    </span>
                    {trace.duration_ms !== undefined && (
                      <span className="text-[10px] text-[var(--text-muted)] font-mono ml-auto mr-1">
                        {trace.duration_ms}ms
                      </span>
                    )}
                    {trace.status === 'success' && (
                      <CheckCircle size={11} className="text-emerald-400 flex-shrink-0" />
                    )}
                    {trace.status === 'error' && (
                      <XCircle size={11} className="text-red-400 flex-shrink-0" />
                    )}
                    {trace.status === 'pending' && (
                      <Loader size={11} className="text-[var(--brand)] flex-shrink-0 animate-spin" />
                    )}
                    {openSteps.has(i) ? (
                      <ChevronDown size={10} className="text-[var(--text-muted)] flex-shrink-0" />
                    ) : (
                      <ChevronRight size={10} className="text-[var(--text-muted)] flex-shrink-0" />
                    )}
                  </button>

                  {/* Step detail */}
                  <AnimatePresence>
                    {openSteps.has(i) && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.15 }}
                        className="overflow-hidden"
                      >
                        <div className="px-2 py-2 bg-[rgba(10,10,24,0.6)] rounded-b-md space-y-2">
                          {/* Input */}
                          <div>
                            <div className="text-[9px] uppercase tracking-widest text-[var(--text-muted)] mb-1 font-mono">
                              Input
                            </div>
                            <pre className="text-[10px] font-mono text-[var(--text-secondary)] overflow-x-auto whitespace-pre-wrap break-all leading-relaxed">
                              {JSON.stringify(trace.input, null, 2)}
                            </pre>
                          </div>
                          {/* Output */}
                          {trace.output !== undefined && (
                            <div>
                              <div className="text-[9px] uppercase tracking-widest text-[var(--text-muted)] mb-1 font-mono">
                                Output
                              </div>
                              <pre className="text-[10px] font-mono text-[var(--text-secondary)] overflow-x-auto whitespace-pre-wrap break-all leading-relaxed max-h-32 overflow-y-auto">
                                {typeof trace.output === 'string'
                                  ? trace.output
                                  : JSON.stringify(trace.output, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
