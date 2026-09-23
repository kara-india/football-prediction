import React from 'react'

export interface TerminalCardProps {
  title?: React.ReactNode
  subtitle?: React.ReactNode
  badge?: React.ReactNode
  actions?: React.ReactNode
  children: React.ReactNode
  className?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
  headerBorder?: boolean
}

export default function TerminalCard({
  title,
  subtitle,
  badge,
  actions,
  children,
  className = '',
  padding = 'md',
  headerBorder = true,
}: TerminalCardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4 sm:p-5',
    lg: 'p-6 sm:p-7',
  }[padding]

  const hasHeader = Boolean(title || subtitle || badge || actions)

  return (
    <div
      className={`bg-[#0F172A] border border-[#1E293B] hover:border-[#334155] rounded-xl transition-colors duration-150 text-[#F8FAFC] shadow-sm ${className}`}
    >
      {hasHeader && (
        <div
          className={`flex items-center justify-between gap-3 px-4 sm:px-5 py-3 ${
            headerBorder ? 'border-b border-[#1E293B]' : ''
          }`}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            {badge && <div className="shrink-0">{badge}</div>}
            <div className="min-w-0">
              {title && (
                <div className="text-xs sm:text-sm font-semibold tracking-tight text-[#F8FAFC] truncate">
                  {title}
                </div>
              )}
              {subtitle && (
                <div className="text-[11px] font-mono text-[#94A3B8] truncate mt-0.5">
                  {subtitle}
                </div>
              )}
            </div>
          </div>
          {actions && <div className="shrink-0 flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className={paddingClasses}>{children}</div>
    </div>
  )
}
