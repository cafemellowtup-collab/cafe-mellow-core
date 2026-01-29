import { Metadata } from 'next'
import MasterSidebar from '@/components/master/MasterSidebar'

export const metadata: Metadata = {
  title: 'TITAN Master Dashboard',
  description: 'Multi-tenant management and system administration',
}

export default function MasterLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-zinc-950">
      <MasterSidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-6 py-8">
          {children}
        </div>
      </main>
    </div>
  )
}
