import LiveMatchSection from '../components/dashboard/LiveMatchSection'
import UpcomingMatchSection from '../components/dashboard/UpcomingMatchSection'

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <LiveMatchSection />
      <UpcomingMatchSection />
    </div>
  )
}
