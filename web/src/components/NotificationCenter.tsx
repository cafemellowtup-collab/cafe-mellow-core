"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, X, AlertTriangle, Info, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";

type NotificationType = "critical" | "warning" | "info" | "success";

type Notification = {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
};

const API_PREFIX = "/api/v1";

export default function NotificationCenter() {
  const { tenant } = useTenant();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchNotifications();
    // Poll for new notifications every 60 seconds
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, [tenant.org_id, tenant.location_id]);

  useEffect(() => {
    setUnreadCount(notifications.filter(n => !n.read).length);
  }, [notifications]);

  async function fetchNotifications() {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        org_id: tenant.org_id,
        location_id: tenant.location_id,
      });
      
      const res = await fetch(`${API_BASE_URL}${API_PREFIX}/notifications?${params}`);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
      } else {
        // If API doesn't exist yet, show sample notifications for demo
        setNotifications(getSampleNotifications());
      }
    } catch {
      // Show sample notifications if API fails
      setNotifications(getSampleNotifications());
    } finally {
      setLoading(false);
    }
  }

  function getSampleNotifications(): Notification[] {
    const now = new Date();
    return [
      {
        id: "1",
        type: "warning",
        title: "Data Freshness Alert",
        message: "Sales data hasn't been synced in 24 hours. Consider running a sync.",
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        read: false,
      },
      {
        id: "2",
        type: "info",
        title: "New AI Insight Available",
        message: "TITAN has detected a pattern in your weekend sales. Check the dashboard.",
        timestamp: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
        read: false,
      },
      {
        id: "3",
        type: "success",
        title: "Daily Sync Complete",
        message: "All data sources have been synchronized successfully.",
        timestamp: new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString(),
        read: true,
      },
    ];
  }

  function markAsRead(id: string) {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }

  function markAllAsRead() {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }

  function dismissNotification(id: string) {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }

  function getIcon(type: NotificationType) {
    switch (type) {
      case "critical":
        return <XCircle size={16} className="text-red-400" />;
      case "warning":
        return <AlertTriangle size={16} className="text-amber-400" />;
      case "info":
        return <Info size={16} className="text-blue-400" />;
      case "success":
        return <CheckCircle size={16} className="text-emerald-400" />;
    }
  }

  function getBgColor(type: NotificationType, read: boolean) {
    if (read) return "bg-zinc-900/50";
    switch (type) {
      case "critical":
        return "bg-red-500/10 border-red-500/30";
      case "warning":
        return "bg-amber-500/10 border-amber-500/30";
      case "info":
        return "bg-blue-500/10 border-blue-500/30";
      case "success":
        return "bg-emerald-500/10 border-emerald-500/30";
    }
  }

  function formatTime(timestamp: string) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative rounded-full border border-white/10 bg-white/5 p-2 text-zinc-300 transition hover:bg-white/10 hover:text-white"
        aria-label="Notifications"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="absolute right-0 top-full z-50 mt-2 w-80 rounded-2xl border border-white/10 bg-zinc-900 shadow-2xl shadow-black/50"
            >
              <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                <div className="flex items-center gap-2">
                  <Bell size={16} className="text-emerald-400" />
                  <span className="text-sm font-semibold text-white">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-200">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={fetchNotifications}
                    disabled={loading}
                    className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-white/10 hover:text-white disabled:opacity-50"
                    aria-label="Refresh"
                  >
                    <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-white/10 hover:text-white"
                    aria-label="Close"
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>

              <div className="max-h-[400px] overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-zinc-500">
                    No notifications
                  </div>
                ) : (
                  <div className="space-y-1 p-2">
                    {notifications.map((notification) => (
                      <motion.div
                        key={notification.id}
                        layout
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        onClick={() => markAsRead(notification.id)}
                        className={`group cursor-pointer rounded-xl border p-3 transition hover:bg-white/5 ${getBgColor(notification.type, notification.read)}`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-start gap-2">
                            <div className="mt-0.5">{getIcon(notification.type)}</div>
                            <div className="min-w-0">
                              <div className={`text-xs font-semibold ${notification.read ? "text-zinc-300" : "text-white"}`}>
                                {notification.title}
                              </div>
                              <div className="mt-0.5 text-[11px] text-zinc-400 line-clamp-2">
                                {notification.message}
                              </div>
                              <div className="mt-1 text-[10px] text-zinc-500">
                                {formatTime(notification.timestamp)}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              dismissNotification(notification.id);
                            }}
                            className="rounded p-1 text-zinc-500 opacity-0 transition hover:bg-white/10 hover:text-white group-hover:opacity-100"
                            aria-label="Dismiss"
                          >
                            <X size={12} />
                          </button>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>

              {notifications.length > 0 && unreadCount > 0 && (
                <div className="border-t border-white/10 p-2">
                  <button
                    onClick={markAllAsRead}
                    className="w-full rounded-xl bg-white/5 px-3 py-2 text-xs font-semibold text-zinc-300 transition hover:bg-white/10 hover:text-white"
                  >
                    Mark all as read
                  </button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
