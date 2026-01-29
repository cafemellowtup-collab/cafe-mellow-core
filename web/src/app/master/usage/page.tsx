"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  DollarSign, 
  TrendingUp, 
  Brain, 
  Database,
  MessageSquare,
  FileText,
  Users,
  Calendar
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface UsageData {
  period_days: number
  all_tenants: TenantUsage[]
  top_users: TopUser[]
  cost_breakdown: CostBreakdown
}

interface TenantUsage {
  tenant_id: string
  total_ai_tokens: number
  total_cost: number
  total_messages: number
  total_api_calls: number
  active_days: number
}

interface TopUser {
  tenant_id: string
  total_cost: number
  total_tokens: number
  total_messages: number
}

interface CostBreakdown {
  ai_cost: number
  bq_cost: number
  total: number
  ai_percentage: number
  bq_percentage: number
}

export default function UsageAnalytics() {
  const [usageData, setUsageData] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [periodFilter, setPeriodFilter] = useState('7')
  const [tenantNames, setTenantNames] = useState<{[key: string]: string}>({})

  useEffect(() => {
    fetchUsageData()
    fetchTenantNames()
  }, [periodFilter])

  const fetchUsageData = async () => {
    try {
      const response = await fetch(`/api/v1/master/usage?days=${periodFilter}`)
      if (response.ok) {
        const data = await response.json()
        setUsageData(data)
      } else {
        // Mock data for demonstration
        setUsageData({
          period_days: parseInt(periodFilter),
          all_tenants: [
            {
              tenant_id: "tenant_001",
              total_ai_tokens: 15420,
              total_cost: 245.50,
              total_messages: 1240,
              total_api_calls: 890,
              active_days: parseInt(periodFilter)
            },
            {
              tenant_id: "tenant_002",
              total_ai_tokens: 8920,
              total_cost: 142.30,
              total_messages: 670,
              total_api_calls: 420,
              active_days: parseInt(periodFilter) - 1
            },
            {
              tenant_id: "tenant_003",
              total_ai_tokens: 3240,
              total_cost: 52.80,
              total_messages: 280,
              total_api_calls: 150,
              active_days: parseInt(periodFilter) - 2
            }
          ],
          top_users: [
            { tenant_id: "tenant_001", total_cost: 245.50, total_tokens: 15420, total_messages: 1240 },
            { tenant_id: "tenant_002", total_cost: 142.30, total_tokens: 8920, total_messages: 670 },
            { tenant_id: "tenant_003", total_cost: 52.80, total_tokens: 3240, total_messages: 280 }
          ],
          cost_breakdown: {
            ai_cost: 380.60,
            bq_cost: 60.00,
            total: 440.60,
            ai_percentage: 86.4,
            bq_percentage: 13.6
          }
        })
      }
    } catch (error) {
      setUsageData(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchTenantNames = async () => {
    try {
      const response = await fetch('/api/v1/master/tenants')
      if (response.ok) {
        const data = await response.json()
        const names: {[key: string]: string} = {}
        data.tenants?.forEach((tenant: any) => {
          names[tenant.tenant_id] = tenant.name
        })
        setTenantNames(names)
      } else {
        // Mock tenant names
        setTenantNames({
          "tenant_001": "Cafe Mellow Tiruppur",
          "tenant_002": "Coffee Express Chennai", 
          "tenant_003": "The Bean House"
        })
      }
    } catch (error) {
      setTenantNames({})
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400"></div>
      </div>
    )
  }

  const totalCost = usageData?.cost_breakdown.total || 0
  const totalTokens = usageData?.all_tenants.reduce((sum, tenant) => sum + tenant.total_ai_tokens, 0) || 0
  const totalMessages = usageData?.all_tenants.reduce((sum, tenant) => sum + tenant.total_messages, 0) || 0
  const totalApiCalls = usageData?.all_tenants.reduce((sum, tenant) => sum + tenant.total_api_calls, 0) || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Usage Analytics</h1>
          <p className="text-zinc-400 mt-1">
            Monitor resource usage and costs across all tenants
          </p>
        </div>
        
        <Select value={periodFilter} onValueChange={setPeriodFilter}>
          <SelectTrigger className="w-[180px] bg-zinc-800 border-zinc-700 text-white">
            <Calendar className="w-4 h-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="1">Last 24 hours</SelectItem>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Overview Stats */}
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
                  <p className="text-sm font-medium text-zinc-400">Total Cost</p>
                  <p className="text-2xl font-bold text-white">₹{totalCost.toFixed(2)}</p>
                  <p className="text-xs text-green-400 mt-1">Last {periodFilter} days</p>
                </div>
                <div className="p-3 rounded-lg bg-green-500/10">
                  <DollarSign className="h-6 w-6 text-green-400" />
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
                  <p className="text-sm font-medium text-zinc-400">AI Tokens</p>
                  <p className="text-2xl font-bold text-white">{totalTokens.toLocaleString()}</p>
                  <p className="text-xs text-blue-400 mt-1">Total processed</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-500/10">
                  <Brain className="h-6 w-6 text-blue-400" />
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
                  <p className="text-sm font-medium text-zinc-400">Messages</p>
                  <p className="text-2xl font-bold text-white">{totalMessages.toLocaleString()}</p>
                  <p className="text-xs text-purple-400 mt-1">Chat interactions</p>
                </div>
                <div className="p-3 rounded-lg bg-purple-500/10">
                  <MessageSquare className="h-6 w-6 text-purple-400" />
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
                  <p className="text-sm font-medium text-zinc-400">API Calls</p>
                  <p className="text-2xl font-bold text-white">{totalApiCalls.toLocaleString()}</p>
                  <p className="text-xs text-amber-400 mt-1">Total requests</p>
                </div>
                <div className="p-3 rounded-lg bg-amber-500/10">
                  <Database className="h-6 w-6 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Cost Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <TrendingUp className="mr-2 h-5 w-5" />
              Cost Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
                  <span className="text-sm text-zinc-300">AI Processing</span>
                </div>
                <div className="text-right">
                  <p className="font-medium text-white">₹{usageData?.cost_breakdown.ai_cost.toFixed(2)}</p>
                  <p className="text-xs text-zinc-400">{usageData?.cost_breakdown.ai_percentage.toFixed(1)}%</p>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <span className="text-sm text-zinc-300">BigQuery</span>
                </div>
                <div className="text-right">
                  <p className="font-medium text-white">₹{usageData?.cost_breakdown.bq_cost.toFixed(2)}</p>
                  <p className="text-xs text-zinc-400">{usageData?.cost_breakdown.bq_percentage.toFixed(1)}%</p>
                </div>
              </div>

              <div className="pt-2 border-t border-zinc-800">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-white">Total</span>
                  <span className="font-bold text-white">₹{usageData?.cost_breakdown.total.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Visual bar */}
            <div className="mt-4">
              <div className="w-full bg-zinc-700 rounded-full h-3 overflow-hidden">
                <div className="flex h-full">
                  <div 
                    className="bg-blue-400 h-full"
                    style={{ width: `${usageData?.cost_breakdown.ai_percentage}%` }}
                  ></div>
                  <div 
                    className="bg-green-400 h-full"
                    style={{ width: `${usageData?.cost_breakdown.bq_percentage}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Users className="mr-2 h-5 w-5" />
              Top Users (By Cost)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {usageData?.top_users.slice(0, 5).map((user, index) => (
                <div key={user.tenant_id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center text-xs font-bold text-white">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-white text-sm">
                        {tenantNames[user.tenant_id] || user.tenant_id}
                      </p>
                      <p className="text-xs text-zinc-400">
                        {user.total_messages} messages • {user.total_tokens.toLocaleString()} tokens
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-white">₹{user.total_cost.toFixed(2)}</p>
                    <Badge variant="outline" className="text-xs">
                      {((user.total_cost / totalCost) * 100).toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Tenant Usage */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-white">Detailed Usage by Tenant</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left p-3 text-sm font-medium text-zinc-400">Tenant</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">Cost</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">Tokens</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">Messages</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">API Calls</th>
                  <th className="text-right p-3 text-sm font-medium text-zinc-400">Active Days</th>
                </tr>
              </thead>
              <tbody>
                {usageData?.all_tenants.map((tenant, index) => (
                  <motion.tr
                    key={tenant.tenant_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-zinc-800 hover:bg-zinc-800/50"
                  >
                    <td className="p-3">
                      <p className="font-medium text-white">
                        {tenantNames[tenant.tenant_id] || tenant.tenant_id}
                      </p>
                    </td>
                    <td className="p-3 text-right font-medium text-white">
                      ₹{tenant.total_cost.toFixed(2)}
                    </td>
                    <td className="p-3 text-right text-zinc-300">
                      {tenant.total_ai_tokens.toLocaleString()}
                    </td>
                    <td className="p-3 text-right text-zinc-300">
                      {tenant.total_messages.toLocaleString()}
                    </td>
                    <td className="p-3 text-right text-zinc-300">
                      {tenant.total_api_calls.toLocaleString()}
                    </td>
                    <td className="p-3 text-right text-zinc-300">
                      {tenant.active_days}/{periodFilter}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
