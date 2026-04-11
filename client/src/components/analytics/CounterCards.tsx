/**
 * VisionX — CounterCards Component
 * Object count stat cards with animated numbers
 */

import { motion } from 'framer-motion';

interface CounterCard {
  label: string;
  value: string | number;
  change?: string;
  icon: string;
  color: string;
}

interface CounterCardsProps {
  cards: CounterCard[];
}

export function CounterCards({ cards }: CounterCardsProps) {
  return (
    <div className="grid grid-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08 }}
          className="glass-card stat-card"
        >
          <div className="stat-card__icon" style={{ color: card.color }}>{card.icon}</div>
          <div className="stat-card__info">
            <span className="stat-card__value">{card.value}</span>
            <span className="stat-card__label">{card.label}</span>
          </div>
          {card.change && (
            <span className="badge badge-success" style={{ marginLeft: 'auto', fontSize: '0.6rem' }}>
              {card.change}
            </span>
          )}
        </motion.div>
      ))}
    </div>
  );
}
