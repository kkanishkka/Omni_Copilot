'use client';

import { useState, useEffect, useCallback } from 'react';
import { getProfile } from '@/lib/api';

export interface UserProfile {
  user_id: string;
  email: string;
  name: string;
  picture?: string;
  integrations: {
    google_connected: boolean;
    notion_connected: boolean;
  };
}

const STORAGE_KEY = 'omni_user';

export function useUser() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        setLoading(false);
        return;
      }
      const parsed = JSON.parse(stored) as UserProfile;
      setUser(parsed);

      // Refresh from server to get latest integration status
      try {
        const fresh = await getProfile(parsed.user_id);
        const merged = { ...parsed, ...fresh };
        setUser(merged);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      } catch (err: any) {
        if (err?.response?.status === 404) {
          localStorage.removeItem(STORAGE_KEY);
          setUser(null);
        }
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const saveUser = useCallback((profile: UserProfile) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    setUser(profile);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!user) return;
    try {
      const fresh = await getProfile(user.user_id);
      const merged = { ...user, ...fresh };
      setUser(merged);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    } catch {}
  }, [user]);

  return { user, loading, saveUser, logout, refreshUser };
}
