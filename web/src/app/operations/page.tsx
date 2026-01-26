import dynamic from "next/dynamic";

const OperationsClient = dynamic(() => import("./OperationsClient"), {
  loading: () => (
    <div className="space-y-3 rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="h-5 w-32 animate-pulse rounded bg-white/10" />
      <div className="grid gap-3 md:grid-cols-2">
        {[1, 2, 3, 4].map((k) => (
          <div key={k} className="rounded-xl border border-white/10 bg-white/5 p-3">
            <div className="h-4 w-24 animate-pulse rounded bg-white/10" />
            <div className="mt-2 h-3 w-full animate-pulse rounded bg-white/10" />
            <div className="mt-2 h-3 w-2/3 animate-pulse rounded bg-white/10" />
          </div>
        ))}
      </div>
    </div>
  ),
});

export default function OperationsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Operations</h1>
        <p className="mt-1 text-sm text-zinc-500">Explore expenses and drill down operational drivers.</p>
      </div>
      <OperationsClient />
    </div>
  );
}
