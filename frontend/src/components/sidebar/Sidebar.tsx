'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus, MessageSquare, LogOut, ChevronLeft, ChevronRight,
  Calendar, HardDrive, Mail, BookOpen, CheckCircle, X, Trash2, Sparkles,
} from 'lucide-react';
import type { UserProfile } from '@/hooks/useUser';
import type { Session } from '@/hooks/useChat';
import { connectNotion, disconnectNotion, redirectToGoogleAuth } from '@/lib/api';
import toast from 'react-hot-toast';

interface SidebarProps {
  user: UserProfile;
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
  onLogout: () => void;
  onRefreshUser: () => void;
}

// ── Notion Modal ──────────────────────────────────────────────────────────────
function NotionModal({ userId, onClose, onSuccess }: {
  userId: string; onClose: () => void; onSuccess: () => void;
}) {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    if (!token.trim()) return;
    setLoading(true);
    try {
      await connectNotion(userId, token.trim());
      toast.success('Notion connected!');
      onSuccess();
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to connect Notion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94, y: 12 }}
        transition={{ type: 'spring', stiffness: 300, damping: 28 }}
        className="relative rounded-2xl p-6 w-full max-w-md z-10"
        style={{ background: 'var(--glass-strong)', border: '1px solid var(--border)', boxShadow: '0 24px 64px rgba(0,0,0,0.6)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(91,122,255,0.12)', border: '1px solid rgba(91,122,255,0.2)' }}>
              <BookOpen size={15} className="text-[var(--brand-light)]" />
            </div>
            <h3 className="font-syne font-semibold text-[var(--text-primary)]">Connect Notion</h3>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-2)] transition-all">
            <X size={15} />
          </button>
        </div>

        <div className="space-y-3 mb-5 text-sm text-[var(--text-secondary)]">
          <p className="text-xs leading-relaxed">Create an Internal Integration Token from your Notion workspace:</p>
          <ol className="space-y-2 text-xs">
            {[
              <>Go to <a href="https://www.notion.so/profile/integrations" target="_blank" rel="noreferrer" className="text-[var(--brand-light)] underline underline-offset-2">notion.so/profile/integrations</a> → click <strong className="text-[var(--text-primary)]">New integration</strong></>,
              <>Set permissions to <strong className="text-[var(--text-primary)]">Read + Write</strong>, then Submit</>,
              <>Copy the <strong className="text-[var(--text-primary)]">Internal Integration Secret</strong> (<code className="text-[10px] text-[var(--brand-light)]">secret_...</code> or <code className="text-[10px] text-[var(--brand-light)]">ntn_...</code>)</>,
              <>Paste below, then connect your Notion pages via <strong className="text-[var(--text-primary)]">··· → Add connections</strong></>,
            ].map((step, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-[var(--brand-light)] font-mono font-bold flex-shrink-0">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
          <div className="p-2.5 rounded-xl text-xs" style={{ background: 'rgba(251,191,36,0.07)', border: '1px solid rgba(251,191,36,0.18)', color: '#fbbf24' }}>
            ⚠️ After connecting, share your Notion pages with the integration to allow access.
          </div>
        </div>

        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
          placeholder="secret_xxxxxxxxxxxxxxxxxxxx"
          className="w-full rounded-xl px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none font-mono mb-3 transition-colors"
          style={{ background: 'var(--bg-surface-2)', border: '1px solid var(--border)' }}
          onFocus={(e) => { (e.target as HTMLInputElement).style.borderColor = 'var(--border-focus)'; }}
          onBlur={(e) => { (e.target as HTMLInputElement).style.borderColor = 'var(--border)'; }}
        />

        <div className="flex gap-2">
          <button onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-surface-2)] transition-colors"
            style={{ border: '1px solid var(--border)' }}>
            Cancel
          </button>
          <button onClick={handleConnect} disabled={loading || !token.trim()}
            className="flex-1 py-2.5 rounded-xl text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-opacity hover:opacity-90"
            style={{ background: 'linear-gradient(135deg, #5b7aff 0%, #8b5cf6 100%)' }}>
            {loading ? 'Connecting…' : 'Connect Notion'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── Delete Confirm Modal ──────────────────────────────────────────────────────
function DeleteConfirmModal({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onCancel}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 8 }}
        transition={{ type: 'spring', stiffness: 340, damping: 28 }}
        className="relative rounded-2xl p-5 w-full max-w-xs z-10 text-center"
        style={{ background: 'var(--glass-strong)', border: '1px solid var(--border)', boxShadow: '0 16px 48px rgba(0,0,0,0.5)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-3"
          style={{ background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.2)' }}>
          <Trash2 size={16} className="text-red-400" />
        </div>
        <h3 className="font-syne font-semibold text-[var(--text-primary)] mb-1.5 text-sm">Delete conversation?</h3>
        <p className="text-[11px] text-[var(--text-muted)] mb-4">This cannot be undone.</p>
        <div className="flex gap-2">
          <button onClick={onCancel}
            className="flex-1 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-surface-2)] transition-colors"
            style={{ border: '1px solid var(--border)' }}>
            Cancel
          </button>
          <button onClick={onConfirm}
            className="flex-1 py-2 rounded-xl text-xs text-white font-semibold transition-opacity hover:opacity-90"
            style={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}>
            Delete
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── Integration item ──────────────────────────────────────────────────────────
function IntegrationItem({ icon: Icon, label, connected, onConnect, onDisconnect }: {
  icon: any; label: string; connected: boolean; onConnect?: () => void; onDisconnect?: () => void;
}) {
  return (
    <div className="flex items-center gap-2 px-2.5 py-2 rounded-xl hover:bg-[var(--bg-surface-2)] transition-colors group cursor-default">
      <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${connected ? 'bg-[rgba(91,122,255,0.12)]' : 'bg-[var(--bg-surface-3)]'}`}>
        <Icon size={11} className={connected ? 'text-[var(--brand-light)]' : 'text-[var(--text-muted)]'} />
      </div>
      <span className={`text-xs flex-1 truncate ${connected ? 'text-[var(--text-secondary)]' : 'text-[var(--text-muted)]'}`}>
        {label}
      </span>
      {connected ? (
        <div className="flex items-center gap-1.5">
          <CheckCircle size={11} className="text-emerald-400 flex-shrink-0" />
          {onDisconnect && (
            <button onClick={onDisconnect}
              className="opacity-0 group-hover:opacity-100 text-[var(--text-muted)] hover:text-red-400 transition-all p-0.5 rounded"
              title="Disconnect">
              <X size={10} />
            </button>
          )}
        </div>
      ) : onConnect ? (
        <button onClick={onConnect}
          className="opacity-0 group-hover:opacity-100 text-[10px] text-[var(--brand-light)] transition-opacity font-mono px-1.5 py-0.5 rounded border border-[var(--brand)]/30 hover:bg-[var(--brand)]/10">
          Connect
        </button>
      ) : (
        <div className="w-2 h-2 rounded-full bg-[var(--bg-surface-3)]" />
      )}
    </div>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
export default function Sidebar({
  user, sessions, currentSessionId, onSelectSession,
  onNewSession, onDeleteSession, onLogout, onRefreshUser,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [showNotion, setShowNotion] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const google = user.integrations?.google_connected;
  const notion = user.integrations?.notion_connected;

  const handleGoogleConnect = async () => {
    try { await redirectToGoogleAuth(user.user_id); }
    catch { toast.error('Failed to start Google auth'); }
  };

  const handleNotionDisconnect = async () => {
    try {
      await disconnectNotion(user.user_id);
      toast.success('Notion disconnected');
      onRefreshUser();
    } catch { toast.error('Failed to disconnect Notion'); }
  };

  // FIX #5: Single-click delete → shows modal → one confirm click
  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setDeleteTarget(sessionId);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    const id = deleteTarget;
    setDeleteTarget(null);
    try {
      await onDeleteSession(id);
      toast.success('Conversation deleted');
    } catch {
      toast.error('Failed to delete');
    }
  };

  return (
    <>
      <AnimatePresence>
        {showNotion && (
          <NotionModal userId={user.user_id} onClose={() => setShowNotion(false)} onSuccess={onRefreshUser} />
        )}
        {deleteTarget && (
          <DeleteConfirmModal
            onConfirm={handleDeleteConfirm}
            onCancel={() => setDeleteTarget(null)}
          />
        )}
      </AnimatePresence>

      <motion.aside
        animate={{ width: collapsed ? 52 : 256 }}
        transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
        className="flex-shrink-0 flex flex-col h-full relative z-10 border-r border-[var(--border)]"
        style={{ background: 'var(--glass-strong)', overflow: 'hidden' }}
      >
        {/* Header */}
        <div className="flex items-center gap-2.5 px-3 py-4 border-b border-[var(--border)] min-h-[58px]">
          <div className="w-7 h-7 rounded-xl gradient-brand flex items-center justify-center flex-shrink-0 glow-sm">
            <Sparkles size={13} className="text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.p
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -6 }}
                transition={{ duration: 0.14 }}
                className="flex-1 min-w-0 text-sm font-syne font-semibold gradient-text truncate"
              >
                Omni Copilot
              </motion.p>
            )}
          </AnimatePresence>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex-shrink-0 p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-2)] transition-all"
          >
            {collapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
          </button>
        </div>

        {/* New chat */}
        <div className="px-2 py-2 border-b border-[var(--border)]">
          <button
            onClick={onNewSession}
            className={`w-full flex items-center gap-2 px-2 py-2 rounded-xl text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[rgba(91,122,255,0.07)] border border-transparent hover:border-[var(--border)] transition-all ${collapsed ? 'justify-center' : ''}`}
          >
            <Plus size={13} className="text-[var(--brand)] flex-shrink-0" />
            {!collapsed && <span className="font-dm text-xs">New Chat</span>}
          </button>
        </div>

        {/* Sessions */}
        {!collapsed && (
          <div className="flex-1 overflow-y-auto py-1.5 px-1.5 space-y-0.5">
            {sessions.length === 0 ? (
              <p className="text-[11px] text-[var(--text-muted)] px-2 py-4 text-center">
                No conversations yet
              </p>
            ) : (
              sessions.map((s) => (
                <div
                  key={s.session_id}
                  onClick={() => onSelectSession(s.session_id)}
                  className={`relative w-full flex items-center gap-2 px-2.5 py-2 rounded-xl text-xs transition-all group cursor-pointer ${
                    currentSessionId === s.session_id
                      ? 'text-[var(--text-primary)]'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-surface-2)]'
                  }`}
                  style={currentSessionId === s.session_id ? {
                    background: 'rgba(91,122,255,0.1)',
                    border: '1px solid rgba(91,122,255,0.18)',
                  } : { border: '1px solid transparent' }}
                >
                  <MessageSquare size={11} className="flex-shrink-0 opacity-50" />
                  <span className="truncate flex-1 font-dm">{s.title}</span>
                  {/* FIX #5: Single click → modal confirm */}
                  <button
                    onClick={(e) => handleDeleteClick(e, s.session_id)}
                    title="Delete conversation"
                    className="flex-shrink-0 p-0.5 rounded transition-all opacity-0 group-hover:opacity-60 hover:!opacity-100 text-[var(--text-muted)] hover:text-red-400"
                  >
                    <Trash2 size={10} />
                  </button>
                </div>
              ))
            )}
          </div>
        )}

        {collapsed && <div className="flex-1" />}

        {/* Integrations */}
        {!collapsed && (
          <div className="border-t border-[var(--border)] px-2 py-3 space-y-0.5">
            <p className="text-[9px] uppercase tracking-widest text-[var(--text-muted)] px-2.5 mb-2 font-mono">
              Integrations
            </p>
            <IntegrationItem icon={Calendar} label="Google Calendar" connected={!!google} onConnect={handleGoogleConnect} />
            <IntegrationItem icon={HardDrive} label="Google Drive" connected={!!google} onConnect={handleGoogleConnect} />
            <IntegrationItem icon={Mail} label="Gmail" connected={!!google} onConnect={handleGoogleConnect} />
            <IntegrationItem icon={BookOpen} label="Notion" connected={!!notion} onConnect={() => setShowNotion(true)} onDisconnect={handleNotionDisconnect} />
          </div>
        )}

        {/* User profile */}
        <div className={`border-t border-[var(--border)] p-2.5 flex items-center gap-2 ${collapsed ? 'justify-center' : ''}`}
          style={{ background: 'rgba(0,0,0,0.15)' }}>
          {user.picture ? (
            <img src={user.picture} alt={user.name} className="w-7 h-7 rounded-xl flex-shrink-0 object-cover ring-1 ring-[var(--border)]" />
          ) : (
            <div className="w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 text-xs text-[var(--text-secondary)] font-syne font-semibold"
              style={{ background: 'var(--bg-surface-3)', border: '1px solid var(--border)' }}>
              {user.name?.[0]?.toUpperCase()}
            </div>
          )}
          {!collapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-[var(--text-primary)] truncate font-dm">{user.name}</p>
                <p className="text-[10px] text-[var(--text-muted)] truncate font-mono">{user.email}</p>
              </div>
              <button
                onClick={onLogout}
                title="Sign out"
                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-all flex-shrink-0"
              >
                <LogOut size={12} />
              </button>
            </>
          )}
        </div>
      </motion.aside>
    </>
  );
}
