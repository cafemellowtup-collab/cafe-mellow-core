"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Brain, 
  TrendingUp, 
  AlertCircle, 
  Lightbulb,
  Target,
  Users,
  DollarSign,
  CheckCircle,
  Clock,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface AIInsight {
  insight_id: string
  type: string
  priority: string
  tenant_id?: string
  title: string
  description: string
  recommendation: string
  data: any
  created_at: string
  acknowledged: boolean
}

interface DailyDigest {
  date: string
  summary: string
  key_insights: string[]
  recommendations: string[]
  tenant_count: number
  alerts_generated: number
  opportunities_found: number
}

export default function AIInsightsPage() {
  const [insights, setInsights] = useState<AIInsight[]>([])
  const [dailyDigest, setDailyDigest] = useState<DailyDigest | null>(null)
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [tenantFilter, setTenantFilter] = useState('all')
  const [showUnacknowledged, setShowUnacknowledged] = useState(false)

  useEffect(() => {
    fetchInsights()
    fetchDailyDigest()
  }, [typeFilter, priorityFilter, tenantFilter, showUnacknowledged])

  const fetchInsights = async () => {
    try {
      let url = '/api/v1/master/ai/insights?limit=50'
      if (typeFilter !== 'all') url += `&insight_type=${typeFilter}`
      if (priorityFilter !== 'all') url += `&priority=${priorityFilter}`
      if (tenantFilter !== 'all') url += `&tenant_id=${tenantFilter}`
      if (showUnacknowledged) url += `&unacknowledged_only=true`

      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setInsights(data.insights)
      } else {
        // Mock data for demonstration
        setInsights([
          {
            insight_id: "insight_001",
            type: "growth_opportunity",
            priority: "high",
            tenant_id: "tenant_001",
            title: "Revenue Growth Opportunity",
            description: "Coffee sales showing 25% growth trend over the past week. Customer demand is significantly higher during afternoon hours.",
            recommendation: "Consider expanding coffee menu offerings and increasing staff during peak afternoon hours to capitalize on this growth trend.",
            data: { growth_rate: 25.3, category: "beverages", peak_hours: "2-4 PM" },
            created_at: "2026-01-29T10:30:00Z",
            acknowledged: false
          },
          {
            insight_id: "insight_002",
            type: "cost_alert",
            priority: "medium",
            tenant_id: "tenant_002",
            title: "Ingredient Cost Increase",
            description: "Milk prices have increased by 8% this month, impacting profit margins on coffee-based beverages.",
            recommendation: "Consider bulk purchasing agreements or alternative suppliers to mitigate cost increases. Review pricing strategy for affected items.",
            data: { cost_increase: 8.2, category: "ingredients", affected_items: ["cappuccino", "latte", "macchiato"] },
            created_at: "2026-01-29T08:15:00Z",
            acknowledged: true
          },
          {
            insight_id: "insight_003",
            type: "churn_risk",
            priority: "urgent",
            tenant_id: "tenant_003",
            title: "Tenant Engagement Drop",
            description: "Tenant has shown 40% decrease in system usage over the past 5 days. Last login was 3 days ago.",
            recommendation: "Immediate outreach recommended. Provide additional training or support to re-engage the tenant and prevent churn.",
            data: { usage_drop: 40.2, days_inactive: 3, risk_score: 0.85 },
            created_at: "2026-01-28T16:45:00Z",
            acknowledged: false
          },
          {
            insight_id: "insight_004",
            type: "high_performer",
            priority: "low",
            tenant_id: "tenant_001",
            title: "Exceptional Performance",
            description: "Tenant consistently achieving 95%+ efficiency metrics across all operational areas.",
            recommendation: "Consider featuring as a success story and case study. Offer participation in beta features testing.",
            data: { efficiency_score: 95.8, metrics: "operational", consistency: "3_weeks" },
            created_at: "2026-01-28T12:20:00Z",
            acknowledged: false
          },
          {
            insight_id: "insight_005",
            type: "feature_suggestion",
            priority: "medium",
            title: "System-wide Pattern",
            description: "Multiple tenants requesting inventory forecasting features. 70% of enterprise clients have inquired about this capability.",
            recommendation: "Prioritize development of AI-powered inventory forecasting feature for next product release.",
            data: { request_percentage: 70, tier: "enterprise", feature: "inventory_forecasting" },
            created_at: "2026-01-28T09:10:00Z",
            acknowledged: false
          }
        ])
      }
    } catch (error) {
      setInsights([])
    } finally {
      setLoading(false)
    }
  }

  const fetchDailyDigest = async () => {
    try {
      const response = await fetch('/api/v1/master/ai/digest')
      if (response.ok) {
        const data = await response.json()
        setDailyDigest(data)
      } else {
        // Mock data
        setDailyDigest({
          date: "2026-01-29",
          summary: "System health excellent with 2 growth opportunities and 1 urgent attention item identified across 12 active tenants.",
          key_insights: [
            "Coffee sales trending up 25% - expansion opportunity",
            "Milk costs increased 8% - pricing review needed",
            "One tenant at risk - immediate intervention required"
          ],
          recommendations: [
            "Expand coffee menu offerings for high-growth tenants",
            "Review supplier agreements for cost optimization", 
            "Provide proactive support to at-risk tenant"
          ],
          tenant_count: 12,
          alerts_generated: 5,
          opportunities_found: 2
        })
      }
    } catch (error) {
      setDailyDigest(null)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500/10 text-red-400 border-red-500/20'
      case 'high': return 'bg-orange-500/10 text-orange-400 border-orange-500/20'
      case 'medium': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
      case 'low': return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'growth_opportunity': return TrendingUp
      case 'cost_alert': return DollarSign
      case 'churn_risk': return AlertCircle
      case 'high_performer': return Target
      case 'feature_suggestion': return Lightbulb
      default: return Brain
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'growth_opportunity': return 'text-green-400'
      case 'cost_alert': return 'text-yellow-400'
      case 'churn_risk': return 'text-red-400'
      case 'high_performer': return 'text-blue-400'
      case 'feature_suggestion': return 'text-purple-400'
      default: return 'text-cyan-400'
    }
  }

  const acknowledgeInsight = async (insightId: string) => {
    try {
      await fetch(`/api/v1/master/ai/insights/${insightId}/acknowledge`, {
        method: 'POST'
      })
      // Refresh insights
      fetchInsights()
    } catch (error) {
      console.error('Failed to acknowledge insight:', error)
    }
  }

  const filteredInsights = insights.filter(insight => {
    if (typeFilter !== 'all' && insight.type !== typeFilter) return false
    if (priorityFilter !== 'all' && insight.priority !== priorityFilter) return false
    if (tenantFilter !== 'all' && insight.tenant_id !== tenantFilter) return false
    if (showUnacknowledged && insight.acknowledged) return false
    return true
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
          <h1 className="text-3xl font-bold text-white">AI Insights</h1>
          <p className="text-zinc-400 mt-1">
            AI-generated insights and recommendations for system optimization
          </p>
        </div>
        
        <Button
          onClick={() => fetchInsights()}
          className="bg-amber-500 hover:bg-amber-600 text-black"
        >
          <Brain className="w-4 h-4 mr-2" />
          Run Analysis
        </Button>
      </div>

      {/* Daily Digest */}
      {dailyDigest && (
        <Card className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border-amber-500/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Brain className="mr-2 h-5 w-5 text-amber-400" />
              Daily AI Digest - {dailyDigest.date}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-zinc-200">{dailyDigest.summary}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-white mb-2">Key Insights</h4>
                  <ul className="space-y-1">
                    {dailyDigest.key_insights.map((insight, index) => (
                      <li key={index} className="text-sm text-zinc-300 flex items-start">
                        <div className="w-1.5 h-1.5 bg-amber-400 rounded-full mt-2 mr-2 flex-shrink-0"></div>
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-white mb-2">Recommendations</h4>
                  <ul className="space-y-1">
                    {dailyDigest.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-zinc-300 flex items-start">
                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-2 mr-2 flex-shrink-0"></div>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="flex items-center space-x-6 pt-2 border-t border-amber-500/20">
                <div className="text-center">
                  <p className="text-2xl font-bold text-amber-400">{dailyDigest.tenant_count}</p>
                  <p className="text-xs text-zinc-400">Tenants Analyzed</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-orange-400">{dailyDigest.alerts_generated}</p>
                  <p className="text-xs text-zinc-400">Insights Generated</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-400">{dailyDigest.opportunities_found}</p>
                  <p className="text-xs text-zinc-400">Opportunities Found</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center">
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[180px] bg-zinc-800 border-zinc-700 text-white">
            <SelectValue placeholder="Insight Type" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="growth_opportunity">Growth Opportunity</SelectItem>
            <SelectItem value="cost_alert">Cost Alert</SelectItem>
            <SelectItem value="churn_risk">Churn Risk</SelectItem>
            <SelectItem value="high_performer">High Performer</SelectItem>
            <SelectItem value="feature_suggestion">Feature Suggestion</SelectItem>
          </SelectContent>
        </Select>

        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-[150px] bg-zinc-800 border-zinc-700 text-white">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-800 border-zinc-700">
            <SelectItem value="all">All Priorities</SelectItem>
            <SelectItem value="urgent">Urgent</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant={showUnacknowledged ? "default" : "outline"}
          onClick={() => setShowUnacknowledged(!showUnacknowledged)}
          className={showUnacknowledged ? "bg-amber-500 text-black" : "border-zinc-700"}
        >
          <Filter className="w-4 h-4 mr-2" />
          {showUnacknowledged ? "Show All" : "Unacknowledged Only"}
        </Button>
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredInsights.map((insight, index) => {
          const TypeIcon = getTypeIcon(insight.type)
          return (
            <motion.div
              key={insight.insight_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className={`bg-zinc-900 border-zinc-800 ${!insight.acknowledged ? 'ring-1 ring-amber-500/20' : ''}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg bg-zinc-800`}>
                        <TypeIcon className={`h-5 w-5 ${getTypeColor(insight.type)}`} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white text-sm">{insight.title}</h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge className={getPriorityColor(insight.priority)}>
                            {insight.priority}
                          </Badge>
                          {insight.tenant_id && (
                            <span className="text-xs text-zinc-400">{insight.tenant_id}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {insight.acknowledged ? (
                      <CheckCircle className="h-5 w-5 text-green-400" />
                    ) : (
                      <Clock className="h-5 w-5 text-yellow-400" />
                    )}
                  </div>
                </CardHeader>
                
                <CardContent className="pt-0">
                  <div className="space-y-3">
                    <p className="text-sm text-zinc-300">{insight.description}</p>
                    
                    <div className="bg-zinc-800 rounded-lg p-3">
                      <h4 className="text-xs font-medium text-zinc-400 mb-1">AI Recommendation</h4>
                      <p className="text-sm text-white">{insight.recommendation}</p>
                    </div>

                    {insight.data && Object.keys(insight.data).length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(insight.data).slice(0, 3).map(([key, value]) => (
                          <span 
                            key={key} 
                            className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300"
                          >
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t border-zinc-800">
                      <span className="text-xs text-zinc-400">
                        {new Date(insight.created_at).toLocaleDateString()}
                      </span>
                      
                      {!insight.acknowledged && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => acknowledgeInsight(insight.insight_id)}
                          className="text-xs border-zinc-700 hover:bg-zinc-800"
                        >
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {filteredInsights.length === 0 && (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-12 text-center">
            <Brain className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No Insights Found</h3>
            <p className="text-zinc-400">
              No AI insights match your current filters. Try adjusting the filters or run a new analysis.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
