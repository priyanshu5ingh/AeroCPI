import React, { useMemo } from 'react';
import katex from 'katex';

interface MathProps {
  math: string;
  className?: string;
  ariaLabel?: string;
}

/**
 * Inline mathematical formula rendered with KaTeX.
 * Designed for inline equations within explanatory text.
 */
export const InlineMath: React.FC<MathProps> = ({ math, className = '', ariaLabel }) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math, {
        displayMode: false,
        throwOnError: false,
        output: 'htmlAndMathml',
      });
    } catch {
      return `<span class="font-mono text-xs text-rose-500">${math}</span>`;
    }
  }, [math]);

  return (
    <span
      className={`inline-block align-middle select-text ${className}`}
      aria-label={ariaLabel || math}
      role="math"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

/**
 * Centered, display-mode mathematical formula rendered with KaTeX.
 * Responsive, scalable, and styled for both light and dark technical surfaces.
 */
export const BlockMath: React.FC<MathProps> = ({ math, className = '', ariaLabel }) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math, {
        displayMode: true,
        throwOnError: false,
        output: 'htmlAndMathml',
      });
    } catch {
      return `<div class="font-mono text-xs text-rose-500">${math}</div>`;
    }
  }, [math]);

  return (
    <div
      className={`w-full overflow-x-auto overflow-y-hidden py-1.5 text-center select-text font-serif ${className}`}
      aria-label={ariaLabel || math}
      role="math"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
