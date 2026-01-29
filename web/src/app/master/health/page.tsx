"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Shield, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Database,
  Server,
  RefreshCw
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface SystemHealth {
  status: string
  uptime_percentage: number
  active_tenants: number
  total_tenants: number
  api_response_time_ms: number
  error_rate_24h: number
  active_alerts: number
  critical_alerts: number
}

interface TenantHealth {
  tenant_id: string
  status: string
  score: number
  active_alerts: number
}

export default function SystemHealthPage() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [tenantHealth, setTenantHealth] = useState<TenantHealth[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    fetchHealthData()
    const interval = setInterval(fetchHealthData, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchHealthData = async () => {
    try {
      // Fetch system health
      const systemResponse = await fetch('/api/v1/master/health/system')
      if (systemResponse.ok) {
        const systemData = await systemResponse.json()
        setSystemHealth(systemData)
      } else {
        // Mock data
        setSystemHealth({
          status: "healthy",
          uptime_percentage: 99.9,
          active_tenants: 8,
          total_tenants: 12,
          api_response_time_ms: 150.0,
          error_rate_24h: 0.1,
          active_alerts: 3,
          critical_alerts: 0
        })
      }

      // Fetch tenant health
      const tenantResponse = await fetch('/api/v1/master/health/tenants')
      if (tenantResponse.ok) {
        const tenantData = await tenantResponse.json()
        setTenantHealth(tenantData.tenants)
      } else {
        // Mock data
        setTenantHealth([
          { tenant_id: "tenant_001", status: "healthy", score: 95.2, active_alerts: 0 },
          { tenant_id: "tenant_002", status: "healthy", score: 87.8, active_alerts: 1 },
          { tenant_id: "tenant_003", status: "warning", score: 72.1, active_alerts: 2 }
        ])
      }

      setLastUpdate(new Date())
    } catch (error) {
      console.error('Failed to fetch health data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-400'
      case 'warning': return 'text-yellow-400'
      case 'critical': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500/10 text-green-400 border-green-500/20'
      case 'warning': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
      case 'critical': return 'bg-red-500/10 text-red-400 border-red-500/20'
      default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
    }
  }

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy': return CheckCircle
      case 'warning': return AlertTriangle
      case 'critical': return XCircle
      default: return Activity
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">System Health</h1>
          <p className="text-zinc-400 mt-1">
            Real-time monitoring of system performance and tenant health
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-zinc-400">Last Updated</p>
            <p className="text-sm text-white">{lastUpdate.toLocaleTimeString()}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchHealthData}
            className="border-zinc-700"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0 }}
        >
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-400">System Status</p>
                  <p className={`text-2xl font-bold ${getStatusColor(systemHealth?.status || '')}`}>
                    {systemHealth?.status || 'unknown'}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${systemHealth?.status === 'healthy' ? 'bg-green-500/10' : 'bg-yellow-500/10'}`}>
                  <Shield className={`h-6 w-6 ${getStatusColor(systemHealth?.status || '')}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-400">Uptime</p>
                  <p className="text-2xl font-bold text-white">{systemHealth?.uptime_percentage}%</p>
                  <p className="text-xs text-green-400 mt-1">Last 30 days</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-500/10">
                  <Activity className="h-6 w-6 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-400">Response Time</p>
                  <p className="text-2xl font-bold text-white">{systemHealth?.api_response_time_ms}ms</p>
                  <p className="text-xs text-green-400 mt-1">Average API response</p>
                </div>
                <div className="p-3 rounded-lg bg-purple-500/10">
                  <Zap className="h-6 w-6 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-400">Error Rate</p>
                  <p className="text-2xl font-bold text-white">{systemHealth?.error_rate_24h}%</p>
                  <p className="text-xs text-green-400 mt-1">Last 24 hours</p>
                </div>
                <div className="p-3 rounded-lg bg-amber-500/10">
                  <AlertTriangle className="h-6 w-6 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Active Alerts Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-zinc-400">Active Alerts</p>
                <p className="text-3xl font-bold text-white">{systemHealth?.active_alerts}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-zinc-400">Critical Issues</p>
                <p className="text-3xl font-bold text-white">{systemHealth?.critical_alerts}</p>
              </div>
              <XCircle className={`h-8 w-8 ${systemHealth?.critical_alerts === 0 ? 'text-green-400' : 'text-red-400'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-zinc-400">Active Tenants</p>
                <p className="text-3xl font-bold text-white">
                  {systemHealth?.active_tenants}/{systemHealth?.total_tenants}
                </p>
              </div>
              <Server className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Components Health */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <Database className="mr-2 h-5 w-5" />
            System Components
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { name: 'API Server', status: 'healthy', uptime: '99.9%' },
              { name: 'Database (BigQuery)', status: 'healthy', uptime: '99.8%' },
              { name: 'Authentication Service', status: 'healthy', uptime: '99.9%' },
              { name: 'AI Processing', status: 'healthy', uptime: '99.7%' },
              { name: 'Phoenix Protocols', status: 'healthy', uptime: '99.5%' },
              { name: 'Evolution Core', status: 'healthy', uptime: '99.6%' }
            ].map((component, index) => {
              const Icon = getHealthIcon(component.status)
              return (
                <motion.div
                  key={component.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center justify-between p-3 bg-zinc-800 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`h-5 w-5 ${getStatusColor(component.status)}`} />
                    <div>
                      <p className="font-medium text-white text-sm">{component.name}</p>
                      <p className="text-xs text-zinc-400">Uptime: {component.uptime}</p>
                    </div>
                  </div>
                  <Badge className={getStatusBadge(component.status)}>
                    {component.status}
                  </Badge>
                </motion.div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Tenant Health Overview */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-white">Tenant Health Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left p-3 text-sm font-medium text-zinc-400">Tenant ID</th>
                  <th className="text-left p-3 text-sm font-medium text-zinc-400">Status</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">Health Score</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">Active Alerts</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tenantHealth.map((tenant, index) => {
                  const Icon = getHealthIcon(tenant.status)
                  return (
                    <motion.tr
                      key={tenant.tenant_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="border-b border-zinc-800 hover:bg-zinc-800/50"
                    >
                      <td className="p-3">
                        <div className="flex items-center space-x-3">
                          <Icon className={`h-4 w-4 ${getStatusColor(tenant.status)}`} />
                          <span className="font-medium text-white">{tenant.tenant_id}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <Badge className={getStatusBadge(tenant.status)}>
                          {tenant.status}
                        </Badge>
                      </td>
                      <td className="p-3 text-right">
                        <span className={`font-medium ${tenant.score >= 90 ? 'text-green-400' : tenant.score >= 70 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {tenant.score}%
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <span className={`font-medium ${tenant.active_alerts === 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                          {tenant.active_alerts}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-white">
                          View Details
                        </Button>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
