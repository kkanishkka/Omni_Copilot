import { Suspense } from 'react';
import AuthSuccessClient from './AuthSuccessClient';

export default function AuthSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="h-screen mesh-bg flex items-center justify-center">
          <div className="text-[var(--text-muted)] text-sm">Loading…</div>
        </div>
      }
    >
      <AuthSuccessClient />
    </Suspense>
  );
}
