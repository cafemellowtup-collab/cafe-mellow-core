"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Users, 
  Plus, 
  Search, 
  Filter,
  MoreVertical,
  Edit,
  Pause,
  Play,
  Trash2,
  Crown,
  Activity,
  AlertCircle
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface Tenant {
  tenant_id: string
  name: string
  email: string
  phone?: string
  plan: string
  status: string
  created_at: string
  last_activity?: string
  health_score: number
}

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [planFilter, setPlanFilter] = useState('all')
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  useEffect(() => {
    fetchTenants()
  }, [])

  const fetchTenants = async () => {
    try {
      const response = await fetch('/api/v1/master/tenants')
      if (response.ok) {
        const data = await response.json()
        setTenants(data.tenants)
      } else {
        // Mock data for demonstration
        setTenants([
          {
            tenant_id: "tenant_001",
            name: "Cafe Mellow Tiruppur",
            email: "owner@cafemellow.com",
            phone: "+91-9876543210",
            plan: "pro",
            status: "active",
            created_at: "2026-01-20T10:30:00Z",
            last_activity: "2026-01-29T15:45:00Z",
            health_score: 95.2
          },
          {
            tenant_id: "tenant_002", 
            name: "Coffee Express Chennai",
            email: "admin@coffeeexpress.com",
            phone: "+91-9876543211",
            plan: "free",
            status: "active",
            created_at: "2026-01-22T14:20:00Z",
            last_activity: "2026-01-29T12:30:00Z",
            health_score: 87.8
          },
          {
            tenant_id: "tenant_003",
            name: "The Bean House",
            email: "contact@beanhouse.com", 
            plan: "enterprise",
            status: "paused",
            created_at: "2026-01-15T09:15:00Z",
            last_activity: "2026-01-25T16:20:00Z",
            health_score: 72.1
          }
        ])
      }
    } catch (error) {
      setTenants([])
    } finally {
      setLoading(false)
    }
  }

  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tenant.email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || tenant.status === statusFilter
    const matchesPlan = planFilter === 'all' || tenant.plan === planFilter
    
    return matchesSearch && matchesStatus && matchesPlan
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/10 text-green-400 border-green-500/20'
      case 'paused': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
      case 'suspended': return 'bg-red-500/10 text-red-400 border-red-500/20'
      default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
    }
  }

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'free': return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      case 'pro': return 'bg-purple-500/10 text-purple-400 border-purple-500/20'
      case 'enterprise': return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
      default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-400'
    if (score >= 70) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Tenant Management</h1>
          <p className="text-zinc-400 mt-1">
            Manage all cafe tenants and their configurations
          </p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-amber-500 hover:bg-amber-600 text-black">
              <Plus className="w-4 h-4 mr-2" />
              Add Tenant
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white">Create New Tenant</DialogTitle>
              <DialogDescription className="text-zinc-400">
                Add a new cafe owner to the TITAN system
              </DialogDescription>
            </DialogHeader>
            <CreateTenantForm onClose={() => setShowCreateDialog(false)} onSuccess={fetchTenants} />
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Tenants</p>
                <p className="text-2xl font-bold text-white">{tenants.length}</p>
              </div>
              <Users className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Active</p>
                <p className="text-2xl font-bold text-white">
                  {tenants.filter(t => t.status === 'active').length}
                </p>
              </div>
              <Activity className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Enterprise</p>
                <p className="text-2xl font-bold text-white">
                  {tenants.filter(t => t.plan === 'enterprise').length}
                </p>
              </div>
              <Crown className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Issues</p>
                <p className="text-2xl font-bold text-white">
                  {tenants.filter(t => t.health_score < 80).length}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400 w-4 h-4" />
          <Input
            placeholder="Search tenants..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-zinc-800 border-zinc-700 text-white placeholder-zinc-400"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px] bg-zinc-800 border-zinc-700 text-white">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>

        <Select value={planFilter} onValueChange={setPlanFilter}>
          <SelectTrigger className="w-full sm:w-[180px] bg-zinc-800 border-zinc-700 text-white">
            <SelectValue placeholder="Plan" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="all">All Plans</SelectItem>
            <SelectItem value="free">Free</SelectItem>
            <SelectItem value="pro">Pro</SelectItem>
            <SelectItem value="enterprise">Enterprise</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Tenants Table */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left p-4 text-sm font-medium text-zinc-400">Tenant</th>
                  <th className="text-left p-4 text-sm font-medium text-zinc-400">Plan</th>
                  <th className="text-left p-4 text-sm font-medium text-zinc-400">Status</th>
                  <th className="text-left p-4 text-sm font-medium text-zinc-400">Health</th>
                  <th className="text-left p-4 text-sm font-medium text-zinc-400">Last Activity</th>
                  <th className="text-right p-4 text-sm font-medium text-zinc-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTenants.map((tenant, index) => (
                  <motion.tr
                    key={tenant.tenant_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-zinc-800 hover:bg-zinc-800/50"
                  >
                    <td className="p-4">
                      <div>
                        <p className="font-medium text-white">{tenant.name}</p>
                        <p className="text-sm text-zinc-400">{tenant.email}</p>
                        {tenant.phone && (
                          <p className="text-xs text-zinc-500">{tenant.phone}</p>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <Badge className={getPlanColor(tenant.plan)}>
                        {tenant.plan}
                      </Badge>
                    </td>
                    <td className="p-4">
                      <Badge className={getStatusColor(tenant.status)}>
                        {tenant.status}
                      </Badge>
                    </td>
                    <td className="p-4">
                      <span className={`font-medium ${getHealthColor(tenant.health_score)}`}>
                        {tenant.health_score}%
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-sm text-zinc-400">
                        {tenant.last_activity 
                          ? new Date(tenant.last_activity).toLocaleDateString()
                          : 'Never'
                        }
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-zinc-800 border-zinc-700">
                          <DropdownMenuItem className="text-white hover:bg-zinc-700">
                            <Edit className="mr-2 h-4 w-4" />
                            Edit Details
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-white hover:bg-zinc-700">
                            {tenant.status === 'active' ? (
                              <>
                                <Pause className="mr-2 h-4 w-4" />
                                Pause Tenant
                              </>
                            ) : (
                              <>
                                <Play className="mr-2 h-4 w-4" />
                                Activate Tenant
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-red-400 hover:bg-red-900/20">
                            <Trash2 className="mr-2 h-4 w-4" />
                            Suspend Tenant
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
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

function CreateTenantForm({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    plan: 'free'
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const response = await fetch('/api/v1/master/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (response.ok) {
        onSuccess()
        onClose()
      }
    } catch (error) {
      console.error('Failed to create tenant:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="name" className="text-white">Business Name</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="Cafe Mellow"
          required
        />
      </div>
      
      <div>
        <Label htmlFor="email" className="text-white">Email</Label>
        <Input
          id="email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="owner@cafemellow.com"
          required
        />
      </div>
      
      <div>
        <Label htmlFor="phone" className="text-white">Phone (Optional)</Label>
        <Input
          id="phone"
          value={formData.phone}
          onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="+91-9876543210"
        />
      </div>
      
      <div>
        <Label htmlFor="plan" className="text-white">Subscription Plan</Label>
        <Select value={formData.plan} onValueChange={(value) => setFormData(prev => ({ ...prev, plan: value }))}>
          <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="free">Free (50 AI calls/day)</SelectItem>
            <SelectItem value="pro">Pro (500 AI calls/day)</SelectItem>
            <SelectItem value="enterprise">Enterprise (5000 AI calls/day)</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div className="flex justify-end space-x-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-black">
          Create Tenant
        </Button>
      </div>
    </form>
  )
}
