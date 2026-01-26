"use client";

import { motion } from "framer-motion";
import { MapPin, ChevronDown } from "lucide-react";
import { useTenant } from "@/contexts/TenantContext";
import { useState, useRef, useEffect } from "react";

export default function LocationSelector() {
  const { tenant, setTenant, availableLocations } = useTenant();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <motion.button
        whileTap={{ scale: 0.97 }}
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white shadow-lg backdrop-blur-sm transition hover:border-emerald-400/40 hover:bg-white/10"
        type="button"
      >
        <MapPin size={16} className="text-emerald-300" />
        <div className="text-left">
          <div className="text-[11px] uppercase tracking-wider text-zinc-400">Location</div>
          <div className="text-sm font-semibold">{tenant.location_name}</div>
        </div>
        <ChevronDown
          size={16}
          className={`text-zinc-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </motion.button>

      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute right-0 top-full z-50 mt-2 w-64 rounded-xl border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(52,211,153,0.15),_transparent_50%),_rgba(12,12,16,0.98)] p-2 shadow-2xl backdrop-blur-xl"
        >
          <div className="mb-2 px-3 py-2">
            <div className="text-[11px] uppercase tracking-wider text-emerald-200">
              Select Outlet
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              Switch between locations
            </div>
          </div>
          <div className="space-y-1">
            {availableLocations.map((loc) => {
              const isActive =
                loc.org_id === tenant.org_id && loc.location_id === tenant.location_id;
              return (
                <motion.button
                  key={`${loc.org_id}-${loc.location_id}`}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setTenant(loc);
                    setIsOpen(false);
                  }}
                  className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm transition ${
                    isActive
                      ? "border border-emerald-400/40 bg-emerald-500/15 text-white"
                      : "border border-transparent bg-white/5 text-zinc-200 hover:border-white/10 hover:bg-white/10"
                  }`}
                  type="button"
                >
                  <div>
                    <div className="font-semibold">{loc.location_name}</div>
                    <div className="text-xs text-zinc-400">{loc.org_name}</div>
                  </div>
                  {isActive && (
                    <div className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
                  )}
                </motion.button>
              );
            })}
          </div>
        </motion.div>
      )}
    </div>
  );
}
