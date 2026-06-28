import { useState } from "react";
import type { FormEvent } from "react";

interface Props {
  sending: boolean;
  onSend: (message: string) => void;
}

export default function FollowUpComposer({ sending, onSend }: Props) {
  const [message, setMessage] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || sending) return;
    onSend(trimmed);
    setMessage("");
  }

  return (
    <form className="follow-up-composer" onSubmit={handleSubmit}>
      <input
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Ask a grounded follow-up"
        disabled={sending}
      />
      <button className="btn-primary" type="submit" disabled={sending || !message.trim()}>
        {sending ? "Sending..." : "Send"}
      </button>
    </form>
  );
}
