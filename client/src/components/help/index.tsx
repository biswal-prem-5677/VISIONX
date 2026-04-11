/**
 * VisionX — Help Center sub-components
 * HelpSearch, ArticleViewer, TicketForm, TicketList, LiveChat, ContextualHelp
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlowButton } from '../ui/GlowButton';

// ─── HelpSearch ──────────────────────────────────

export function HelpSearch({ onSearch }: { onSearch?: (query: string) => void }) {
  const [query, setQuery] = useState('');
  return (
    <div style={{
      display: 'flex', gap: 8, padding: 16,
      background: 'var(--surface)', borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border)',
    }}>
      <span style={{ fontSize: 18, opacity: 0.5 }}>🔍</span>
      <input
        value={query} onChange={(e) => { setQuery(e.target.value); onSearch?.(e.target.value); }}
        placeholder="Search help articles, FAQs, guides..."
        style={{
          flex: 1, background: 'transparent', border: 'none', outline: 'none',
          color: 'var(--text-primary)', fontSize: '0.9rem', fontFamily: 'var(--font-sans)',
        }}
      />
    </div>
  );
}

// ─── ArticleViewer ──────────────────────────────────

interface Article {
  title: string; content: string; category: string; readTime: string;
}

export function ArticleViewer({ article, onBack }: { article: Article; onBack: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
      <button onClick={onBack} className="text-sm"
        style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', marginBottom: 16, fontFamily: 'var(--font-sans)' }}>
        ← Back to articles
      </button>
      <span className="badge badge-accent" style={{ marginBottom: 8, display: 'inline-block' }}>{article.category}</span>
      <h2 className="text-xl font-bold" style={{ marginBottom: 8 }}>{article.title}</h2>
      <p className="text-xs" style={{ color: 'var(--text-tertiary)', marginBottom: 20 }}>📖 {article.readTime} read</p>
      <div className="text-sm" style={{ lineHeight: 1.8, color: 'var(--text-secondary)' }}>
        {article.content}
      </div>
    </motion.div>
  );
}

// ─── TicketForm ──────────────────────────────────

export function TicketForm({ onSubmit }: { onSubmit?: (subject: string, description: string) => void }) {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = () => {
    if (!subject || !description) return;
    onSubmit?.(subject, description);
    setSubject('');
    setDescription('');
  };

  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>📝 Submit Ticket</h3>
      <input value={subject} onChange={(e) => setSubject(e.target.value)}
        placeholder="Subject"
        style={{
          width: '100%', padding: 10, marginBottom: 10, borderRadius: 'var(--radius-sm)',
          background: 'var(--surface)', border: '1px solid var(--border)',
          color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none',
          fontFamily: 'var(--font-sans)',
        }}
      />
      <textarea value={description} onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe your issue..."
        rows={4}
        style={{
          width: '100%', padding: 10, marginBottom: 12, borderRadius: 'var(--radius-sm)',
          background: 'var(--surface)', border: '1px solid var(--border)',
          color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none',
          resize: 'vertical', fontFamily: 'var(--font-sans)',
        }}
      />
      <GlowButton size="sm" onClick={handleSubmit}>Submit</GlowButton>
    </div>
  );
}

// ─── TicketList ──────────────────────────────────

interface Ticket {
  id: string; subject: string; status: 'open' | 'in_progress' | 'closed'; created: string;
}

export function TicketList({ tickets }: { tickets: Ticket[] }) {
  const statusColors = { open: 'var(--warning)', in_progress: 'var(--accent)', closed: 'var(--success)' };
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>My Tickets</h3>
      {tickets.length === 0 ? (
        <p className="text-sm" style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: 20 }}>No tickets yet</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {tickets.map((t) => (
            <div key={t.id} className="glass-subtle" style={{
              padding: '10px 14px', borderRadius: 'var(--radius-sm)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <span className="font-medium text-sm">{t.subject}</span>
                <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block' }}>#{t.id} · {t.created}</span>
              </div>
              <span style={{
                padding: '3px 8px', borderRadius: 4, fontSize: '0.6rem', fontWeight: 700,
                color: statusColors[t.status], background: `${statusColors[t.status]}15`,
                textTransform: 'capitalize',
              }}>
                {t.status.replace('_', ' ')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── LiveChat ──────────────────────────────────

export function LiveChat() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<{ from: 'user' | 'agent'; text: string }[]>([
    { from: 'agent', text: "Hi! I'm VisionX Support. How can I help you today?" },
  ]);

  const send = () => {
    if (!message.trim()) return;
    setMessages((m) => [...m, { from: 'user', text: message }]);
    setMessage('');
    setTimeout(() => {
      setMessages((m) => [...m, { from: 'agent', text: "Thanks for your message! A support agent will be with you shortly." }]);
    }, 1000);
  };

  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>💬 Live Chat</h3>
      <div style={{
        height: 200, overflowY: 'auto', padding: 12,
        background: 'var(--surface)', borderRadius: 'var(--radius-sm)',
        marginBottom: 8, display: 'flex', flexDirection: 'column', gap: 8,
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.from === 'user' ? 'flex-end' : 'flex-start',
            background: m.from === 'user' ? 'var(--accent)' : 'rgba(255,255,255,0.05)',
            color: m.from === 'user' ? '#fff' : 'var(--text-primary)',
            padding: '8px 12px', borderRadius: 12, maxWidth: '75%', fontSize: '0.8rem',
          }}>
            {m.text}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input value={message} onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Type a message..."
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-sm)',
            background: 'var(--surface)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none',
            fontFamily: 'var(--font-sans)',
          }}
        />
        <GlowButton size="sm" onClick={send}>Send</GlowButton>
      </div>
    </div>
  );
}

// ─── ContextualHelp ──────────────────────────────────

export function ContextualHelp({ text, position = 'top' }: { text: string; position?: 'top' | 'bottom' | 'left' | 'right' }) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span style={{ position: 'relative', display: 'inline-flex' }}>
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        style={{
          width: 18, height: 18, borderRadius: '50%', border: '1px solid var(--border)',
          background: 'var(--surface)', color: 'var(--text-tertiary)',
          fontSize: '0.6rem', cursor: 'help', display: 'flex',
          alignItems: 'center', justifyContent: 'center', fontWeight: 700,
        }}
      >
        ?
      </button>
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            style={{
              position: 'absolute', zIndex: 100,
              [position === 'bottom' ? 'top' : 'bottom']: '100%',
              left: '50%', transform: 'translateX(-50%)',
              marginTop: position === 'bottom' ? 6 : undefined,
              marginBottom: position === 'top' ? 6 : undefined,
              padding: '8px 12px', borderRadius: 8, width: 200,
              background: 'rgba(15,15,25,0.98)', border: '1px solid var(--border)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
              fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5,
            }}
          >
            {text}
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
}
