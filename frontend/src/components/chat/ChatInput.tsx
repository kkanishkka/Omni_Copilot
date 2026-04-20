'use client';

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Paperclip, X, FileText, Mic } from 'lucide-react';
import { uploadFile } from '@/lib/api';
import toast from 'react-hot-toast';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [fileContext, setFileContext] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = useCallback(() => {
    const msg = value.trim();
    if (!msg || disabled) return;
    onSend(fileContext ? `${msg}\n\n[File: ${fileName}]\n${fileContext}` : msg);
    setValue('');
    setFileContext(null);
    setFileName(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, disabled, onSend, fileContext, fileName]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 180) + 'px';
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadFile(file);
      setFileContext(result.full_text);
      setFileName(file.name);
      toast.success(`"${file.name}" attached`);
    } catch {
      toast.error('Failed to upload file');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <div className="px-4 pb-5 pt-2">
      {/* File attachment preview */}
      <AnimatePresence>
        {fileName && (
          <motion.div
            initial={{ opacity: 0, height: 0, marginBottom: 0 }}
            animate={{ opacity: 1, height: 'auto', marginBottom: 8 }}
            exit={{ opacity: 0, height: 0, marginBottom: 0 }}
          >
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl w-fit max-w-full border border-[var(--border)]"
              style={{ background: 'rgba(91,122,255,0.07)' }}>
              <FileText size={13} className="text-[var(--brand-light)] flex-shrink-0" />
              <span className="text-xs text-[var(--text-secondary)] truncate max-w-[220px] font-mono">{fileName}</span>
              <button
                onClick={() => { setFileContext(null); setFileName(null); }}
                className="text-[var(--text-muted)] hover:text-red-400 transition-colors flex-shrink-0 ml-0.5"
              >
                <X size={12} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main input box */}
      <div
        className="flex items-end gap-2 px-3 py-2.5 rounded-2xl transition-all duration-200"
        style={{
          background: 'var(--glass-bg)',
          backdropFilter: 'blur(20px)',
          border: '1px solid var(--border)',
        }}
        onFocus={() => {}}
      >
        {/* Attach */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading || disabled}
          title="Attach file (PDF, DOCX, TXT)"
          className="flex-shrink-0 p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--brand-light)] hover:bg-[rgba(91,122,255,0.1)] transition-all disabled:opacity-40 mb-0.5"
        >
          {uploading ? (
            <div className="w-4 h-4 border border-[var(--brand)] border-t-transparent rounded-full animate-spin" />
          ) : (
            <Paperclip size={16} />
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileUpload}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask anything — Calendar, Drive, Gmail, Notion…"
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] resize-none outline-none leading-relaxed py-1.5 max-h-[180px] overflow-y-auto disabled:opacity-50 font-dm"
        />

        {/* Send */}
        <motion.button
          onClick={handleSend}
          disabled={!canSend}
          whileTap={canSend ? { scale: 0.88 } : {}}
          className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all mb-0.5"
          style={canSend ? {
            background: 'linear-gradient(135deg, #5b7aff 0%, #8b5cf6 100%)',
            boxShadow: '0 2px 12px rgba(91,122,255,0.4)',
          } : {
            background: 'var(--bg-surface-3)',
          }}
        >
          <Send size={13} className={canSend ? 'text-white' : 'text-[var(--text-muted)]'} />
        </motion.button>
      </div>

      <p className="text-center text-[10px] text-[var(--text-muted)] mt-2 opacity-50 font-mono">
        Enter to send · Shift+Enter for new line · PDF, DOCX, TXT supported
      </p>
    </div>
  );
}
