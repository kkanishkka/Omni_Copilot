'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { redirectToGoogleAuth } from '@/lib/api';
import { useUser } from '@/hooks/useUser';
import { useChat } from '@/hooks/useChat';
import Sidebar from '@/components/sidebar/Sidebar';
import MessageBubble, { TypingIndicator } from '@/components/chat/MessageBubble';
import ChatInput from '@/components/chat/ChatInput';
import { Sparkles, Calendar, FileText, Mail, BookOpen, ArrowRight, Shield, Zap, Globe } from 'lucide-react';
import toast from 'react-hot-toast';

const FEATURES = [
  { icon: Calendar, label: 'Calendar', desc: 'Schedule & manage events' },
  { icon: FileText, label: 'Drive', desc: 'Find & organize files' },
  { icon: Mail, label: 'Gmail', desc: 'Summarize & send emails' },
  { icon: BookOpen, label: 'Notion', desc: 'Create & edit pages' },
];

const TRUST_BADGES = [
  { icon: Shield, text: 'End-to-end encrypted' },
  { icon: Zap, text: 'Sub-second responses' },
  { icon: Globe, text: 'Works across all tools' },
];

function LandingPage() {
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      await redirectToGoogleAuth('new');
    } catch {
      toast.error('Failed to start login. Is the backend running?');
      setLoading(false);
    }
  };

  return (
    <div className="h-screen mesh-bg flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-0 left-1/3 w-[600px] h-[400px] rounded-full opacity-30 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(91,122,255,0.18) 0%, transparent 70%)', filter: 'blur(40px)' }} />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[350px] rounded-full opacity-20 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(167,139,250,0.2) 0%, transparent 70%)', filter: 'blur(40px)' }} />
      <div className="absolute inset-0 pointer-events-none"
        style={{ backgroundImage: 'radial-gradient(rgba(91,122,255,0.04) 1px, transparent 1px)', backgroundSize: '28px 28px' }} />

      <motion.div
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-lg z-10 flex flex-col items-center"
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.05, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="mb-8 relative"
        >
          <div className="w-16 h-16 rounded-2xl gradient-brand flex items-center justify-center glow-brand shadow-2xl">
            <Sparkles className="text-white" size={26} />
          </div>
          <div className="absolute -inset-2 rounded-3xl opacity-20 blur-xl gradient-brand" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.55, ease: 'easeOut' }}
          className="text-center mb-3"
        >
          <h1 className="text-5xl font-bold font-syne leading-tight mb-3">
            Your AI Copilot<br />
            for <span className="gradient-text-warm">Everything</span>
          </h1>
          <p className="text-[var(--text-secondary)] text-base leading-relaxed max-w-sm mx-auto">
            One intelligent interface. All your tools unified — powered by AI that truly understands your context.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.45 }}
          className="flex flex-wrap justify-center gap-2 mb-8"
        >
          {FEATURES.map((f) => (
            <div key={f.label} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs text-[var(--text-secondary)] border border-[var(--border)]">
              <f.icon size={11} className="text-[var(--brand-light)]" />
              <span>{f.label}</span>
            </div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.33, duration: 0.4 }}
          className="w-full flex flex-col gap-3 mb-7"
        >
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="w-full group relative flex items-center justify-center gap-3 py-3.5 px-6 rounded-2xl font-dm font-semibold text-sm text-white transition-all duration-200 overflow-hidden disabled:opacity-60 disabled:cursor-not-allowed"
            style={{
              background: 'linear-gradient(135deg, #5b7aff 0%, #8b5cf6 100%)',
              boxShadow: loading ? 'none' : '0 4px 24px rgba(91,122,255,0.4), 0 1px 0 rgba(255,255,255,0.1) inset',
            }}
          >
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ background: 'linear-gradient(135deg, #6b88ff 0%, #9b6cf6 100%)' }} />
            {loading ? (
              <div className="relative flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Redirecting to Google…</span>
              </div>
            ) : (
              <div className="relative flex items-center gap-3">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="white" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="rgba(255,255,255,0.85)" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="rgba(255,255,255,0.7)" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="rgba(255,255,255,0.9)" />
                </svg>
                <span>Continue with Google</span>
                <ArrowRight size={15} className="ml-0.5 group-hover:translate-x-0.5 transition-transform" />
              </div>
            )}
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.4 }}
          className="flex items-center justify-center gap-5 mb-4"
        >
          {TRUST_BADGES.map((b) => (
            <div key={b.text} className="flex items-center gap-1.5">
              <b.icon size={11} className="text-[var(--text-muted)]" />
              <span className="text-[10px] text-[var(--text-muted)]">{b.text}</span>
            </div>
          ))}
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.58, duration: 0.4 }}
          className="text-[10px] text-[var(--text-muted)] text-center"
        >
          By continuing you agree to our Terms of Service. Your data is encrypted and never sold.
        </motion.p>
      </motion.div>
    </div>
  );
}

