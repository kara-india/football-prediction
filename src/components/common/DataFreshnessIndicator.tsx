import DataFreshnessBadge, { DataFreshnessBadgeProps } from '../ui/terminal/DataFreshnessBadge'

export type DataFreshnessIndicatorProps = DataFreshnessBadgeProps

export default function DataFreshnessIndicator(props: DataFreshnessIndicatorProps) {
  return <DataFreshnessBadge {...props} />
}
