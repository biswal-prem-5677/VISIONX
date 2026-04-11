/**
 * VisionX — Help Center Page
 * FAQ, support tickets, onboarding, live chat
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { GlowButton } from '../components/ui/GlowButton';

const faqItems = [
  { q: 'How do I connect a camera?', a: 'Go to Settings → Devices → Add Camera. Enter your RTSP URL or select USB webcam from the dropdown. Click "Test Connection" to verify.' },
  { q: 'What AI modules are available?', a: 'VisionX includes: Object Detection, Tracking, Counting, OCR, Face Recognition, Pose Estimation, and Segmentation. Enable them from Settings → AI Modules.' },
  { q: 'How do automation rules work?', a: 'Automation follows an "IF-THEN" pattern. Define a trigger (e.g., "Person count > 5") and actions (e.g., "Send email + Sound alarm"). The system executes automatically.' },
  { q: 'Can I use VisionX offline?', a: 'Yes! Edge AI detection and tracking work fully offline. Cloud features (Face Recognition, OCR) require internet. Your data syncs automatically when you reconnect.' },
  { q: 'What cameras are supported?', a: 'USB Webcams, RTSP streams, IP cameras (HTTP), and video files (MP4/AVI/MKV). Any ONVIF-compatible camera works via RTSP.' },
  { q: 'How do I export my data?', a: 'Go to Account → Privacy → Export Data. You\'ll receive a full JSON export of all your events, settings, and history within 24 hours.' },
];

const guides = [
  { icon: '🚀', title: 'Getting Started', desc: 'Set up your first camera in 5 minutes', tag: 'Beginner' },
  { icon: '⚙️', title: 'AI Module Configuration', desc: 'Fine-tune detection for your environment', tag: 'Intermediate' },
  { icon: '⚡', title: 'Automation Rules', desc: 'Build intelligent "If-Then" automation', tag: 'Intermediate' },
  { icon: '📊', title: 'Analytics Deep Dive', desc: 'Understand your analytics dashboard', tag: 'Beginner' },
  { icon: '🔒', title: 'Security Best Practices', desc: 'Secure your VisionX deployment', tag: 'Advanced' },
  { icon: '🌐', title: 'Multi-Camera Setup', desc: 'Connect and manage multiple cameras', tag: 'Advanced' },
];

export default function HelpCenter() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [ticketSubject, setTicketSubject] = useState('');

  return (
    <div className="help-center">
      {/* Search Bar */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 24 }}>
        <GlassCard style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 20, opacity: 0.5 }}>🔍</span>
            <input
              type="text"
              placeholder="Search help articles, guides, and FAQs..."
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                color: 'var(--text-primary)', fontSize: '1rem', fontFamily: 'var(--font-sans)',
              }}
            />
          </div>
        </GlassCard>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 20 }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Quick Guides */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 16 }}>Quick Guides</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {guides.map((g, i) => (
                  <motion.div
                    key={i}
                    className="glass-subtle"
                    style={{ padding: '16px', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}
                    whileHover={{ scale: 1.02, borderColor: 'var(--accent)' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: 28 }}>{g.icon}</span>
                      <span className={`badge ${g.tag === 'Beginner' ? 'badge-success' : g.tag === 'Intermediate' ? 'badge-accent' : 'badge-warning'}`}
                        style={{ fontSize: '0.6rem' }}>{g.tag}</span>
                    </div>
                    <p className="font-medium text-sm" style={{ marginTop: 8 }}>{g.title}</p>
                    <p className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>{g.desc}</p>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </motion.div>

          {/* FAQ */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 16 }}>Frequently Asked Questions</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {faqItems.map((faq, i) => (
                  <div key={i} className="glass-subtle" style={{
                    borderRadius: 'var(--radius-sm)', overflow: 'hidden',
                  }}>
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      style={{
                        width: '100%', textAlign: 'left', padding: '14px 16px',
                        background: 'transparent', border: 'none', cursor: 'pointer',
                        color: 'var(--text-primary)', fontFamily: 'var(--font-sans)',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      }}
                    >
                      <span className="font-medium text-sm">{faq.q}</span>
                      <span style={{
                        transform: openFaq === i ? 'rotate(180deg)' : 'rotate(0)',
                        transition: 'transform 0.2s', opacity: 0.5,
                      }}>▼</span>
                    </button>
                    <AnimatePresence>
                      {openFaq === i && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          style={{ overflow: 'hidden' }}
                        >
                          <p className="text-sm" style={{
                            padding: '0 16px 14px', color: 'var(--text-secondary)', lineHeight: 1.6,
                          }}>{faq.a}</p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Submit Ticket */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 12 }}>Submit a Ticket</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <input
                  type="text"
                  placeholder="Subject..."
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                    background: 'var(--surface)', border: '1px solid var(--border)',
                    color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', outline: 'none',
                  }}
                />
                <textarea
                  placeholder="Describe your issue..."
                  rows={4}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                    background: 'var(--surface)', border: '1px solid var(--border)',
                    color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', outline: 'none',
                    resize: 'vertical',
                  }}
                />
                <GlowButton style={{ width: '100%' }}>Submit Ticket</GlowButton>
              </div>
            </GlassCard>
          </motion.div>

          {/* Live Chat */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 8 }}>Live Chat</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
                Talk to our support team in real-time
              </p>
              <div className="glass-subtle" style={{
                padding: 16, borderRadius: 'var(--radius-sm)', textAlign: 'center',
              }}>
                <span style={{ fontSize: 32 }}>💬</span>
                <p className="text-sm font-medium" style={{ marginTop: 8 }}>Support Available</p>
                <p className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>
                  Average response: 2 minutes
                </p>
                <GlowButton size="sm" style={{ marginTop: 12 }}>Start Chat</GlowButton>
              </div>
            </GlassCard>
          </motion.div>

          {/* Quick Links */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 12 }}>Quick Links</h3>
              {['📖 Release Notes', '🔑 API Documentation', '🎥 Video Tutorials', '💬 Community Forum'].map((link, i) => (
                <div key={i} className="glass-subtle" style={{
                  padding: '10px 14px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                  marginBottom: 6,
                }}>
                  <span className="text-sm">{link}</span>
                </div>
              ))}
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
