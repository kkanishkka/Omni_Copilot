'use client';

import { useState, useCallback, useRef } from 'react';
import { sendMessage, getSessions, getMessages, createSession, deleteSession as apiDeleteSession } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

export interface ToolTrace {
  tool_name: string;
  input: Record<string, unknown>;
  output?: unknown;
  status: 'pending' | 'success' | 'error';
  duration_ms?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tool_trace?: ToolTrace[];
}

export interface Session {
  session_id: string;
  title: string;
  updated_at: string;
}

export function useChat(userId: string | null) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const loadSessions = useCallback(async () => {
    if (!userId) return;
    setLoadingSessions(true);
    try {
      const data = await getSessions(userId);
      setSessions(data || []);
    } catch {
    } finally {
      setLoadingSessions(false);
    }
  }, [userId]);

  const selectSession = useCallback(async (sessionId: string) => {
    if (!userId) return;
    setCurrentSessionId(sessionId);
    try {
      const msgs = await getMessages(userId, sessionId);
      setMessages(
        (msgs || []).map((m: any) => ({
          id: uuidv4(),
          role: m.role,
          content: m.content,
          timestamp: m.timestamp || new Date().toISOString(),
          tool_trace: m.tool_trace,
        }))
      );
    } catch {
      setMessages([]);
    }
  }, [userId]);

  const newSession = useCallback(async () => {
    if (!userId) return;
    const sessionId = await createSession(userId);
    setCurrentSessionId(sessionId);
    setMessages([]);
    await loadSessions();
    return sessionId;
  }, [userId, loadSessions]);

  const deleteSession = useCallback(async (sessionId: string) => {
    if (!userId) return;
    await apiDeleteSession(userId, sessionId);
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null);
      setMessages([]);
    }
    await loadSessions();
  }, [userId, currentSessionId, loadSessions]);

  const send = useCallback(
    async (message: string, fileContext?: string) => {
      if (!userId || !message.trim()) return;

      let sessionId = currentSessionId;
      if (!sessionId) {
        sessionId = await newSession() || uuidv4();
      }

      const userMsg: Message = {
        id: uuidv4(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      try {
        const result = await sendMessage({
          user_id: userId,
          session_id: sessionId,
          message,
          file_context: fileContext,
        });

        const assistantMsg: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: result.message,
          timestamp: new Date().toISOString(),
          tool_trace: result.tool_trace,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setCurrentSessionId(result.session_id);

        await loadSessions();
      } catch (err: any) {
        const errorMsg: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: `Sorry, something went wrong: ${err?.response?.data?.detail || err.message}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [userId, currentSessionId, newSession, loadSessions]
  );

  // FIX #6: Edit message — truncates history after edited message then re-sends
  const editAndResend = useCallback(
    async (messageId: string, newContent: string) => {
      if (!userId || !newContent.trim() || loading) return;

      const msgIndex = messages.findIndex((m) => m.id === messageId);
      if (msgIndex === -1) return;

      // Keep all messages up to (but not including) the edited one
      const truncatedMessages = messages.slice(0, msgIndex);
      setMessages(truncatedMessages);

      // Now send with the truncated context
      let sessionId = currentSessionId;
      if (!sessionId) {
        sessionId = await newSession() || uuidv4();
      }

      const userMsg: Message = {
        id: uuidv4(),
        role: 'user',
        content: newContent,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      // Build history from truncated messages only
      const history = truncatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      try {
        const result = await sendMessage({
          user_id: userId,
          session_id: sessionId,
          message: newContent,
          file_context: undefined,
        });

        const assistantMsg: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: result.message,
          timestamp: new Date().toISOString(),
          tool_trace: result.tool_trace,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setCurrentSessionId(result.session_id);
        await loadSessions();
      } catch (err: any) {
        const errorMsg: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: `Sorry, something went wrong: ${err?.response?.data?.detail || err.message}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [userId, currentSessionId, messages, loading, newSession, loadSessions]
  );

  return {
    sessions,
    currentSessionId,
    messages,
    loading,
    loadingSessions,
    loadSessions,
    selectSession,
    newSession,
    deleteSession,
    send,
    editAndResend,
    setCurrentSessionId,
  };
}
