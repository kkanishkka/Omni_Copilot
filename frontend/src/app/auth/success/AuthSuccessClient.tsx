'use client';

import { useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useUser } from '@/hooks/useUser';
import { motion } from 'framer-motion';
import { Sparkles, CheckCircle } from 'lucide-react';

export default function AuthSuccessClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { saveUser } = useUser();

  useEffect(() => {
    const user_id = searchParams.get('user_id');
    const email = searchParams.get('email');
    const name = searchParams.get('name');
    const picture = searchParams.get('picture');
    const error = searchParams.get('error');

    if (error) {
      router.replace(`/?error=${encodeURIComponent(error)}`);
      return;
    }

    if (user_id && email && name) {
      saveUser({
        user_id,
        email: decodeURIComponent(email),
        name: decodeURIComponent(name),
        picture: picture ? decodeURIComponent(picture) : undefined,
        integrations: {
          google_connected: true,
          notion_connected: false,
        },
      });
      // Short delay so the user sees the success screen
      setTimeout(() => router.replace('/'), 800);
    } else {
      router.replace('/');
    }
  }, [searchParams, router, saveUser]);

  return (
    <div className="h-screen mesh-bg flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 260, damping: 22 }}
        className="flex flex-col items-center gap-5 text-center"
      >
        {/* Icon stack */}
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl gradient-brand flex items-center justify-center glow-brand">
            <Sparkles className="text-white" size={26} />
          </div>
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3, type: 'spring', stiffness: 300 }}
            className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center"
            style={{ background: 'var(--bg-base)', border: '2px solid var(--bg-base)' }}
          >
            <CheckCircle size={18} className="text-emerald-400" />
          </motion.div>
        </div>

        <div>
          <motion.p
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="text-base font-syne font-semibold text-[var(--text-primary)] mb-1"
          >
            Signing you in
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25 }}
            className="text-xs text-[var(--text-muted)]"
          >
            Connecting your Google account…
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex items-center gap-1.5"
        >
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand)] typing-dot" />
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand)] typing-dot" />
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--brand)] typing-dot" />
        </motion.div>
      </motion.div>
    </div>
  );
}
