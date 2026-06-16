import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Zap, Target, Search, Rocket } from 'lucide-react'
import SparkleLogo from '../components/SparkleLogo'

function HomePage() {
  const features = [
    {
      icon: <Target size={24} />,
      title: 'IFR 顶点锚定',
      description: '从最终理想解出发，逆向寻找最优路径'
    },
    {
      icon: <Search size={24} />,
      title: '生态资源扫描',
      description: '自动发现外部免费资源，替代内部损耗'
    },
    {
      icon: <Zap size={24} />,
      title: '物理矛盾消解',
      description: '运用 TRIZ 分离原理，化解核心冲突'
    },
    {
      icon: <Rocket size={24} />,
      title: '可执行方案',
      description: '输出具备工程可执行性的落地方案'
    }
  ]

  return (
    <div className="home-page">
      {/* Hero Section - Gemini Style */}
      <section className="hero">
        <div className="hero-content">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="hero-logo"
          >
            <SparkleLogo size={64} />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="hero-title"
          >
            认识 TRIZ IFR
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="hero-subtitle"
          >
            你的逆向收敛专家
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <Link to="/chat" className="hero-cta">
              <span>开始对话</span>
              <ArrowRight size={18} />
            </Link>
          </motion.div>
        </div>

        {/* Background gradient effect */}
        <div className="hero-bg-gradient" />
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="features-grid">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 + index * 0.1 }}
              className="feature-card"
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-desc">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="how-it-works">
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="section-title"
        >
          通用求解四步法
        </motion.h2>

        <div className="steps">
          {[
            { num: '01', title: '问题功能化解构', desc: '将问题转化为终极功能与有害因素' },
            { num: '02', title: 'IFR 顶点锚定', desc: '定义最终理想解的顶点状态' },
            { num: '03', title: '逆向资源扫描', desc: '扫描外部免费资源，卡出物理矛盾' },
            { num: '04', title: '可执行方案输出', desc: '输出具备工程可执行性的落地方案' }
          ].map((step, index) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.4 + index * 0.15 }}
              className="step-item"
            >
              <span className="step-num">{step.num}</span>
              <div className="step-content">
                <h4>{step.title}</h4>
                <p>{step.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <style>{`
        .home-page {
          min-height: 100vh;
        }
        .hero {
          position: relative;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: var(--space-xl);
          overflow: hidden;
        }
        .hero-bg-gradient {
          position: absolute;
          inset: 0;
          background: radial-gradient(ellipse at 50% 50%, rgba(66, 133, 244, 0.08) 0%, transparent 70%);
          pointer-events: none;
        }
        .hero-content {
          position: relative;
          z-index: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-lg);
        }
        .hero-logo {
          margin-bottom: var(--space-md);
        }
        .hero-title {
          font-size: clamp(2rem, 5vw, 3.5rem);
          font-weight: 700;
          color: var(--text-primary);
          letter-spacing: -0.02em;
        }
        .hero-subtitle {
          font-size: clamp(1.1rem, 2.5vw, 1.5rem);
          color: var(--text-secondary);
          font-weight: 400;
        }
        .hero-cta {
          display: inline-flex;
          align-items: center;
          gap: var(--space-sm);
          padding: var(--space-md) var(--space-xl);
          background: var(--accent-gradient);
          background-size: 200% 200%;
          color: white;
          text-decoration: none;
          border-radius: var(--radius-full);
          font-weight: 600;
          font-size: 1rem;
          transition: all var(--transition-normal);
          box-shadow: var(--shadow-glow);
          margin-top: var(--space-md);
        }
        .hero-cta:hover {
          transform: translateY(-2px);
          box-shadow: 0 0 30px rgba(66, 133, 244, 0.3);
        }

        .features {
          padding: var(--space-3xl) var(--space-xl);
          max-width: 1200px;
          margin: 0 auto;
        }
        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: var(--space-lg);
        }
        .feature-card {
          padding: var(--space-xl);
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          transition: all var(--transition-normal);
        }
        .feature-card:hover {
          border-color: var(--border-medium);
          transform: translateY(-4px);
          box-shadow: var(--shadow-md);
        }
        .feature-icon {
          color: var(--accent-cyan);
          margin-bottom: var(--space-md);
        }
        .feature-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--space-sm);
        }
        .feature-desc {
          font-size: 0.9rem;
          color: var(--text-secondary);
          line-height: 1.5;
        }

        .how-it-works {
          padding: var(--space-3xl) var(--space-xl);
          max-width: 800px;
          margin: 0 auto;
        }
        .section-title {
          text-align: center;
          font-size: 1.8rem;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: var(--space-2xl);
        }
        .steps {
          display: flex;
          flex-direction: column;
          gap: var(--space-lg);
        }
        .step-item {
          display: flex;
          align-items: flex-start;
          gap: var(--space-lg);
          padding: var(--space-lg);
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
        }
        .step-num {
          font-size: 1.5rem;
          font-weight: 700;
          background: var(--accent-gradient);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          flex-shrink: 0;
          min-width: 40px;
        }
        .step-content h4 {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--space-xs);
        }
        .step-content p {
          font-size: 0.9rem;
          color: var(--text-secondary);
        }

        @media (max-width: 768px) {
          .hero {
            min-height: 80vh;
            padding: var(--space-lg);
          }
          .features-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  )
}

export default HomePage
