'use client';

import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Toaster } from '@/components/ui/sonner';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-white">
      <Sidebar />
      <Header />
      <main className="pl-64 pt-16">
        <div className="p-6">{children}</div>
      </main>
      <Toaster position="bottom-right" />
    </div>
  );
}
