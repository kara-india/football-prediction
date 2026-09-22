import MetricsSummary from '../../components/analytics/MetricsSummary'
import CalibrationChart from '../../components/analytics/CalibrationChart'
import PLChart from '../../components/analytics/PLChart'

export default function Analytics() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Learning Dashboard</h1>
      <MetricsSummary />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CalibrationChart />
        <PLChart />
      </div>
    </div>
  )
}
