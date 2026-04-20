import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Omni Copilot — Your AI Productivity Assistant',
  description: 'Control Google Calendar, Drive, Gmail, and Notion through natural language. One AI. All your tools.',
  icons: { icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>✨</text></svg>" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="mesh-bg h-screen overflow-hidden antialiased">{children}</body>
    </html>
  );
}
