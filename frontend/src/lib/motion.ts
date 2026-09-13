import { Variants, Transition } from 'framer-motion';

// Transitions
export const springTight: Transition = {
  type: 'spring',
  stiffness: 400,
  damping: 30,
};

export const springSmooth: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 25,
};

export const easeOutStandard: Transition = {
  type: 'tween',
  ease: 'easeOut',
  duration: 0.2, // ~200ms Target: 180-240ms
};

export const easeOutFast: Transition = {
  type: 'tween',
  ease: 'easeOut',
  duration: 0.15, // ~150ms
};

// Page Transitions
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: springSmooth },
  exit: { opacity: 0, y: -4, transition: easeOutFast },
};

// Drawer Transitions
export const drawerVariants: Variants = {
  initial: { x: '100%', opacity: 0.8 },
  animate: { x: 0, opacity: 1, transition: springTight },
  exit: { x: '100%', opacity: 0.8, transition: springTight },
};

export const drawerBackdropVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 0.15, transition: easeOutStandard },
  exit: { opacity: 0, transition: easeOutFast },
};

// Trace Node Stagger
export const traceContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.015, // 50ms stagger
    },
  },
};

export const traceNodeVariants: Variants = {
  initial: { opacity: 0, y: 5 },
  animate: { opacity: 1, y: 0, transition: springSmooth },
};

// List Stagger (for general use)
export const listContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: { staggerChildren: 0.04 },
  },
};

export const listItemVariants: Variants = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0, transition: springSmooth },
};
