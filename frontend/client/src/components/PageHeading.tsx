import type { ReactNode } from 'react';

interface PageHeadingProps {
  index: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export default function PageHeading({ index, title, subtitle, actions }: PageHeadingProps) {
  return (
    <header className="page-heading">
      <div className="page-heading-index">{index}</div>
      <div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="page-heading-actions">{actions}</div>}
    </header>
  );
}