const EXAMPLES = [
  { icon: '📅', text: 'Create a Google Meet at 7 PM today', color: 'rgba(91,122,255,0.08)' },
  { icon: '📄', text: 'Fetch my resume from Drive and summarize it', color: 'rgba(139,92,246,0.08)' },
  { icon: '📧', text: 'Summarize my unread emails', color: 'rgba(91,122,255,0.08)' },
  { icon: '📓', text: 'Write an About Me page in Notion', color: 'rgba(167,139,250,0.08)' },
];

function ChatApp() {
  const { user, logout, refreshUser } = useUser();
  const {
    sessions, currentSessionId, messages, loading,
    loadSessions, selectSession, newSession, deleteSession, send, editAndResend,
  } = useChat(user?.user_id ?? null);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (user?.user_id) loadSessions();
  }, [user?.user_id, loadSessions]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  if (!user) return null;

  const currentSession = sessions.find((s) => s.session_id === currentSessionId);

  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar
        user={user}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={selectSession}
        onNewSession={newSession}
        onDeleteSession={deleteSession}
        onLogout={logout}
        onRefreshUser={refreshUser}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[var(--bg-base)]">
        {/* Top bar */}
        <div className="h-[58px] flex-shrink-0 flex items-center px-5 gap-3 border-b border-[var(--border)]"
          style={{ background: 'var(--glass-strong)', backdropFilter: 'blur(24px)' }}>
          <div className="flex-1 min-w-0">
            {currentSession ? (
              <p className="text-sm font-dm font-medium text-[var(--text-secondary)] truncate">
                {currentSession.title}
              </p>
            ) : (
              <p className="text-sm text-[var(--text-muted)] font-dm">New conversation</p>
            )}
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {user.integrations?.google_connected && (
              <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-mono font-medium"
                style={{ background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.2)', color: '#34d399' }}>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
                Google Connected
              </span>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 md:px-10 py-7">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center justify-center h-full gap-8"
            >
              <div className="text-center">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
                  className="w-14 h-14 rounded-2xl gradient-brand mx-auto mb-5 flex items-center justify-center glow-brand"
                >
                  <Sparkles className="text-white" size={22} />
                </motion.div>
                <h2 className="text-2xl font-syne font-semibold mb-2 gradient-text">
                  What can I help you with?
                </h2>
                <p className="text-sm text-[var(--text-muted)] max-w-xs mx-auto leading-relaxed">
                  Ask me anything about your calendar, files, emails, or notes.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-lg">
                {EXAMPLES.map((ex, i) => (
                  <motion.button
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.12 + i * 0.07 }}
                    onClick={() => send(ex.text)}
                    className="flex items-start gap-3 p-4 rounded-xl text-left transition-all group border border-[var(--border)] hover:border-[var(--border-hover)] hover:scale-[1.01]"
                    style={{ background: ex.color }}
                  >
                    <span className="text-xl flex-shrink-0 mt-0.5">{ex.icon}</span>
                    <span className="text-xs text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors leading-snug">
                      {ex.text}
                    </span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-5">
              <AnimatePresence>
                {messages.map((msg, i) => (
                  <MessageBubble
                    key={msg.id}
                    message={msg}
                    isLast={i === messages.length - 1}
                    onEdit={editAndResend}
                    editDisabled={loading}
                  />
                ))}
                {loading && (
                  <motion.div
                    key="typing"
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 6 }}
                  >
                    <TypingIndicator />
                  </motion.div>
                )}
              </AnimatePresence>
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="flex-shrink-0 max-w-3xl w-full mx-auto">
          <ChatInput onSend={send} disabled={loading} />
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const { user, loading } = useUser();

  if (loading) {
    return (
      <div className="h-screen mesh-bg flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <div className="w-12 h-12 rounded-2xl gradient-brand flex items-center justify-center glow-brand">
            <Sparkles className="text-white" size={20} />
          </div>
          <div className="flex gap-1.5 items-center">
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand)] typing-dot" />
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand)] typing-dot" />
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand)] typing-dot" />
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--bg-surface-2)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            fontSize: '13px',
            fontFamily: 'DM Sans, sans-serif',
            borderRadius: '12px',
            padding: '10px 14px',
          },
          success: { iconTheme: { primary: '#34d399', secondary: 'transparent' } },
          error: { iconTheme: { primary: '#f87171', secondary: 'transparent' } },
        }}
      />
      {user ? <ChatApp /> : <LandingPage />}
    </>
  );
}
