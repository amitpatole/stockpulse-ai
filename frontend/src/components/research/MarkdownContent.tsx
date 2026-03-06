'use client';

interface MarkdownContentProps {
  content: string;
}

export default function MarkdownContent({ content }: MarkdownContentProps) {
  // Simple markdown-to-HTML rendering for common patterns
  const html = content
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-white mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold text-white mt-5 mb-2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold text-white mt-6 mb-3">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc text-slate-300 mb-1">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal text-slate-300 mb-1">$2</li>')
    .replace(/`(.+?)`/g, '<code class="rounded bg-slate-700 px-1.5 py-0.5 text-xs text-blue-400 font-mono">$1</code>')
    .replace(/\n\n/g, '</p><p class="text-sm text-slate-300 leading-relaxed mb-3">')
    .replace(/\n/g, '<br />');

  return (
    <div
      className="prose prose-invert max-w-none text-sm text-slate-300 leading-relaxed"
      dangerouslySetInnerHTML={{ __html: `<p class="text-sm text-slate-300 leading-relaxed mb-3">${html}</p>` }}
    />
  );
}
