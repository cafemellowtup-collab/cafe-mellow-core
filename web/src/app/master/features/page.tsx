"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Zap, 
  Settings, 
  Crown, 
  Shield,
  Star,
  Eye,
  EyeOff,
  Plus,
  Search,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
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
import { 
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'

interface Feature {
  feature_id: string
  name: string
  description: string
  tiers: string[]
  category: string
  is_beta: boolean
  rollout_percentage: number
}

interface FeaturesByCategory {
  [category: string]: Feature[]
}

interface TenantFeatureOverride {
  tenant_id: string
  feature_id: string
  enabled: boolean
  reason: string
  updated_by: string
  updated_at: string
}

export default function FeaturesPage() {
  const [features, setFeatures] = useState<Feature[]>([])
  const [featuresByCategory, setFeaturesByCategory] = useState<FeaturesByCategory>({})
  const [overrides, setOverrides] = useState<TenantFeatureOverride[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [tierFilter, setTierFilter] = useState('all')
  const [showBetaOnly, setShowBetaOnly] = useState(false)
  const [showOverrideDialog, setShowOverrideDialog] = useState(false)
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null)

  useEffect(() => {
    fetchFeatures()
    fetchOverrides()
  }, [])

  const fetchFeatures = async () => {
    try {
      const response = await fetch('/api/v1/master/features')
      if (response.ok) {
        const data = await response.json()
        setFeatures(data.features)
        setFeaturesByCategory(data.by_category)
      } else {
        // Mock data for demonstration
        const mockFeatures: Feature[] = [
          {
            feature_id: "chat",
            name: "AI Chat",
            description: "TITAN CFO conversational AI",
            tiers: ["free", "pro", "enterprise"],
            category: "ai",
            is_beta: false,
            rollout_percentage: 100
          },
          {
            feature_id: "dashboard",
            name: "Dashboard",
            description: "KPI dashboard with analytics",
            tiers: ["free", "pro", "enterprise"],
            category: "general",
            is_beta: false,
            rollout_percentage: 100
          },
          {
            feature_id: "reports_ai",
            name: "AI Reports",
            description: "AI-generated custom reports",
            tiers: ["pro", "enterprise"],
            category: "reporting",
            is_beta: false,
            rollout_percentage: 100
          },
          {
            feature_id: "api_access",
            name: "API Access",
            description: "Direct API access for integrations",
            tiers: ["pro", "enterprise"],
            category: "integration",
            is_beta: false,
            rollout_percentage: 100
          },
          {
            feature_id: "multi_location",
            name: "Multi-Location",
            description: "Manage multiple business locations",
            tiers: ["enterprise"],
            category: "general",
            is_beta: false,
            rollout_percentage: 100
          },
          {
            feature_id: "ai_proactive",
            name: "Proactive AI Alerts",
            description: "AI sends alerts without prompting",
            tiers: ["enterprise"],
            category: "ai",
            is_beta: true,
            rollout_percentage: 80
          },
          {
            feature_id: "climate_module",
            name: "Climate Module",
            description: "Weather-based demand prediction",
            tiers: ["enterprise"],
            category: "ai",
            is_beta: true,
            rollout_percentage: 25
          }
        ]
        setFeatures(mockFeatures)
        
        // Group by category
        const grouped = mockFeatures.reduce((acc, feature) => {
          if (!acc[feature.category]) acc[feature.category] = []
          acc[feature.category].push(feature)
          return acc
        }, {} as FeaturesByCategory)
        setFeaturesByCategory(grouped)
      }
    } catch (error) {
      setFeatures([])
    } finally {
      setLoading(false)
    }
  }

  const fetchOverrides = async () => {
    try {
      const response = await fetch('/api/v1/master/features/overrides')
      if (response.ok) {
        const data = await response.json()
        setOverrides(data.overrides)
      } else {
        // Mock data
        setOverrides([
          {
            tenant_id: "tenant_001",
            feature_id: "climate_module",
            enabled: true,
            reason: "Beta testing participant",
            updated_by: "admin",
            updated_at: "2026-01-29T10:00:00Z"
          }
        ])
      }
    } catch (error) {
      setOverrides([])
    }
  }

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      case 'pro': return 'bg-purple-500/10 text-purple-400 border-purple-500/20'  
      case 'enterprise': return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
      default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'ai': return 'text-cyan-400'
      case 'reporting': return 'text-green-400'
      case 'integration': return 'text-purple-400'
      case 'general': return 'text-blue-400'
      default: return 'text-gray-400'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'ai': return Zap
      case 'reporting': return Settings
      case 'integration': return Shield
      case 'general': return Star
      default: return Settings
    }
  }

  const filteredFeatures = features.filter(feature => {
    const matchesSearch = feature.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         feature.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = categoryFilter === 'all' || feature.category === categoryFilter
    const matchesTier = tierFilter === 'all' || feature.tiers.includes(tierFilter)
    const matchesBeta = !showBetaOnly || feature.is_beta
    
    return matchesSearch && matchesCategory && matchesTier && matchesBeta
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
          <h1 className="text-3xl font-bold text-white">Features Management</h1>
          <p className="text-zinc-400 mt-1">
            Manage feature flags, tiers, and tenant overrides
          </p>
        </div>
        
        <Button
          onClick={() => setShowOverrideDialog(true)}
          className="bg-amber-500 hover:bg-amber-600 text-black"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Override
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Features</p>
                <p className="text-2xl font-bold text-white">{features.length}</p>
              </div>
              <Zap className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Beta Features</p>
                <p className="text-2xl font-bold text-white">
                  {features.filter(f => f.is_beta).length}
                </p>
              </div>
              <Eye className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Enterprise Only</p>
                <p className="text-2xl font-bold text-white">
                  {features.filter(f => f.tiers.includes('enterprise') && !f.tiers.includes('pro') && !f.tiers.includes('free')).length}
                </p>
              </div>
              <Crown className="h-8 w-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Active Overrides</p>
                <p className="text-2xl font-bold text-white">{overrides.length}</p>
              </div>
              <Settings className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Feature Management Tabs */}
      <Tabs defaultValue="features" className="space-y-6">
        <TabsList className="bg-zinc-800 border-zinc-700">
          <TabsTrigger value="features" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
            Features
          </TabsTrigger>
          <TabsTrigger value="overrides" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
            Overrides
          </TabsTrigger>
          <TabsTrigger value="rollouts" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
            Rollouts
          </TabsTrigger>
        </TabsList>

        <TabsContent value="features" className="space-y-6">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400 w-4 h-4" />
              <Input
                placeholder="Search features..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-zinc-800 border-zinc-700 text-white placeholder-zinc-400"
              />
            </div>
            
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-[150px] bg-zinc-800 border-zinc-700 text-white">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-800 border-zinc-700">
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="ai">AI Features</SelectItem>
                <SelectItem value="reporting">Reporting</SelectItem>
                <SelectItem value="integration">Integration</SelectItem>
                <SelectItem value="general">General</SelectItem>
              </SelectContent>
            </Select>

            <Select value={tierFilter} onValueChange={setTierFilter}>
              <SelectTrigger className="w-full sm:w-[150px] bg-zinc-800 border-zinc-700 text-white">
                <SelectValue placeholder="Tier" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-800 border-zinc-700">
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="free">Free</SelectItem>
                <SelectItem value="pro">Pro</SelectItem>
                <SelectItem value="enterprise">Enterprise</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center space-x-2">
              <Switch
                checked={showBetaOnly}
                onCheckedChange={setShowBetaOnly}
              />
              <Label className="text-white">Beta Only</Label>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFeatures.map((feature, index) => {
              const CategoryIcon = getCategoryIcon(feature.category)
              return (
                <motion.div
                  key={feature.feature_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-colors">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="p-2 rounded-lg bg-zinc-800">
                            <CategoryIcon className={`h-5 w-5 ${getCategoryColor(feature.category)}`} />
                          </div>
                          <div>
                            <h3 className="font-semibold text-white">{feature.name}</h3>
                            <p className="text-xs text-zinc-400 mt-1">{feature.category}</p>
                          </div>
                        </div>
                        
                        <div className="flex flex-col space-y-1">
                          {feature.is_beta && (
                            <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-xs">
                              BETA
                            </Badge>
                          )}
                          {feature.rollout_percentage < 100 && (
                            <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-xs">
                              {feature.rollout_percentage}%
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent className="pt-0">
                      <div className="space-y-3">
                        <p className="text-sm text-zinc-300">{feature.description}</p>
                        
                        <div className="flex flex-wrap gap-1">
                          {feature.tiers.map(tier => (
                            <Badge key={tier} className={getTierColor(tier)}>
                              {tier}
                            </Badge>
                          ))}
                        </div>

                        <div className="flex justify-between items-center pt-2 border-t border-zinc-800">
                          <span className="text-xs text-zinc-500">
                            {feature.feature_id}
                          </span>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedFeature(feature)
                              setShowOverrideDialog(true)
                            }}
                            className="text-xs border-zinc-700 hover:bg-zinc-800"
                          >
                            Override
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="overrides" className="space-y-6">
          {/* Overrides Table */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white">Active Feature Overrides</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-zinc-800">
                      <th className="text-left p-3 text-sm font-medium text-zinc-400">Tenant</th>
                      <th className="text-left p-3 text-sm font-medium text-zinc-400">Feature</th>
                      <th className="text-left p-3 text-sm font-medium text-zinc-400">Status</th>
                      <th className="text-left p-3 text-sm font-medium text-zinc-400">Reason</th>
                      <th className="text-left p-3 text-sm font-medium text-zinc-400">Updated</th>
                      <th className="text-right p-3 text-sm font-medium text-zinc-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overrides.map((override, index) => (
                      <motion.tr
                        key={`${override.tenant_id}_${override.feature_id}`}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="border-b border-zinc-800 hover:bg-zinc-800/50"
                      >
                        <td className="p-3 font-medium text-white">{override.tenant_id}</td>
                        <td className="p-3 text-zinc-300">{override.feature_id}</td>
                        <td className="p-3">
                          <Badge className={override.enabled ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}>
                            {override.enabled ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </td>
                        <td className="p-3 text-zinc-300 text-sm">{override.reason}</td>
                        <td className="p-3 text-zinc-400 text-sm">
                          {new Date(override.updated_at).toLocaleDateString()}
                        </td>
                        <td className="p-3 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs border-zinc-700 hover:bg-zinc-800"
                          >
                            Remove
                          </Button>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {overrides.length === 0 && (
                <div className="text-center py-8">
                  <Settings className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-white mb-2">No Overrides</h3>
                  <p className="text-zinc-400">No feature overrides have been configured.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rollouts" className="space-y-6">
          {/* Rollout Management */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white">Feature Rollouts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {features.filter(f => f.rollout_percentage < 100 || f.is_beta).map((feature, index) => (
                  <motion.div
                    key={feature.feature_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 bg-zinc-800 rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      <div>
                        <h4 className="font-medium text-white">{feature.name}</h4>
                        <p className="text-sm text-zinc-400">{feature.description}</p>
                      </div>
                      {feature.is_beta && (
                        <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20">
                          BETA
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="font-medium text-white">{feature.rollout_percentage}%</p>
                        <p className="text-xs text-zinc-400">Rollout</p>
                      </div>
                      
                      <div className="w-24 bg-zinc-700 rounded-full h-2">
                        <div 
                          className="bg-amber-400 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${feature.rollout_percentage}%` }}
                        ></div>
                      </div>
                      
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs border-zinc-700 hover:bg-zinc-800"
                      >
                        Adjust
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Override Dialog */}
      <Dialog open={showOverrideDialog} onOpenChange={setShowOverrideDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white">
              {selectedFeature ? `Override: ${selectedFeature.name}` : 'Create Feature Override'}
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Set a feature override for a specific tenant
            </DialogDescription>
          </DialogHeader>
          <CreateOverrideForm 
            feature={selectedFeature}
            onClose={() => {
              setShowOverrideDialog(false)
              setSelectedFeature(null)
            }}
            onSuccess={() => {
              fetchOverrides()
              setShowOverrideDialog(false)
              setSelectedFeature(null)
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}

function CreateOverrideForm({ 
  feature, 
  onClose, 
  onSuccess 
}: { 
  feature: Feature | null
  onClose: () => void
  onSuccess: () => void 
}) {
  const [formData, setFormData] = useState({
    tenant_id: '',
    feature_id: feature?.feature_id || '',
    enabled: true,
    reason: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const response = await fetch(`/api/v1/master/tenants/${formData.tenant_id}/features/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feature_id: formData.feature_id,
          enabled: formData.enabled,
          reason: formData.reason
        })
      })
      
      if (response.ok) {
        onSuccess()
      }
    } catch (error) {
      console.error('Failed to create override:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="tenant_id" className="text-white">Tenant ID</Label>
        <Input
          id="tenant_id"
          value={formData.tenant_id}
          onChange={(e) => setFormData(prev => ({ ...prev, tenant_id: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="tenant_001"
          required
        />
      </div>
      
      {!feature && (
        <div>
          <Label htmlFor="feature_id" className="text-white">Feature ID</Label>
          <Input
            id="feature_id"
            value={formData.feature_id}
            onChange={(e) => setFormData(prev => ({ ...prev, feature_id: e.target.value }))}
            className="bg-zinc-800 border-zinc-700 text-white"
            placeholder="feature_name"
            required
          />
        </div>
      )}
      
      <div className="flex items-center space-x-2">
        <Switch
          checked={formData.enabled}
          onCheckedChange={(checked) => setFormData(prev => ({ ...prev, enabled: checked }))}
        />
        <Label className="text-white">
          {formData.enabled ? 'Enable Feature' : 'Disable Feature'}
        </Label>
      </div>
      
      <div>
        <Label htmlFor="reason" className="text-white">Reason</Label>
        <Textarea
          id="reason"
          value={formData.reason}
          onChange={(e) => setFormData(prev => ({ ...prev, reason: e.target.value }))}
          className="bg-zinc-800 border-zinc-700 text-white"
          placeholder="Reason for this override"
          required
        />
      </div>
      
      <div className="flex justify-end space-x-2 pt-4">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-black">
          Create Override
        </Button>
      </div>
    </form>
  )
}
