"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Bell, 
  AlertTriangle, 
  Info, 
  AlertCircle,
  CheckCircle,
  Plus,
  Search,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface Alert {
  alert_id: string
  tenant_id?: string
  severity: string
  category: string
  title: string
  message: string
  created_at: string
}

interface AlertSummary {
  info: number
  warning: number
  error: number
  critical: number
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [summary, setSummary] = useState<AlertSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [tenantFilter, setTenantFilter] = useState('all')
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  useEffect(() => {
    fetchAlerts()
    fetchAlertSummary()
  }, [severityFilter, categoryFilter, tenantFilter])

  const fetchAlerts = async () => {
    try {
      let url = '/api/v1/master/alerts?limit=100'
      if (severityFilter !== 'all') url += `&severity=${severityFilter}`
      if (tenantFilter !== 'all') url += `&tenant_id=${tenantFilter}`

      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setAlerts(data.alerts)
      } else {
        // Mock data for demonstration
        setAlerts([
          {
            alert_id: "alert_001",
            tenant_id: "tenant_001",
            severity: "warning",
            category: "performance",
            title: "High Response Time",
            message: "API response time exceeded 500ms threshold for Cafe Mellow Tiruppur",
            created_at: "2026-01-29T15:30:00Z"
          },
          {
            alert_id: "alert_002",
            severity: "critical",
            category: "system",
            title: "Database Connection Issues",
            message: "BigQuery connection experiencing intermittent failures",
            created_at: "2026-01-29T14:15:00Z"
          },
          {
            alert_id: "alert_003",
            tenant_id: "tenant_002",
            severity: "error",
            category: "data_quality",
            title: "Data Sync Failure",
            message: "Sales data sync failed for Coffee Express Chennai - missing API credentials",
            created_at: "2026-01-29T13:45:00Z"
          },
          {
            alert_id: "alert_004",
            tenant_id: "tenant_001",
            severity: "info",
            category: "usage",
            title: "API Limit Reached",
            message: "Tenant approaching daily API call limit (450/500)",
            created_at: "2026-01-29T12:20:00Z"
          },
          {
            alert_id: "alert_005",
            severity: "warning",
            category: "cost",
            title: "Cost Alert",
            message: "System-wide costs increased 15% compared to last week",
            created_at: "2026-01-29T11:10:00Z"
          }
        ])
      }
    } catch (error) {
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }

  const fetchAlertSummary = async () => {
    try {
      const response = await fetch('/api/v1/master/alerts/summary')
      if (response.ok) {
        const data = await response.json()
        setSummary(data.summary)
      } else {
        // Mock data
        setSummary({
          info: 12,
          warning: 8,
          error: 3,
          critical: 1
        })
      }
    } catch (error) {
      setSummary({ info: 0, warning: 0, error: 0, critical: 0 })
    }
  }

  const resolveAlert = async (alertId: string) => {
    try {
      await fetch(`/api/v1/master/alerts/${alertId}/resolve`, {
        method: 'POST'
      })
      // Refresh alerts
      fetchAlerts()
      fetchAlertSummary()
    } catch (error) {
      console.error('Failed to resolve alert:', error)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500/10 text-red-400 border-red-500/20'
      case 'error': return 'bg-orange-500/10 text-orange-400 border-orange-500/20'
      case 'warning': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
      case 'info': return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return AlertCircle
      case 'error': return AlertTriangle
      case 'warning': return AlertTriangle
      case 'info': return Info
      default: return Bell
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'system': return 'bg-red-500/10 text-red-400'
      case 'performance': return 'bg-orange-500/10 text-orange-400'
      case 'data_quality': return 'bg-yellow-500/10 text-yellow-400'
      case 'usage': return 'bg-blue-500/10 text-blue-400'
      case 'cost': return 'bg-purple-500/10 text-purple-400'
      default: return 'bg-gray-500/10 text-gray-400'
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.message.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter
    const matchesCategory = categoryFilter === 'all' || alert.category === categoryFilter
    const matchesTenant = tenantFilter === 'all' || (alert.tenant_id && alert.tenant_id === tenantFilter)
    
    return matchesSearch && matchesSeverity && matchesCategory && matchesTenant
  })

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
          <h1 className="text-3xl font-bold text-white">Alerts Management</h1>
          <p className="text-zinc-400 mt-1">
            Monitor and manage system alerts across all tenants
          </p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-amber-500 hover:bg-amber-600 text-black">
              <Plus className="w-4 h-4 mr-2" />
              Create Alert
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white">Create New Alert</DialogTitle>
              <DialogDescription className="text-zinc-400">
                Create a manual alert for system monitoring
              </DialogDescription>
            </DialogHeader>
            <CreateAlertForm onClose={() => setShowCreateDialog(false)} onSuccess={fetchAlerts} />
          </DialogContent>
        </Dialog>
      </div>

