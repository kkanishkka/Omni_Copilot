'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '@/hooks/useChat';
import ToolTraceView from './ToolTrace';
import { Sparkles, Pencil, Check, X, Copy, CheckCheck } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  isLast?: boolean;
  onEdit?: (messageId: string, newContent: string) => void;
  editDisabled?: boolean;
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

export default function MessageBubble({ message, isLast, onEdit, editDisabled }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState(message.content);
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [editing]);

  const handleEditStart = () => {
    setEditValue(message.content);
    setEditing(true);
  };

  const handleEditCancel = () => {
    setEditing(false);
    setEditValue(message.content);
  };

  const handleEditSubmit = () => {
    const trimmed = editValue.trim();
    if (!trimmed || trimmed === message.content) {
      handleEditCancel();
      return;
    }
    onEdit?.(message.id, trimmed);
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleEditSubmit();
    }
    if (e.key === 'Escape') {
      handleEditCancel();
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} group`}
    >
      {/* AI Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-xl gradient-brand flex items-center justify-center flex-shrink-0 mt-0.5 glow-sm">
          <Sparkles size={14} className="text-white" />
        </div>
      )}

      <div className={`max-w-[80%] flex flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
        {isUser ? (
          <div className="flex flex-col gap-1.5 items-end w-full">
            <AnimatePresence mode="wait">
              {editing ? (
                <motion.div
                  key="edit"
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.97 }}
                  className="w-full"
                >
                  <div className="rounded-2xl rounded-tr-sm overflow-hidden"
                    style={{ border: '1.5px solid rgba(91,122,255,0.5)', background: 'rgba(18,18,42,0.95)' }}>
                    <textarea
                      ref={textareaRef}
                      value={editValue}
                      onChange={(e) => {
                        setEditValue(e.target.value);
                        e.target.style.height = 'auto';
                        e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
                      }}
                      onKeyDown={handleKeyDown}
                      rows={1}
                      className="w-full px-4 pt-3 pb-2 text-sm text-[var(--text-primary)] bg-transparent outline-none resize-none leading-relaxed font-dm"
                      style={{ minHeight: '44px', maxHeight: '200px' }}
                    />
                    <div className="flex items-center justify-end gap-1.5 px-3 pb-2.5">
                      <span className="text-[10px] text-[var(--text-muted)] mr-auto font-mono">Enter to send · Esc to cancel</span>
                      <button
                        onClick={handleEditCancel}
                        className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-2)] transition-all"
                      >
                        <X size={12} />
                      </button>
                      <button
                        onClick={handleEditSubmit}
                        disabled={!editValue.trim()}
                        className="p-1.5 rounded-lg text-emerald-400 hover:bg-emerald-500/10 transition-all disabled:opacity-40"
                      >
                        <Check size={12} />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="bubble"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed text-white relative"
                  style={{
                    background: 'linear-gradient(135deg, #5b7aff 0%, #7c5bf5 100%)',
                    boxShadow: '0 2px 20px rgba(91,122,255,0.28)',
                  }}
                >
                  {message.content}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Edit button — only on user messages, when not editing */}
            {!editing && onEdit && !editDisabled && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 0 }}
                whileHover={{ opacity: 1 }}
                className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] text-[var(--text-muted)] hover:text-[var(--brand-light)] transition-colors opacity-0 group-hover:opacity-100"
                style={{ border: '1px solid transparent' }}
                onClick={handleEditStart}
                title="Edit message"
              >
                <Pencil size={10} />
                <span className="font-mono">Edit</span>
              </motion.button>
            )}
          </div>
        ) : (
          <div
            className="px-4 py-3.5 rounded-2xl rounded-tl-sm text-sm leading-relaxed relative"
            style={{
              background: 'var(--glass-bg)',
              backdropFilter: 'blur(20px)',
              border: '1px solid var(--border)',
            }}
          >
            <div className="prose-chat">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
            {message.tool_trace && message.tool_trace.length > 0 && (
              <ToolTraceView traces={message.tool_trace} />
            )}

            {/* Copy button for AI messages */}
            <button
              onClick={handleCopy}
              className="absolute top-2.5 right-2.5 p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-surface-2)] transition-all opacity-0 group-hover:opacity-100"
              title="Copy response"
            >
              {copied ? <CheckCheck size={11} className="text-emerald-400" /> : <Copy size={11} />}
            </button>
          </div>
        )}

        {/* Timestamp */}
        <span className="text-[10px] text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity font-mono px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-xl border border-[var(--border)] flex items-center justify-center flex-shrink-0 mt-0.5 text-[var(--text-secondary)] text-xs font-syne font-semibold"
          style={{ background: 'var(--bg-surface-3)' }}>
          U
        </div>
      )}
    </motion.div>
  );
}

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="flex gap-3 justify-start"
    >
      <div className="w-8 h-8 rounded-xl gradient-brand flex items-center justify-center flex-shrink-0 glow-sm">
        <Sparkles size={14} className="text-white" />
      </div>
      <div className="px-4 py-3.5 rounded-2xl rounded-tl-sm flex items-center gap-1.5"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--border)' }}>
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand-light)] typing-dot" />
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand-light)] typing-dot" />
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand-light)] typing-dot" />
      </div>
    </motion.div>
  );
}
