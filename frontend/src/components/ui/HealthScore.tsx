interface HealthScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const SIZE_CONFIG = {
  sm: { svg: 64, stroke: 6, radius: 26, fontSize: 'text-lg' },
  md: { svg: 96, stroke: 8, radius: 40, fontSize: 'text-2xl' },
  lg: { svg: 128, stroke: 8, radius: 56, fontSize: 'text-3xl' },
};

function getScoreColor(score: number): string {
  if (score >= 85) return 'text-emerald-500';
  if (score >= 70) return 'text-amber-500';
  return 'text-red-500';
}

function getScoreLabel(score: number): string {
  if (score >= 85) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 50) return 'Fair';
  return 'Poor';
}

export function HealthScore({ score, size = 'md', showLabel = true }: HealthScoreProps) {
  const config = SIZE_CONFIG[size];
  const circumference = 2 * Math.PI * config.radius;
  const offset = circumference * (1 - score / 100);
  const color = getScoreColor(score);
  const center = config.svg / 2;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: config.svg, height: config.svg }}>
        <svg
          width={config.svg}
          height={config.svg}
          className="transform -rotate-90"
          viewBox={`0 0 ${config.svg} ${config.svg}`}
        >
          <circle
            cx={center}
            cy={center}
            r={config.radius}
            stroke="currentColor"
            strokeWidth={config.stroke}
            fill="none"
            className="text-muted/20"
          />
          <circle
            cx={center}
            cy={center}
            r={config.radius}
            stroke="currentColor"
            strokeWidth={config.stroke}
            fill="none"
            className={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.6s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`${config.fontSize} font-semibold text-foreground`}>
            {score}%
          </span>
        </div>
      </div>
      {showLabel && (
        <span className={`text-xs font-medium ${color}`}>
          {getScoreLabel(score)}
        </span>
      )}
    </div>
  );
}
