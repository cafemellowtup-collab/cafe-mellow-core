import DashboardClient from "./DashboardClient";
import LocationSelector from "@/components/LocationSelector";

export default function DashboardPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Dashboard</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Choose any range (presets or custom dates) to refresh KPIs, trends, and tasks.
          </p>
        </div>
        <LocationSelector />
      </div>
      <DashboardClient />
    </div>
  );
}