      {/* Alert Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Critical</p>
                  <p className="text-2xl font-bold text-red-400">{summary.critical}</p>
                </div>
                <AlertCircle className="h-8 w-8 text-red-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Errors</p>
                  <p className="text-2xl font-bold text-orange-400">{summary.error}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Warnings</p>
                  <p className="text-2xl font-bold text-yellow-400">{summary.warning}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Info</p>
                  <p className="text-2xl font-bold text-blue-400">{summary.info}</p>
                </div>
                <Info className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400 w-4 h-4" />
          <Input
            placeholder="Search alerts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-zinc-800 border-zinc-700 text-white placeholder-zinc-400"
          />
        </div>
        
        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-full sm:w-[150px] bg-zinc-800 border-zinc-700 text-white">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="all">All Severities</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="error">Error</SelectItem>
            <SelectItem value="warning">Warning</SelectItem>
            <SelectItem value="info">Info</SelectItem>
          </SelectContent>
        </Select>

        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full sm:w-[150px] bg-zinc-800 border-zinc-700 text-white">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="system">System</SelectItem>
            <SelectItem value="performance">Performance</SelectItem>
            <SelectItem value="data_quality">Data Quality</SelectItem>
            <SelectItem value="usage">Usage</SelectItem>
            <SelectItem value="cost">Cost</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert, index) => {
          const SeverityIcon = getSeverityIcon(alert.severity)
          return (
            <motion.div
              key={alert.alert_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-colors">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="p-2 rounded-lg bg-zinc-800">
                        <SeverityIcon className={`h-5 w-5 ${alert.severity === 'critical' ? 'text-red-400' : alert.severity === 'error' ? 'text-orange-400' : alert.severity === 'warning' ? 'text-yellow-400' : 'text-blue-400'}`} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="font-semibold text-white">{alert.title}</h3>
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                          <Badge variant="outline" className={getCategoryColor(alert.category)}>
                            {alert.category}
                          </Badge>
                          {alert.tenant_id && (
                            <span className="text-xs text-zinc-400 bg-zinc-800 px-2 py-1 rounded">
                              {alert.tenant_id}
                            </span>
                          )}
                        </div>
                        
                        <p className="text-zinc-300 text-sm mb-3">{alert.message}</p>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-zinc-500">
                            {new Date(alert.created_at).toLocaleString()}
                          </span>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => resolveAlert(alert.alert_id)}
                            className="text-xs border-zinc-700 hover:bg-zinc-800"
                          >
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Resolve
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {filteredAlerts.length === 0 && (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-12 text-center">
            <Bell className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No Alerts Found</h3>
            <p className="text-zinc-400">
              {alerts.length === 0 
                ? "No active alerts in the system. Everything looks good!" 
                : "No alerts match your current filters. Try adjusting the search criteria."
              }
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function CreateAlertForm({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    severity: 'info',
    category: 'system',
    title: '',
    message: '',
    tenant_id: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const payload = {
        ...formData,
        tenant_id: formData.tenant_id || null
      }
      
      const response = await fetch('/api/v1/master/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      if (response.ok) {
        onSuccess()
        onClose()
      }
    } catch (error) {
      console.error('Failed to create alert:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="severity" className="text-white">Severity</Label>
          <Select value={formData.severity} onValueChange={(value) => setFormData(prev => ({ ...prev, severity: value }))}>
            <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-800 border-zinc-700">
              <SelectItem value="info">Info</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
              <SelectItem value="error">Error</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label htmlFor="category" className="text-white">Category</Label>
          <Select value={formData.category} onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}>
            <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-800 border-zinc-700">
              <SelectItem value="system">System</SelectItem>
              <SelectItem value="performance">Performance</SelectItem>
              <SelectItem value="data_quality">Data Quality</SelectItem>
              <SelectItem value="usage">Usage</SelectItem>
              <SelectItem value="cost">Cost</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div>
        <Label htmlFor="title" className="text-white">Alert Title</Label>
        <Input
          id="title"
          value={formData.title}
          onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="Brief description of the alert"
          required
        />
      </div>
      
      <div>
        <Label htmlFor="message" className="text-white">Message</Label>
        <Textarea
          id="message"
          value={formData.message}
          onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="Detailed alert message"
          rows={3}
          required
        />
      </div>
      
      <div>
        <Label htmlFor="tenant_id" className="text-white">Tenant ID (Optional)</Label>
        <Input
          id="tenant_id"
          value={formData.tenant_id}
          onChange={(e) => setFormData(prev => ({ ...prev, tenant_id: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="Leave blank for system-wide alert"
        />
      </div>
      
      <div className="flex justify-end space-x-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-black">
          Create Alert
        </Button>
      </div>
    </form>
  )
}
