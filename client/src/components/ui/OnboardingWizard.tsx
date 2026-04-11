/**
 * VisionX — Onboarding Wizard
 * Step-by-step setup guide for new users
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { GlowButton } from '../components/ui/GlowButton';

interface Step {
  id: number;
  title: string;
  description: string;
  icon: string;
  content: string;
}

const steps: Step[] = [
  {
    id: 1, title: 'Welcome to VisionX', icon: '🚀',
    description: 'Let\'s set up your AI vision platform in 3 easy steps.',
    content: 'VisionX transforms any camera into an intelligent eye. Detect objects, track movement, count people, and automate responses — all powered by edge AI.',
  },
  {
    id: 2, title: 'Connect Your Camera', icon: '📹',
    description: 'Add your first camera source to start monitoring.',
    content: 'Supports USB webcams, RTSP streams, IP cameras, and video files. Just enter the URL or select from connected devices.',
  },
  {
    id: 3, title: 'Choose AI Modules', icon: '🧠',
    description: 'Select which AI features to enable for your use case.',
    content: 'Enable object detection, tracking, counting, OCR, face recognition, pose estimation, and more. Only enabled modules consume resources.',
  },
  {
    id: 4, title: 'Set Up Automation', icon: '⚡',
    description: 'Create your first "If this, then that" rule.',
    content: 'Define triggers (e.g., "Person count > 5") and actions (e.g., "Send email alert"). VisionX will auto-execute when conditions are met.',
  },
  {
    id: 5, title: 'You\'re All Set!', icon: '🎉',
    description: 'Your VisionX platform is ready to go.',
    content: 'Start monitoring in real-time, review analytics, and fine-tune your settings. Need help? Visit the Help Center anytime.',
  },
];

export function OnboardingWizard({ onComplete }: { onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);

  const step = steps[currentStep];
  const isLast = currentStep === steps.length - 1;
  const isFirst = currentStep === 0;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 10000,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)',
    }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        style={{ width: '100%', maxWidth: 520 }}
      >
        <GlassCard style={{ padding: 0, overflow: 'hidden' }}>
          {/* Progress Bar */}
          <div style={{ height: 3, background: 'var(--surface)' }}>
            <motion.div
              style={{ height: '100%', background: 'var(--accent)' }}
              animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          {/* Step Content */}
          <div style={{ padding: '40px 32px' }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <span style={{ fontSize: 48, display: 'block', marginBottom: 12 }}>{step.icon}</span>
                  <h2 className="text-xl font-bold">{step.title}</h2>
                  <p className="text-sm" style={{ color: 'var(--accent)', marginTop: 4 }}>
                    {step.description}
                  </p>
                </div>
                <p className="text-sm" style={{
                  color: 'var(--text-secondary)', lineHeight: 1.8, textAlign: 'center',
                  maxWidth: 400, margin: '0 auto',
                }}>
                  {step.content}
                </p>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Step Dots */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginBottom: 16 }}>
            {steps.map((_, i) => (
              <div
                key={i}
                style={{
                  width: i === currentStep ? 20 : 6, height: 6, borderRadius: 3,
                  background: i <= currentStep ? 'var(--accent)' : 'var(--surface)',
                  transition: 'all 0.3s',
                }}
              />
            ))}
          </div>

          {/* Actions */}
          <div style={{
            padding: '16px 32px 24px',
            display: 'flex', justifyContent: isFirst ? 'flex-end' : 'space-between',
          }}>
            {!isFirst && (
              <GlowButton variant="ghost" onClick={() => setCurrentStep((s) => s - 1)}>
                ← Back
              </GlowButton>
            )}
            {isLast ? (
              <GlowButton onClick={onComplete}>Get Started 🚀</GlowButton>
            ) : (
              <GlowButton onClick={() => setCurrentStep((s) => s + 1)}>
                Next →
              </GlowButton>
            )}
          </div>
        </GlassCard>

        {/* Skip */}
        <button
          onClick={onComplete}
          style={{
            display: 'block', margin: '16px auto', background: 'none',
            border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer',
            fontSize: '0.8rem', fontFamily: 'var(--font-sans)',
          }}
        >
          Skip onboarding
        </button>
      </motion.div>
    </div>
  );
}
