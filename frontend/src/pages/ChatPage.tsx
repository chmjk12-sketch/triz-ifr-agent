import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Plus, Mic, Loader2, User, Bot,
  ChevronDown, Lightbulb, Target, Search, Rocket
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  nodes?: {
    node1?: any
    node2?: any
    node3?: any
    node4?: any
  }
}

function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setShowWelcome(false)

    try {
      const response = await fetch('/api/v1/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem: userMessage.content,
          industry: '通用',
          constraints: []
        })
      })

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: formatResponse(data),
        timestamp: new Date(),
        nodes: data.data
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，求解过程中出现错误。请稍后重试。',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const formatResponse = (data: any): string => {
    if (!data.data) return '暂无结果'

    const { node1_deconstruction, node2_ifr_anchor, node3_resource_scan, node4_actionable_plan } = data.data

    return `
## Node 1: 问题功能化解构

**终极功能**: ${node1_deconstruction?.ultimate_function || 'N/A'}

**有害因素**:
${node1_deconstruction?.harmful_factors?.map((f: string) => `- ${f}`).join('\n') || 'N/A'}

**已剪枝的低理想度路径**:
${node1_deconstruction?.low_ideality_traps?.map((t: string) => `- ${t}`).join('\n') || 'N/A'}

---

## Node 2: IFR 顶点锚定

**IFR 公式类型**: ${node2_ifr_anchor?.ifr_formula_type || 'N/A'}

**IFR 描述**: ${node2_ifr_anchor?.ifr_description || 'N/A'}

**可行性差距**: ${node2_ifr_anchor?.feasibility_gap || 'N/A'}

---

## Node 3: 逆向资源扫描

**物理矛盾**:
${node3_resource_scan?.physical_contradictions?.map((c: any) => `- ${c.parameter}: ${c.requirement_a} vs ${c.requirement_not_a}`).join('\n') || 'N/A'}

**外部资源**:
${node3_resource_scan?.external_resources?.map((r: any) => `- [${r.source}] ${r.name} (${r.cost_type})`).join('\n') || 'N/A'}

**矛盾解决思路**: ${node3_resource_scan?.contradiction_resolution || 'N/A'}

---

## Node 4: 可执行落地方案

**行动步骤**:
${node4_actionable_plan?.action_steps?.map((s: any) => `${s.step_number}. **${s.title}**: ${s.description} (预计: ${s.estimated_effort})`).join('\n') || 'N/A'}

**成功指标**:
${node4_actionable_plan?.success_metrics?.map((m: string) => `- ${m}`).join('\n') || 'N/A'}
    `.trim()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const suggestions = [
    '如何在不增加成本的情况下提升系统性能？',
    '怎样用现有开源工具替代昂贵的商业软件？',
    '如何在资源有限的情况下快速验证产品想法？'
  ]

  return (
    <div className="chat-page">
      {/* Messages Area */}
      <div className="messages-container">
        <AnimatePresence>
          {showWelcome && messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="welcome-screen"
            >
              <div className="welcome-icon">
                <Bot size={48} />
              </div>
              <h2 className="welcome-title">TRIZ IFR 逆向收敛专家</h2>
              <p className="welcome-subtitle">
                描述你的问题，我将通过四步法帮你找到最优的可执行方案
              </p>

              <div className="suggestions">
                {suggestions.map((suggestion, index) => (
                  <motion.button
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    className="suggestion-chip"
                    onClick={() => {
                      setInput(suggestion)
                      inputRef.current?.focus()
                    }}
                  >
                    {suggestion}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {messages.map((message, index) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`message ${message.role}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? (
                <User size={18} />
              ) : (
                <Bot size={18} />
              )}
            </div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">
                  {message.role === 'user' ? '你' : 'TRIZ IFR'}
                </span>
                <span className="message-time">
                  {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div className="message-body">
                {message.role === 'assistant' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                ) : (
                  <p>{message.content}</p>
                )}
              </div>

              {/* Node visualization for assistant messages */}
              {message.role === 'assistant' && message.nodes && (
                <div className="node-visualization">
                  <div className="node-flow">
                    {[
                      { icon: <Lightbulb size={14} />, label: '解构', active: !!message.nodes.node1 },
                      { icon: <Target size={14} />, label: 'IFR', active: !!message.nodes.node2 },
                      { icon: <Search size={14} />, label: '扫描', active: !!message.nodes.node3 },
                      { icon: <Rocket size={14} />, label: '方案', active: !!message.nodes.node4 }
                    ].map((node, i) => (
                      <div key={i} className={`node-badge ${node.active ? 'active' : ''}`}>
                        {node.icon}
                        <span>{node.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="message assistant"
          >
            <div className="message-avatar">
              <Bot size={18} />
            </div>
            <div className="message-content">
              <div className="loading-indicator">
                <Loader2 size={16} className="spin" />
                <span>正在逆向收敛求解...</span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Gemini Style */}
      <div className="input-area">
        <div className="input-container">
          <button className="input-action" aria-label="新建对话">
            <Plus size={20} />
          </button>

          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="描述你的问题..."
              rows={1}
              className="chat-input"
            />
          </div>

          <button className="input-action" aria-label="语音输入">
            <Mic size={20} />
          </button>

          <button
            className={`send-button ${input.trim() ? 'active' : ''}`}
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            aria-label="发送"
          >
            <Send size={18} />
          </button>
        </div>

        <p className="input-hint">
          TRIZ IFR 可能会生成不准确的信息，请验证重要信息。
        </p>
      </div>

      <style>{`
        .chat-page {
          display: flex;
          flex-direction: column;
          height: 100vh;
          padding-top: 56px;
        }
        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: var(--space-lg);
          max-width: 900px;
          width: 100%;
          margin: 0 auto;
        }

        /* Welcome Screen */
        .welcome-screen {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 60vh;
          text-align: center;
          gap: var(--space-lg);
        }
        .welcome-icon {
          color: var(--accent-cyan);
          opacity: 0.8;
        }
        .welcome-title {
          font-size: 1.8rem;
          font-weight: 700;
          color: var(--text-primary);
        }
        .welcome-subtitle {
          font-size: 1rem;
          color: var(--text-secondary);
          max-width: 400px;
        }
        .suggestions {
          display: flex;
          flex-direction: column;
          gap: var(--space-sm);
          margin-top: var(--space-lg);
          width: 100%;
          max-width: 500px;
        }
        .suggestion-chip {
          padding: var(--space-md) var(--space-lg);
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          font-size: 0.9rem;
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: left;
        }
        .suggestion-chip:hover {
          border-color: var(--border-medium);
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        /* Messages */
        .message {
          display: flex;
          gap: var(--space-md);
          margin-bottom: var(--space-xl);
          animation: slideUp 0.3s ease;
        }
        .message-avatar {
          width: 32px;
          height: 32px;
          border-radius: var(--radius-full);
          background: var(--bg-surface);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          color: var(--text-secondary);
        }
        .message.assistant .message-avatar {
          background: var(--accent-gradient);
          color: white;
        }
        .message-content {
          flex: 1;
          min-width: 0;
        }
        .message-header {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
          margin-bottom: var(--space-xs);
        }
        .message-role {
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--text-primary);
        }
        .message-time {
          font-size: 0.75rem;
          color: var(--text-muted);
        }
        .message-body {
          color: var(--text-primary);
          line-height: 1.7;
        }
        .message-body p {
          margin-bottom: var(--space-sm);
        }
        .message-body h2 {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text-accent);
          margin: var(--space-lg) 0 var(--space-sm);
          padding-bottom: var(--space-xs);
          border-bottom: 1px solid var(--border-subtle);
        }
        .message-body ul {
          margin: var(--space-sm) 0;
          padding-left: var(--space-lg);
        }
        .message-body li {
          margin-bottom: var(--space-xs);
        }
        .message-body strong {
          color: var(--text-accent);
        }
        .message-body code {
          background: var(--bg-surface);
          padding: 2px 6px;
          border-radius: var(--radius-sm);
          font-family: var(--font-mono);
          font-size: 0.85em;
        }

        /* Node Visualization */
        .node-visualization {
          margin-top: var(--space-md);
          padding-top: var(--space-md);
          border-top: 1px solid var(--border-subtle);
        }
        .node-flow {
          display: flex;
          gap: var(--space-sm);
          flex-wrap: wrap;
        }
        .node-badge {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-full);
          font-size: 0.75rem;
          color: var(--text-muted);
          transition: all var(--transition-fast);
        }
        .node-badge.active {
          background: rgba(66, 133, 244, 0.15);
          border-color: rgba(66, 133, 244, 0.3);
          color: var(--text-accent);
        }

        /* Loading */
        .loading-indicator {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
          color: var(--text-secondary);
          font-size: 0.9rem;
        }
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* Input Area */
        .input-area {
          padding: var(--space-md) var(--space-lg);
          background: var(--bg-primary);
          border-top: 1px solid var(--border-subtle);
        }
        .input-container {
          max-width: 800px;
          margin: 0 auto;
          display: flex;
          align-items: flex-end;
          gap: var(--space-sm);
          padding: var(--space-sm);
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-xl);
          transition: border-color var(--transition-fast);
        }
        .input-container:focus-within {
          border-color: var(--border-focus);
        }
        .input-action {
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: var(--space-sm);
          border-radius: var(--radius-md);
          transition: all var(--transition-fast);
          flex-shrink: 0;
        }
        .input-action:hover {
          color: var(--text-primary);
          background: var(--bg-tertiary);
        }
        .input-wrapper {
          flex: 1;
          min-width: 0;
        }
        .chat-input {
          width: 100%;
          background: none;
          border: none;
          color: var(--text-primary);
          font-size: 0.95rem;
          line-height: 1.5;
          resize: none;
          outline: none;
          max-height: 200px;
          font-family: inherit;
        }
        .chat-input::placeholder {
          color: var(--text-muted);
        }
        .send-button {
          background: var(--bg-tertiary);
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: var(--space-sm);
          border-radius: var(--radius-md);
          transition: all var(--transition-fast);
          flex-shrink: 0;
        }
        .send-button.active {
          background: var(--accent-gradient);
          color: white;
        }
        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .input-hint {
          text-align: center;
          font-size: 0.75rem;
          color: var(--text-muted);
          margin-top: var(--space-sm);
        }

        @media (max-width: 768px) {
          .messages-container {
            padding: var(--space-md);
          }
          .message {
            gap: var(--space-sm);
          }
          .input-area {
            padding: var(--space-sm);
          }
        }
      `}</style>
    </div>
  )
}

export default ChatPage
