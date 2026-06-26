import { useEffect, useRef } from "react";

interface Props {
  text: string;
  highlight: { start: number; end: number } | null;
}

// ponytail: single active highlight; replace if multi-highlight needed
export default function DocViewer({ text, highlight }: Props) {
  const markRef = useRef<HTMLElement>(null);

  useEffect(() => {
    markRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlight]);

  if (!highlight) {
    return <pre className="doc-text">{text}</pre>;
  }

  return (
    <pre className="doc-text">
      {text.slice(0, highlight.start)}
      <mark ref={markRef}>{text.slice(highlight.start, highlight.end)}</mark>
      {text.slice(highlight.end)}
    </pre>
  );
}
