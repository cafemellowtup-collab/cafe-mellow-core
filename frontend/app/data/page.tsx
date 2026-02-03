'use client';

import { useState, useEffect } from 'react';
import { AppLayout } from '@/components/layout';
import { getFileStatus, FileStatus } from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, RefreshCw, FileSpreadsheet } from 'lucide-react';
import { Button } from '@/components/ui/button';

function formatTimeAgo(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);

  if (diffSec < 60) return 'Just now';
  if (diffMin < 60) return `${diffMin} min${diffMin > 1 ? 's' : ''} ago`;
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
}

function StatusBadge({ status }: { status: FileStatus['status'] }) {
  switch (status) {
    case 'queued':
      return (
        <Badge variant="secondary" className="bg-slate-100 text-slate-700">
          Queued
        </Badge>
      );
    case 'processing':
      return (
        <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">
          <span className="w-2 h-2 bg-amber-500 rounded-full mr-2 animate-pulse" />
          Processing
        </Badge>
      );
    case 'completed':
      return (
        <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
          Indexed
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="destructive">
          Failed
        </Badge>
      );
    default:
      return <Badge variant="secondary">Unknown</Badge>;
  }
}

export default function DataPage() {
  const [files, setFiles] = useState<FileStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchStatus = async () => {
    try {
      const data = await getFileStatus();
      setFiles(data);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to fetch file status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const processingCount = files.filter((f) => f.status === 'processing').length;
  const completedCount = files.filter((f) => f.status === 'completed').length;

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-6 h-6" />
              Data Sources
            </h1>
            <p className="text-slate-500 mt-1">
              Monitor your uploaded files and AI analysis status
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStatus}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Files</CardDescription>
              <CardTitle className="text-3xl">{files.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Processing</CardDescription>
              <CardTitle className="text-3xl text-amber-600">{processingCount}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Indexed</CardDescription>
              <CardTitle className="text-3xl text-green-600">{completedCount}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Data Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Uploaded Files</CardTitle>
              <span className="text-xs text-slate-400">
                Auto-refreshes every 5s • Last: {formatTimeAgo(lastRefresh.toISOString())}
              </span>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-8 h-8 rounded-full border-2 border-slate-300 border-t-slate-600 animate-spin" />
              </div>
            ) : files.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                <FileSpreadsheet className="w-12 h-12 mb-4" />
                <p className="text-lg font-medium">No files uploaded yet</p>
                <p className="text-sm">Upload files from the Dashboard to see them here</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>File Name</TableHead>
                    <TableHead>Upload Time</TableHead>
                    <TableHead>AI Detection</TableHead>
                    <TableHead>Processing Stats</TableHead>
                    <TableHead>Rows</TableHead>
                    <TableHead>Events</TableHead>
                    <TableHead className="text-right">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {files.map((file) => (
                    <TableRow 
                      key={file.file_id} 
                      className={file.status === 'failed' || file.status === 'rejected' ? 'bg-red-50' : ''}
                    >
                      <TableCell className="font-medium">
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2">
                            <FileSpreadsheet className="w-4 h-4 text-slate-400" />
                            {file.filename}
                          </div>
                          {file.status === 'failed' && file.error && (
                            <div className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded max-w-md">
                              ⚠️ {file.error}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {formatTimeAgo(file.upload_time)}
                      </TableCell>
                      <TableCell>
                        {file.ai_detection ? (
                          <code className="text-xs bg-slate-100 px-2 py-1 rounded font-mono">
                            {file.ai_detection}
                          </code>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {file.ghost_items > 0 && (
                            <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">
                              👻 {file.ghost_items} Created
                            </Badge>
                          )}
                          {file.duplicates > 0 && (
                            <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">
                              ⚠️ {file.duplicates} Skipped
                            </Badge>
                          )}
                          {file.new_events > 0 && (
                            <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                              ✅ {file.new_events} Added
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{file.rows_processed || '—'}</TableCell>
                      <TableCell>{file.events_mapped || '—'}</TableCell>
                      <TableCell className="text-right">
                        <StatusBadge status={file.status} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
