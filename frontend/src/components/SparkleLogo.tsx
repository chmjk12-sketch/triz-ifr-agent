import { motion } from 'framer-motion'

function SparkleLogo({ size = 48 }: { size?: number }) {
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      animate={{ rotate: [0, 360] }}
      transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
    >
      <defs>
        <linearGradient id="sparkle-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4285f4" />
          <stop offset="50%" stopColor="#9c27b0" />
          <stop offset="100%" stopColor="#00bcd4" />
        </linearGradient>
      </defs>
      <motion.path
        d="M24 0L28 20L48 24L28 28L24 48L20 28L0 24L20 20L24 0Z"
        fill="url(#sparkle-gradient)"
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
      />
    </motion.svg>
  )
}

export default SparkleLogo
