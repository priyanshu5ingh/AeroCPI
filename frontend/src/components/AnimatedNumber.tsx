import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface AnimatedNumberProps {
  value: number;
  decimals?: number;
  prefix?: string;
  className?: string;
}

export const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
  value,
  decimals = 2,
  prefix = '',
  className = '',
}) => {
  // Graceful fallback for jsdom where matchMedia might fail in useReducedMotion
  const hasMatchMedia = typeof window !== 'undefined' && typeof window.matchMedia === 'function';
  const prefersReducedMotion = hasMatchMedia ? useReducedMotion() : true;
  
  const isNegative = value < 0 && prefix === '+';
  const displayPrefix = isNegative ? '' : prefix;
  const formatted = `${displayPrefix}${value.toFixed(decimals)}`;

  return (
    <motion.span
      className={className}
      initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      {formatted}
    </motion.span>
  );
};
