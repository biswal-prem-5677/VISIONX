/**
 * VisionX — Cookie Consent Banner
 * GDPR-compliant cookie consent with glassmorphic design
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlowButton } from './GlowButton';

const COOKIE_KEY = 'vx_cookie_consent';

export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem(COOKIE_KEY);
    if (!consent) {
      const timer = setTimeout(() => setVisible(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem(COOKIE_KEY, JSON.stringify({ accepted: true, timestamp: Date.now() }));
    setVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem(COOKIE_KEY, JSON.stringify({ accepted: false, timestamp: Date.now() }));
    setVisible(false);
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: 'spring', damping: 25 }}
          style={{
            position: 'fixed', bottom: 24, left: 24, right: 24,
            maxWidth: 520, margin: '0 auto', zIndex: 9999,
            padding: '20px 24px', borderRadius: 16,
            background: 'rgba(15,15,25,0.95)',
            border: '1px solid var(--border)',
            backdropFilter: 'blur(20px)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          }}
        >
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <span style={{ fontSize: 24, flexShrink: 0 }}>🍪</span>
            <div style={{ flex: 1 }}>
              <p className="font-semibold" style={{ marginBottom: 4 }}>Cookie Preferences</p>
              <p className="text-xs" style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                We use cookies for essential functionality, analytics, and to personalize your experience.
                Your data stays local by default.
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
            <GlowButton variant="ghost" size="sm" onClick={handleDecline}>
              Decline
            </GlowButton>
            <GlowButton size="sm" onClick={handleAccept}>
              Accept All
            </GlowButton>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
