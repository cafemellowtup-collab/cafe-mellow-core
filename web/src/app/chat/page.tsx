import ChatClientEnhanced from "./ChatClientEnhanced";

export default function ChatPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Chat</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Ask questions like a founder. Get answers like a CEO.
        </p>
      </div>
      <ChatClientEnhanced />
    </div>
  );
}
