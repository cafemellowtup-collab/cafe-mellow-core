"use client";

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  Users, 
  BarChart3, 
  Shield, 
  Brain, 
  Settings,
  Activity,
  Bell,
  Zap,
  Crown
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  {
    name: 'Overview',
    href: '/master',
    icon: LayoutDashboard,
  },
  {
    name: 'Tenants',
    href: '/master/tenants',
    icon: Users,
  },
  {
    name: 'Usage Analytics',
    href: '/master/usage',
    icon: BarChart3,
  },
  {
    name: 'System Health',
    href: '/master/health',
    icon: Activity,
  },
  {
    name: 'AI Insights',
    href: '/master/ai',
    icon: Brain,
  },
  {
    name: 'Alerts',
    href: '/master/alerts',
    icon: Bell,
  },
  {
    name: 'Features',
    href: '/master/features',
    icon: Zap,
  },
  {
    name: 'Settings',
    href: '/master/settings',
    icon: Settings,
  },
]

export default function MasterSidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 bg-zinc-900 border-r border-zinc-800">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-zinc-800">
        <div className="flex items-center space-x-3">
          <Crown className="h-8 w-8 text-amber-400" />
          <div>
            <h1 className="text-lg font-bold text-white">TITAN Master</h1>
            <p className="text-xs text-zinc-400">System Control</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  : 'text-zinc-300 hover:text-white hover:bg-zinc-800'
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-zinc-800">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center">
            <Shield className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">Super Admin</p>
            <p className="text-xs text-zinc-400">System Administrator</p>
          </div>
        </div>
      </div>
    </div>
  )
}
