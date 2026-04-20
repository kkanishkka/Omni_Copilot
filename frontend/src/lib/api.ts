import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function redirectToGoogleAuth(userId: string): Promise<void> {
  const { data } = await api.get(`/api/auth/google/login?user_id=${userId}`);
  window.location.href = data.auth_url;
}

export async function getProfile(userId: string) {
  const { data } = await api.get(`/api/auth/profile/${userId}`);
  return data;
}

export async function connectNotion(userId: string, token: string) {
  const { data } = await api.post(
    `/api/auth/notion/connect?user_id=${userId}&token=${token}`
  );
  return data;
}

export async function disconnectNotion(userId: string) {
  const { data } = await api.delete(`/api/auth/notion/disconnect/${userId}`);
  return data;
}

// ── Chat ──────────────────────────────────────────────────────────────────────
export async function sendMessage(payload: {
  user_id: string;
  session_id: string;
  message: string;
  file_context?: string;
}) {
  const { data } = await api.post('/api/chat/send', payload);
  return data;
}

export async function getSessions(userId: string) {
  const { data } = await api.get(`/api/chat/sessions/${userId}`);
  return data.sessions;
}

export async function getMessages(userId: string, sessionId: string) {
  const { data } = await api.get(`/api/chat/messages/${userId}/${sessionId}`);
  return data.messages;
}

export async function createSession(userId: string) {
  const { data } = await api.post(`/api/chat/sessions/${userId}`);
  return data.session_id;
}

export async function deleteSession(userId: string, sessionId: string) {
  const { data } = await api.delete(`/api/chat/sessions/${userId}/${sessionId}`);
  return data;
}

// ── Files ─────────────────────────────────────────────────────────────────────
export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/api/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

// ── Integrations ──────────────────────────────────────────────────────────────
export async function getIntegrationStatus(userId: string) {
  const { data } = await api.get(`/api/integrations/status/${userId}`);
  return data;
}
