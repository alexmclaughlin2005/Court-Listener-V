/**
 * TreatmentBadge - Visual indicator for citation risk status
 *
 * Displays citation risk level with appropriate color coding:
 * - Red (Negative): Overruled, Reversed, Questioned, etc.
 * - Green (Positive): Affirmed, Followed, etc.
 * - Gray (Neutral): Distinguished, Cited, etc.
 */
import React from 'react';
import { TreatmentType, Severity, Treatment } from '../lib/api';

interface TreatmentBadgeProps {
  treatment: Treatment | TreatmentSummary | null;
  size?: 'sm' | 'md' | 'lg';
  showConfidence?: boolean;
  showIcon?: boolean;
  className?: string;
}

interface TreatmentSummary {
  treatment_type: TreatmentType;
  severity: Severity;
  confidence: number;
}

const TREATMENT_CONFIG: Record<TreatmentType, {
  label: string;
  icon: string;
  description: string;
}> = {
  OVERRULED: {
    label: 'Overruled',
    icon: '⛔',
    description: 'This case has been overruled and is no longer good law'
  },
  REVERSED: {
    label: 'Reversed',
    icon: '🔴',
    description: 'This case was reversed on appeal'
  },
  VACATED: {
    label: 'Vacated',
    icon: '⭕',
    description: 'This decision was vacated'
  },
  ABROGATED: {
    label: 'Abrogated',
    icon: '❌',
    description: 'This case has been abrogated'
  },
  SUPERSEDED: {
    label: 'Superseded',
    icon: '🚫',
    description: 'This case has been superseded by subsequent authority'
  },
  AFFIRMED: {
    label: 'Affirmed',
    icon: '✅',
    description: 'This case was affirmed on appeal'
  },
  FOLLOWED: {
    label: 'Followed',
    icon: '🟢',
    description: 'This case has been followed by other courts'
  },
  DISTINGUISHED: {
    label: 'Distinguished',
    icon: '🔵',
    description: 'This case has been distinguished from other cases'
  },
  QUESTIONED: {
    label: 'Questioned',
    icon: '🟡',
    description: 'The validity of this case has been questioned'
  },
  CRITICIZED: {
    label: 'Criticized',
    icon: '🟠',
    description: 'This case has been criticized'
  },
  CITED: {
    label: 'Cited',
    icon: '📄',
    description: 'This case has been cited'
  },
  UNKNOWN: {
    label: 'Unknown',
    icon: '❓',
    description: 'Citation risk status unknown'
  }
};

const SEVERITY_COLORS: Record<Severity, {
  bg: string;
  text: string;
  border: string;
  hover: string;
}> = {
  NEGATIVE: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-200',
    hover: 'hover:bg-red-100'
  },
  POSITIVE: {
    bg: 'bg-green-50',
    text: 'text-green-700',
    border: 'border-green-200',
    hover: 'hover:bg-green-100'
  },
  NEUTRAL: {
    bg: 'bg-gray-50',
    text: 'text-gray-700',
    border: 'border-gray-200',
    hover: 'hover:bg-gray-100'
  },
  UNKNOWN: {
    bg: 'bg-gray-50',
    text: 'text-gray-500',
    border: 'border-gray-200',
    hover: 'hover:bg-gray-100'
  }
};

const SIZE_CLASSES = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-3 py-1',
  lg: 'text-base px-4 py-2'
};

export const TreatmentBadge: React.FC<TreatmentBadgeProps> = ({
  treatment,
  size = 'md',
  showConfidence = false,
  showIcon = true,
  className = ''
}) => {
  if (!treatment) {
    return null;
  }

  // Handle both Treatment and TreatmentSummary types
  const treatmentType = 'type' in treatment ? treatment.type : treatment.treatment_type;
  const severity = treatment.severity;
  const confidence = treatment.confidence;

  const config = TREATMENT_CONFIG[treatmentType];
  const colors = SEVERITY_COLORS[severity];

  const confidencePercent = Math.round(confidence * 100);

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-md font-medium border
        ${colors.bg} ${colors.text} ${colors.border} ${colors.hover}
        ${SIZE_CLASSES[size]}
        ${className}
        transition-colors duration-200
      `}
      title={`${config.description}${showConfidence ? ` (${confidencePercent}% confidence)` : ''}`}
    >
      {showIcon && <span className="text-base leading-none">{config.icon}</span>}
      <span>{config.label}</span>
      {showConfidence && (
        <span className="opacity-70 text-xs">
          ({confidencePercent}%)
        </span>
      )}
    </span>
  );
};

export default TreatmentBadge;
