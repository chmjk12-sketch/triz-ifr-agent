import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  const navItems = [
    { path: '/', label: '首页' },
    { path: '/chat', label: '对话' },
  ]

  return (
    <header className="header">
      <div className="header-inner">
        <Link to="/" className="header-brand">
          <Sparkles className="brand-icon" size={20} />
          <span className="brand-text">TRIZ IFR</span>
        </Link>

        <nav className="header-nav desktop-only">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          className="menu-toggle mobile-only"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="切换菜单"
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <AnimatePresence>
        {menuOpen && (
          <motion.nav
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mobile-nav"
          >
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`mobile-nav-link ${location.pathname === item.path ? 'active' : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}
          </motion.nav>
        )}
      </AnimatePresence>

      <style>{`
        .header {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 100;
          background: rgba(10, 10, 15, 0.8);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid var(--border-subtle);
        }
        .header-inner {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 var(--space-lg);
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .header-brand {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
          text-decoration: none;
          color: var(--text-primary);
          font-weight: 600;
          font-size: 1.1rem;
        }
        .brand-icon {
          color: var(--accent-cyan);
        }
        .brand-text {
          background: var(--accent-gradient);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .header-nav {
          display: flex;
          gap: var(--space-lg);
        }
        .nav-link {
          color: var(--text-secondary);
          text-decoration: none;
          font-size: 0.9rem;
          font-weight: 500;
          padding: var(--space-xs) var(--space-sm);
          border-radius: var(--radius-sm);
          transition: all var(--transition-fast);
        }
        .nav-link:hover, .nav-link.active {
          color: var(--text-primary);
          background: var(--bg-surface);
        }
        .menu-toggle {
          display: none;
          background: none;
          border: none;
          color: var(--text-primary);
          cursor: pointer;
          padding: var(--space-sm);
        }
        .mobile-nav {
          display: none;
          flex-direction: column;
          padding: var(--space-md);
          gap: var(--space-sm);
          border-top: 1px solid var(--border-subtle);
          background: rgba(10, 10, 15, 0.95);
        }
        .mobile-nav-link {
          color: var(--text-secondary);
          text-decoration: none;
          padding: var(--space-sm) var(--space-md);
          border-radius: var(--radius-sm);
          transition: all var(--transition-fast);
        }
        .mobile-nav-link:hover, .mobile-nav-link.active {
          color: var(--text-primary);
          background: var(--bg-surface);
        }
        @media (max-width: 768px) {
          .desktop-only { display: none; }
          .menu-toggle { display: flex; }
          .mobile-nav { display: flex; }
        }
      `}</style>
    </header>
  )
}

export default Header
