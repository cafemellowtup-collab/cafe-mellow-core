"use client";

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings, 
  Database, 
  Shield,
  Globe,
  Bell,
  Eye,
  Save,
  RefreshCw,
  Key,
  Server,
  Mail,
  Clock
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { 
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'

interface SystemSettings {
  system_name: string
  admin_email: string
  max_tenants: number
  default_plan: string
  auto_suspend_inactive_days: number
  cost_alert_threshold: number
  maintenance_mode: boolean
  debug_logging: boolean
  api_rate_limit: number
  backup_frequency: string
}

interface NotificationSettings {
  email_notifications: boolean
  slack_webhook?: string
  alert_email?: string
  daily_digest: boolean
  weekly_report: boolean
  critical_alerts_only: boolean
}

interface SecuritySettings {
  session_timeout_minutes: number
  max_login_attempts: number
  require_2fa: boolean
  password_policy: {
    min_length: number
    require_uppercase: boolean
    require_numbers: boolean
    require_symbols: boolean
  }
  ip_whitelist: string[]
}

export default function MasterSettingsPage() {
  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    system_name: "TITAN ERP Master",
    admin_email: "admin@titan.com",
    max_tenants: 100,
    default_plan: "free",
    auto_suspend_inactive_days: 30,
    cost_alert_threshold: 1000,
    maintenance_mode: false,
    debug_logging: false,
    api_rate_limit: 1000,
    backup_frequency: "daily"
  })

  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
    email_notifications: true,
    alert_email: "alerts@titan.com",
    daily_digest: true,
    weekly_report: true,
    critical_alerts_only: false
  })

  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>({
    session_timeout_minutes: 480,
    max_login_attempts: 5,
    require_2fa: false,
    password_policy: {
      min_length: 8,
      require_uppercase: true,
      require_numbers: true,
      require_symbols: false
    },
    ip_whitelist: []
  })

  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      // In a real implementation, fetch from API
      // For now, using mock data
      console.log('Loading master settings...')
    } catch (error) {
      console.error('Failed to fetch settings:', error)
    }
  }

  const saveSettings = async () => {
    setLoading(true)
    try {
      // In a real implementation, save to API
      await new Promise(resolve => setTimeout(resolve, 1000)) // Mock delay
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const runSystemDiagnostics = async () => {
    setLoading(true)
    try {
      // Mock system diagnostics
      await new Promise(resolve => setTimeout(resolve, 2000))
      alert('System diagnostics completed successfully!')
    } catch (error) {
      console.error('Diagnostics failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Master Settings</h1>
          <p className="text-zinc-400 mt-1">
            Configure system-wide settings and preferences
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={runSystemDiagnostics}
            disabled={loading}
            className="border-zinc-700"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Run Diagnostics
          </Button>
          
          <Button
            onClick={saveSettings}
            disabled={loading}
            className="bg-amber-500 hover:bg-amber-600 text-black"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : saved ? (
              <Save className="w-4 h-4 mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            {saved ? 'Saved!' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* Settings Tabs */}
      <Tabs defaultValue="system" className="space-y-6">
        <TabsList className="bg-zinc-800 border-zinc-700">
          <TabsTrigger value="system" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
            <Server className="w-4 h-4 mr-2" />
            System
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
            <Bell className="w-4 h-4 mr-2" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="security" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
            <Shield className="w-4 h-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="database" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
            <Database className="w-4 h-4 mr-2" />
            Database
          </TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Settings className="mr-2 h-5 w-5" />
                  General Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="system_name" className="text-white">System Name</Label>
                  <Input
                    id="system_name"
                    value={systemSettings.system_name}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, system_name: e.target.value }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>
                
                <div>
                  <Label htmlFor="admin_email" className="text-white">Admin Email</Label>
                  <Input
                    id="admin_email"
                    type="email"
                    value={systemSettings.admin_email}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, admin_email: e.target.value }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div>
                  <Label htmlFor="max_tenants" className="text-white">Maximum Tenants</Label>
                  <Input
                    id="max_tenants"
                    type="number"
                    value={systemSettings.max_tenants}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, max_tenants: parseInt(e.target.value) }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div>
                  <Label htmlFor="default_plan" className="text-white">Default Plan for New Tenants</Label>
                  <Select value={systemSettings.default_plan} onValueChange={(value) => setSystemSettings(prev => ({ ...prev, default_plan: value }))}>
                    <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-800 border-zinc-700">
                      <SelectItem value="free">Free</SelectItem>
                      <SelectItem value="pro">Pro</SelectItem>
                      <SelectItem value="enterprise">Enterprise</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Globe className="mr-2 h-5 w-5" />
                  Operational Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="auto_suspend" className="text-white">Auto-suspend inactive tenants (days)</Label>
                  <Input
                    id="auto_suspend"
                    type="number"
                    value={systemSettings.auto_suspend_inactive_days}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, auto_suspend_inactive_days: parseInt(e.target.value) }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div>
                  <Label htmlFor="cost_threshold" className="text-white">Cost Alert Threshold (₹)</Label>
                  <Input
                    id="cost_threshold"
                    type="number"
                    value={systemSettings.cost_alert_threshold}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, cost_alert_threshold: parseFloat(e.target.value) }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div>
                  <Label htmlFor="api_rate_limit" className="text-white">API Rate Limit (per hour)</Label>
                  <Input
                    id="api_rate_limit"
                    type="number"
                    value={systemSettings.api_rate_limit}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, api_rate_limit: parseInt(e.target.value) }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-white">Maintenance Mode</Label>
                    <Switch
                      checked={systemSettings.maintenance_mode}
                      onCheckedChange={(checked) => setSystemSettings(prev => ({ ...prev, maintenance_mode: checked }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label className="text-white">Debug Logging</Label>
                    <Switch
                      checked={systemSettings.debug_logging}
                      onCheckedChange={(checked) => setSystemSettings(prev => ({ ...prev, debug_logging: checked }))}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center">
                <Bell className="mr-2 h-5 w-5" />
                Notification Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="alert_email" className="text-white">Alert Email Address</Label>
                    <Input
                      id="alert_email"
                      type="email"
                      value={notificationSettings.alert_email || ''}
                      onChange={(e) => setNotificationSettings(prev => ({ ...prev, alert_email: e.target.value }))}
                      className="bg-zinc-800 border-zinc-700 text-white"
                    />
                  </div>

                  <div>
                    <Label htmlFor="slack_webhook" className="text-white">Slack Webhook URL (Optional)</Label>
                    <Input
                      id="slack_webhook"
                      value={notificationSettings.slack_webhook || ''}
                      onChange={(e) => setNotificationSettings(prev => ({ ...prev, slack_webhook: e.target.value }))}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder="https://hooks.slack.com/services/..."
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-white">Email Notifications</Label>
                    <Switch
                      checked={notificationSettings.email_notifications}
                      onCheckedChange={(checked) => setNotificationSettings(prev => ({ ...prev, email_notifications: checked }))}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-white">Daily Digest</Label>
                    <Switch
                      checked={notificationSettings.daily_digest}
                      onCheckedChange={(checked) => setNotificationSettings(prev => ({ ...prev, daily_digest: checked }))}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-white">Weekly Reports</Label>
                    <Switch
                      checked={notificationSettings.weekly_report}
                      onCheckedChange={(checked) => setNotificationSettings(prev => ({ ...prev, weekly_report: checked }))}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-white">Critical Alerts Only</Label>
                    <Switch
                      checked={notificationSettings.critical_alerts_only}
                      onCheckedChange={(checked) => setNotificationSettings(prev => ({ ...prev, critical_alerts_only: checked }))}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Shield className="mr-2 h-5 w-5" />
                  Access Control
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="session_timeout" className="text-white">Session Timeout (minutes)</Label>
                  <Input
                    id="session_timeout"
                    type="number"
                    value={securitySettings.session_timeout_minutes}
                    onChange={(e) => setSecuritySettings(prev => ({ ...prev, session_timeout_minutes: parseInt(e.target.value) }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div>
                  <Label htmlFor="max_attempts" className="text-white">Max Login Attempts</Label>
                  <Input
                    id="max_attempts"
                    type="number"
                    value={securitySettings.max_login_attempts}
                    onChange={(e) => setSecuritySettings(prev => ({ ...prev, max_login_attempts: parseInt(e.target.value) }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label className="text-white">Require Two-Factor Auth</Label>
                  <Switch
                    checked={securitySettings.require_2fa}
                    onCheckedChange={(checked) => setSecuritySettings(prev => ({ ...prev, require_2fa: checked }))}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Key className="mr-2 h-5 w-5" />
                  Password Policy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="min_length" className="text-white">Minimum Length</Label>
                  <Input
                    id="min_length"
                    type="number"
                    value={securitySettings.password_policy.min_length}
                    onChange={(e) => setSecuritySettings(prev => ({
                      ...prev,
                      password_policy: { ...prev.password_policy, min_length: parseInt(e.target.value) }
                    }))}
                    className="bg-zinc-800 border-zinc-700 text-white"
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-white">Require Uppercase</Label>
                    <Switch
                      checked={securitySettings.password_policy.require_uppercase}
                      onCheckedChange={(checked) => setSecuritySettings(prev => ({
                        ...prev,
                        password_policy: { ...prev.password_policy, require_uppercase: checked }
                      }))}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-white">Require Numbers</Label>
                    <Switch
                      checked={securitySettings.password_policy.require_numbers}
                      onCheckedChange={(checked) => setSecuritySettings(prev => ({
                        ...prev,
                        password_policy: { ...prev.password_policy, require_numbers: checked }
                      }))}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-white">Require Symbols</Label>
                    <Switch
                      checked={securitySettings.password_policy.require_symbols}
                      onCheckedChange={(checked) => setSecuritySettings(prev => ({
                        ...prev,
                        password_policy: { ...prev.password_policy, require_symbols: checked }
                      }))}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="database" className="space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center">
                <Database className="mr-2 h-5 w-5" />
                Database Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label className="text-white">BigQuery Project ID</Label>
                    <Input
                      value="cafe-mellow-core-2026"
                      className="bg-zinc-800 border-zinc-700 text-white"
                      disabled
                    />
                  </div>

                  <div>
                    <Label className="text-white">Dataset ID</Label>
                    <Input
                      value="cafe_operations"
                      className="bg-zinc-800 border-zinc-700 text-white"
                      disabled
                    />
                  </div>

                  <div>
                    <Label htmlFor="backup_freq" className="text-white">Backup Frequency</Label>
                    <Select value={systemSettings.backup_frequency} onValueChange={(value) => setSystemSettings(prev => ({ ...prev, backup_frequency: value }))}>
                      <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-zinc-700">
                        <SelectItem value="hourly">Hourly</SelectItem>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="p-4 bg-zinc-800 rounded-lg">
                    <h4 className="font-medium text-white mb-2">Database Status</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-zinc-400">Connection</span>
                        <span className="text-green-400">✓ Connected</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-400">Last Backup</span>
                        <span className="text-white">2 hours ago</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-400">Storage Used</span>
                        <span className="text-white">2.4 GB</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <Button 
                      variant="outline" 
                      className="flex-1 border-zinc-700"
                      onClick={() => alert('Backup initiated!')}
                    >
                      <Database className="w-4 h-4 mr-2" />
                      Backup Now
                    </Button>
                    <Button 
                      variant="outline" 
                      className="flex-1 border-zinc-700"
                      onClick={() => alert('Connection test successful!')}
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Test Connection
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
