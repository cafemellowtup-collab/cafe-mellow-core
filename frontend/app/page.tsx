import { AppLayout } from '@/components/layout';
import { DropZone } from '@/components/upload';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Database, Brain, Shield } from 'lucide-react';

export default function Home() {
  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto">
        {/* Welcome Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <h1 className="text-3xl font-bold text-slate-900">Welcome, Master</h1>
            <Badge className="bg-slate-900">Pro</Badge>
          </div>
          <p className="text-slate-500">
            Upload your financial documents and let Titan AI transform them into insights.
          </p>
        </div>

        {/* Drop Zone */}
        <div className="mb-8">
          <DropZone />
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center mb-2">
                <Database className="w-5 h-5 text-blue-600" />
              </div>
              <CardTitle className="text-base">Universal Ingestion</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Upload any CSV or Excel file. Headers auto-detected.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center mb-2">
                <Brain className="w-5 h-5 text-purple-600" />
              </div>
              <CardTitle className="text-base">Semantic Brain</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                AI classifies transactions with 85%+ confidence.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center mb-2">
                <Sparkles className="w-5 h-5 text-amber-600" />
              </div>
              <CardTitle className="text-base">Titan Cortex</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Adaptive AI personality that grows with your data.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center mb-2">
                <Shield className="w-5 h-5 text-green-600" />
              </div>
              <CardTitle className="text-base">God Mode</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Master control over all features and AI behavior.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
