import MatchHeader from '../../../components/match/MatchHeader'
import OddsPanel from '../../../components/match/OddsPanel'
import LiveStatePanel from '../../../components/match/LiveStatePanel'
import ModelPanel from '../../../components/match/ModelPanel'
import MarketTable from '../../../components/match/MarketTable'

export default function MatchIntelligence({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-6">
      <MatchHeader matchId={params.id} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <LiveStatePanel />
        <OddsPanel />
      </div>
      <ModelPanel />
      <MarketTable />
    </div>
  )
}
