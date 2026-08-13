import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';

const stars = [
{ top: 6, left: 10, size: 2 },
{ top: 14, left: 18, size: 1.5 },
{ top: 9, left: 26, size: 1 }];


export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  const reduceMotion = useReducedMotion();

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? 'Switch to day mode' : 'Switch to night mode'}
      onClick={toggleTheme}
      className="relative h-8 w-[68px] shrink-0 overflow-hidden rounded-full border transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      style={{
        borderColor: isDark ? '#1E3A5F' : '#7DD3FC',
        backgroundColor: isDark ? '#020617' : '#DFF1FD'
      }}>
      
      {/* night sky */}
      <span className="pointer-events-none absolute inset-0">
        {stars.map((star) =>
        <motion.span
          key={`${star.top}-${star.left}`}
          className="absolute rounded-full bg-sky-100"
          style={{
            top: star.top,
            left: star.left,
            width: star.size,
            height: star.size,
            backgroundColor: '#E0F2FE'
          }}
          animate={{ opacity: isDark ? 0.9 : 0 }}
          transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }} />

        )}
      </span>

      {/* daylight cloud */}
      <motion.span
        className="pointer-events-none absolute bottom-1 left-2 h-2.5 w-6 rounded-full"
        style={{ backgroundColor: '#FFFFFF' }}
        animate={{ opacity: isDark ? 0 : 0.95, y: isDark ? 6 : 0 }}
        transition={{ duration: 0.22, ease: [0.23, 1, 0.32, 1] }} />
      

      {/* knob */}
      <motion.span
        className="absolute top-1 flex h-6 w-6 items-center justify-center rounded-full"
        style={{ boxShadow: '0 2px 6px rgba(2,6,23,0.35)' }}
        animate={{
          left: isDark ? 4 : 38,
          backgroundColor: isDark ? '#CBD5E1' : '#FBBF24'
        }}
        transition={
        reduceMotion ?
        { duration: 0 } :
        { type: 'spring', stiffness: 520, damping: 32, mass: 0.6 }
        }>
        
        {/* moon crater shadow that slides away in day mode */}
        <motion.span
          className="absolute h-4 w-4 rounded-full"
          style={{ backgroundColor: isDark ? '#020617' : '#DFF1FD' }}
          animate={{ x: isDark ? 5 : 14, opacity: isDark ? 1 : 0 }}
          transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }} />
        
        {/* sun rays */}
        <motion.span
          className="absolute inset-0 rounded-full"
          style={{ boxShadow: '0 0 0 3px rgba(251,191,36,0.35)' }}
          animate={{ opacity: isDark ? 0 : 1, scale: isDark ? 0.6 : 1 }}
          transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }} />
        
      </motion.span>
    </button>);

}