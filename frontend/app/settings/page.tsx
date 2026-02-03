'use client';

import { useState } from 'react';
import { AppLayout } from '@/components/layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Settings, Trash2, AlertTriangle, Database, Brain, Shield } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleReset = async () => {
    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }

    setIsResetting(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/master/factory-reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': 'demo-cafe',
        },
        body: JSON.stringify({ confirm: 'RESET' }),
      });

      if (response.ok) {
        toast.success('Data reset complete', {
          description: 'All test data has been cleared. Intelligence preserved.',
        });
      } else {
        throw new Error('Reset failed');
      }
    } catch (error) {
      toast.error('Reset failed', {
        description: 'Could not reset data. Check backend connection.',
      });
    } finally {
      setIsResetting(false);
      setShowConfirm(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Settings className="w-6 h-6" />
            Settings
          </h1>
          <p className="text-slate-500 mt-1">
            Manage your Titan AI configuration
          </p>
        </div>

        {/* Account Info */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Account</CardTitle>
            <CardDescription>Your current tenant information</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-900">Tenant ID</p>
                <code className="text-sm bg-slate-100 px-2 py-1 rounded">demo-cafe</code>
              </div>
              <Badge className="bg-slate-900">Pro Plan</Badge>
            </div>
          </CardContent>
        </Card>

        {/* System Status */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">System Status</CardTitle>
            <CardDescription>Current AI system components</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                  <Brain className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">Semantic Brain</p>
                  <p className="text-sm text-slate-500">Pattern recognition & classification</p>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-700">Active</Badge>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                  <Database className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">Universal Adapter</p>
                  <p className="text-sm text-slate-500">Data ingestion & mapping</p>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-700">Active</Badge>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">God Mode</p>
                  <p className="text-sm text-slate-500">Master control system</p>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-700">Active</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-lg text-red-600 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Danger Zone
            </CardTitle>
            <CardDescription>
              Irreversible actions that affect your data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">Reset All Data</p>
                <p className="text-sm text-slate-500">
                  Delete all uploaded files and processed events. AI intelligence is preserved.
                </p>
              </div>
              <Button
                variant={showConfirm ? 'destructive' : 'outline'}
                onClick={handleReset}
                disabled={isResetting}
                className={showConfirm ? '' : 'border-red-300 text-red-600 hover:bg-red-50'}
              >
                {isResetting ? (
                  <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                ) : (
                  <>
                    <Trash2 className="w-4 h-4 mr-2" />
                    {showConfirm ? 'Click Again to Confirm' : 'Reset Data'}
                  </>
                )}
              </Button>
            </div>
            {showConfirm && (
              <p className="text-xs text-red-500 mt-2 text-center">
                ⚠️ This action cannot be undone. Click the button again to confirm.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
