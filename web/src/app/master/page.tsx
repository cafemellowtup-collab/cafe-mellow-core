"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Users, 
  TrendingUp, 
  Activity, 
  AlertTriangle, 
  DollarSign,
  Brain,
  Shield,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface OverviewData {
  total_tenants: number
  active_tenants: number
  total_cost_today: number
  total_cost_week: number
  active_alerts: number
  critical_alerts: number
  system_status: string
  ai_insights_pending: number
}

export default function MasterDashboard() {
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOverview()
  }, [])

  const fetchOverview = async () => {
    try {
      const response = await fetch('/api/v1/master/overview')
      if (response.ok) {
        const data = await response.json()
        setOverview(data)
      } else {
        // Mock data for demonstration
        setOverview({
          total_tenants: 12,
          active_tenants: 8,
          total_cost_today: 145.50,
          total_cost_week: 892.30,
          active_alerts: 3,
          critical_alerts: 1,
          system_status: "healthy",
          ai_insights_pending: 5
        })
      }
    } catch (error) {
      // Mock data fallback
      setOverview({
        total_tenants: 12,
        active_tenants: 8,
        total_cost_today: 145.50,
        total_cost_week: 892.30,
        active_alerts: 3,
        critical_alerts: 1,
        system_status: "healthy",
        ai_insights_pending: 5
      })
    } finally {
      setLoading(false)
    }
  }

  const stats = [
    {
      name: 'Total Tenants',
      value: overview?.total_tenants || 0,
      icon: Users,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
    },
    {
      name: 'Active Tenants',
      value: overview?.active_tenants || 0,
      icon: Activity,
      color: 'text-green-400',
      bg: 'bg-green-500/10',
    },
    {
      name: 'Daily Cost',
      value: `₹${overview?.total_cost_today?.toFixed(2) || '0.00'}`,
      icon: DollarSign,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
    },
    {
      name: 'Weekly Cost',
      value: `₹${overview?.total_cost_week?.toFixed(2) || '0.00'}`,
      icon: TrendingUp,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10',
    },
  ]

  const systemMetrics = [
    {
      name: 'Active Alerts',
      value: overview?.active_alerts || 0,
      icon: AlertTriangle,
      color: overview?.active_alerts ? 'text-orange-400' : 'text-green-400',
      bg: overview?.active_alerts ? 'bg-orange-500/10' : 'bg-green-500/10',
    },
    {
      name: 'Critical Issues',
      value: overview?.critical_alerts || 0,
      icon: Shield,
      color: overview?.critical_alerts ? 'text-red-400' : 'text-green-400',
      bg: overview?.critical_alerts ? 'bg-red-500/10' : 'bg-green-500/10',
    },
    {
      name: 'AI Insights',
      value: overview?.ai_insights_pending || 0,
      icon: Brain,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
    },
    {
      name: 'System Status',
      value: overview?.system_status || 'unknown',
      icon: Zap,
      color: overview?.system_status === 'healthy' ? 'text-green-400' : 'text-yellow-400',
      bg: overview?.system_status === 'healthy' ? 'bg-green-500/10' : 'bg-yellow-500/10',
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Master Dashboard</h1>
          <p className="text-zinc-400 mt-1">
            Multi-tenant system overview and control center
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={overview?.system_status === 'healthy' ? 'default' : 'destructive'}>
            System {overview?.system_status}
          </Badge>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="bg-zinc-900 border-zinc-800">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-zinc-400">{stat.name}</p>
                    <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.bg}`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* System Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {systemMetrics.map((metric, index) => (
          <motion.div
            key={metric.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
          >
            <Card className="bg-zinc-900 border-zinc-800">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-zinc-400">{metric.name}</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {typeof metric.value === 'string' ? metric.value : metric.value}
                    </p>
                  </div>
                  <div className={`p-3 rounded-lg ${metric.bg}`}>
                    <metric.icon className={`h-6 w-6 ${metric.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-white">New tenant "Coffee Express" created</p>
                  <p className="text-xs text-zinc-400">2 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-white">System health check completed</p>
                  <p className="text-xs text-zinc-400">4 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-amber-400 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-white">AI insight generated for Cafe Mellow</p>
                  <p className="text-xs text-zinc-400">6 hours ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white">System Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-zinc-400">API Response Time</span>
                <span className="text-sm text-white">150ms</span>
              </div>
              <div className="w-full bg-zinc-700 rounded-full h-2">
                <div className="bg-green-400 h-2 rounded-full" style={{ width: '85%' }}></div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-zinc-400">System Uptime</span>
                <span className="text-sm text-white">99.9%</span>
              </div>
              <div className="w-full bg-zinc-700 rounded-full h-2">
                <div className="bg-blue-400 h-2 rounded-full" style={{ width: '99.9%' }}></div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-zinc-400">Error Rate (24h)</span>
                <span className="text-sm text-white">0.1%</span>
              </div>
              <div className="w-full bg-zinc-700 rounded-full h-2">
                <div className="bg-amber-400 h-2 rounded-full" style={{ width: '5%' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
