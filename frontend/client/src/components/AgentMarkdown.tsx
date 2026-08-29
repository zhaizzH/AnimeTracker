import type { ComponentPropsWithoutRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function MarkdownTable({ children, ...props }: ComponentPropsWithoutRef<'table'>) {
  return (
    <div className="od-agent-table-scroll" role="region" aria-label="表格，可横向滚动" tabIndex={0}>
      <table {...props}>{children}</table>
    </div>
  );
}

export default function AgentMarkdown({ children }: { children: string }) {
  return (
    <div className="od-agent-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ table: MarkdownTable }}>
        {children}
      </ReactMarkdown>
    </div>
  );
}

