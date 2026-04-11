/**
 * VisionX — ActionSelector Component
 * Choose action type for automation rules
 */

interface Action {
  id: string;
  label: string;
  icon: string;
  description: string;
}

interface ActionSelectorProps {
  actions: Action[];
  selected: string[];
  onToggle: (id: string) => void;
}

export function ActionSelector({ actions, selected, onToggle }: ActionSelectorProps) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
      {actions.map((action) => {
        const isSelected = selected.includes(action.id);
        return (
          <button
            key={action.id}
            onClick={() => onToggle(action.id)}
            style={{
              padding: '14px 12px', borderRadius: 'var(--radius-sm)',
              background: isSelected ? 'rgba(var(--accent-rgb, 139,92,246), 0.1)' : 'var(--surface)',
              border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
              cursor: 'pointer', textAlign: 'center',
              transition: 'all 0.2s', color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <span style={{ fontSize: 24, display: 'block', marginBottom: 6 }}>{action.icon}</span>
            <span className="font-medium text-sm" style={{ display: 'block' }}>{action.label}</span>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 2, display: 'block' }}>
              {action.description}
            </span>
          </button>
        );
      })}
    </div>
  );
}
