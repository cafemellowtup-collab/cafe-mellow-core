"use client";

import Link from "next/link";
import { Coffee, TrendingUp, Shield, Zap, BarChart3, Users, Clock, ArrowRight, Check, Star, ChevronRight } from "lucide-react";

export default function LandingPage() {
  const features = [
    {
      icon: TrendingUp,
      title: "Profit Intelligence",
      description: "AI detects profit leaks, revenue anomalies, and cost overruns before they hurt your bottom line."
    },
    {
      icon: BarChart3,
      title: "Real-Time Analytics",
      description: "Live dashboards with revenue, expenses, inventory, and staff metrics updated every minute."
    },
    {
      icon: Zap,
      title: "Smart Automation",
      description: "Auto-sync from POS, Drive folders, and APIs. No manual data entry, ever."
    },
    {
      icon: Shield,
      title: "Cost Guardrails",
      description: "Budget monitoring with alerts. Know exactly where every rupee goes."
    },
    {
      icon: Users,
      title: "Multi-Outlet Ready",
      description: "Manage multiple locations from one dashboard. Compare performance across outlets."
    },
    {
      icon: Clock,
      title: "Time-Saving AI",
      description: "Ask questions in plain English. Get instant answers with data citations."
    }
  ];

  const stats = [
    { value: "35%", label: "Average cost reduction" },
    { value: "2hrs", label: "Daily time saved" },
    { value: "99.9%", label: "Uptime guarantee" },
    { value: "24/7", label: "AI assistance" }
  ];

  const testimonials = [
    {
      quote: "TITAN found ₹45,000 in monthly profit leaks we didn't know existed. The ROI was immediate.",
      author: "Rahul K.",
      role: "Owner, Cafe Chain (3 outlets)"
    },
    {
      quote: "Finally, an ERP that understands restaurant operations. The AI chat is like having a CFO on demand.",
      author: "Priya M.",
      role: "Operations Manager"
    },
    {
      quote: "We switched from Petpooja analytics to TITAN. The difference in insights is night and day.",
      author: "Arjun S.",
      role: "F&B Director"
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-x-hidden">
      {/* Ambient Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(16,185,129,0.12),transparent_40%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(6,182,212,0.1),transparent_35%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_80%,rgba(139,92,246,0.08),transparent_40%)]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-xl sticky top-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Coffee className="h-5 w-5 text-slate-900" />
              </div>
              <span className="text-xl font-bold tracking-tight">TITAN ERP</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-zinc-400 hover:text-white transition text-sm font-medium">Features</a>
              <a href="#testimonials" className="text-zinc-400 hover:text-white transition text-sm font-medium">Testimonials</a>
              <a href="#pricing" className="text-zinc-400 hover:text-white transition text-sm font-medium">Pricing</a>
            </div>

            <div className="flex items-center gap-3">
              <Link 
                href="/login"
                className="px-4 py-2 text-sm font-medium text-zinc-300 hover:text-white transition"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 hover:from-emerald-400 hover:to-cyan-400 transition"
              >
                Start Free Trial
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-8">
            <Zap className="h-4 w-4" />
            AI-Powered Restaurant Intelligence
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            The Brain Behind<br />
            <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-violet-400 bg-clip-text text-transparent">
              Profitable Restaurants
            </span>
          </h1>
          
          <p className="text-xl text-zinc-400 max-w-3xl mx-auto mb-10">
            TITAN ERP combines real-time POS data, AI analytics, and automated operations 
            to help restaurant owners make precision decisions that drive profit.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/signup"
              className="group px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-lg font-semibold text-white shadow-xl shadow-emerald-500/25 hover:from-emerald-400 hover:to-cyan-400 transition flex items-center gap-2"
            >
              Start Free Trial
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition" />
            </Link>
            <Link
              href="/login"
              className="px-8 py-4 rounded-2xl bg-white/5 border border-white/10 text-lg font-medium text-zinc-300 hover:bg-white/10 hover:text-white transition"
            >
              Watch Demo
            </Link>
          </div>

          {/* Stats */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
            {stats.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-sm text-zinc-500 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Everything You Need to<br />
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                Run Smarter Operations
              </span>
            </h2>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              From POS integration to AI-powered insights, TITAN handles the complexity 
              so you can focus on what matters: great food and happy customers.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <div 
                key={i}
                className="group p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-emerald-500/30 hover:bg-white/10 transition duration-300"
              >
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center mb-4 group-hover:from-emerald-500/30 group-hover:to-cyan-500/30 transition">
                  <feature.icon className="h-6 w-6 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integration Section */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/5 bg-gradient-to-b from-transparent to-emerald-950/20">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold mb-6">
                Seamless Integration with<br />
                <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  Petpooja & Google Drive
                </span>
              </h2>
              <p className="text-zinc-400 mb-8">
                Connect your existing tools in minutes. TITAN pulls data automatically from your POS, 
                expense sheets, and inventory files — no manual uploads required.
              </p>
              
              <div className="space-y-4">
                {[
                  "Live order sync from Petpooja POS",
                  "Auto-import expenses from Google Drive",
                  "Recipe & BOM management",
                  "Inventory tracking with alerts"
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="h-6 w-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                      <Check className="h-4 w-4 text-emerald-400" />
                    </div>
                    <span className="text-zinc-300">{item}</span>
                  </div>
                ))}
              </div>

              <Link
                href="/signup"
                className="inline-flex items-center gap-2 mt-8 px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 font-semibold text-white shadow-lg shadow-emerald-500/25 hover:from-emerald-400 hover:to-cyan-400 transition"
              >
                Connect Your Data
                <ChevronRight className="h-5 w-5" />
              </Link>
            </div>

            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-3xl blur-3xl" />
              <div className="relative p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl">
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="h-10 w-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <Zap className="h-5 w-5 text-emerald-400" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-emerald-400">Petpooja Connected</div>
                      <div className="text-xs text-zinc-500">Live sync enabled</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                    <div className="h-10 w-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                      <BarChart3 className="h-5 w-5 text-cyan-400" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-cyan-400">Google Drive Synced</div>
                      <div className="text-xs text-zinc-500">5 folders monitored</div>
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                    <div className="text-xs text-zinc-500 mb-2">Last sync: 2 minutes ago</div>
                    <div className="text-sm text-zinc-300">1,247 orders • ₹2,34,500 revenue today</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Trusted by Restaurant Owners
            </h2>
            <p className="text-zinc-400">See what our customers have to say</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/5">
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, j) => (
                    <Star key={j} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-zinc-300 mb-4 italic">&ldquo;{t.quote}&rdquo;</p>
                <div>
                  <div className="font-medium text-white">{t.author}</div>
                  <div className="text-sm text-zinc-500">{t.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Transform Your<br />
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Restaurant Operations?
            </span>
          </h2>
          <p className="text-zinc-400 mb-10 max-w-2xl mx-auto">
            Join hundreds of restaurant owners who are using AI to make smarter decisions, 
            reduce costs, and grow profits. Start your free trial today.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/signup"
              className="group px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-lg font-semibold text-white shadow-xl shadow-emerald-500/25 hover:from-emerald-400 hover:to-cyan-400 transition flex items-center gap-2"
            >
              Start Free Trial
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition" />
            </Link>
            <span className="text-zinc-500 text-sm">No credit card required</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-400 flex items-center justify-center">
                <Coffee className="h-4 w-4 text-slate-900" />
              </div>
              <span className="font-bold">TITAN ERP</span>
            </div>
            
            <div className="flex items-center gap-8 text-sm text-zinc-500">
              <a href="#" className="hover:text-white transition">Privacy</a>
              <a href="#" className="hover:text-white transition">Terms</a>
              <a href="#" className="hover:text-white transition">Contact</a>
            </div>

            <div className="text-sm text-zinc-500">
              © 2026 TITAN ERP. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
