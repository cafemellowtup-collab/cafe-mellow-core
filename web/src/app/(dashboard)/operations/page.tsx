import OperationsClient from "../../operations/OperationsClient";

export default function OperationsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Operations</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Manage inventory, recipes, purchases, and operational workflows.
        </p>
      </div>
      <OperationsClient />
    </div>
  );
}
