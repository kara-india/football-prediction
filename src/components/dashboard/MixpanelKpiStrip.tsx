'use client'

export default function MixpanelKpiStrip() {
  return (
    <section className="rounded-2xl border border-[#1E293B] bg-[#0F172A] p-5 sm:p-6">
      <div className="flex flex-col gap-2 border-b border-[#1E293B] pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-[#F8FAFC]">Analysis readiness</h2>
          <p className="mt-1 text-xs text-[#94A3B8]">Premier League only · paper decisions only</p>
        </div>
        <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[10px] font-mono text-amber-200">
          Decision engine unavailable
        </span>
      </div>
      <div className="grid gap-3 pt-4 sm:grid-cols-3">
        <div className="rounded-lg border border-[#1E293B] bg-[#0B0F17] p-3">
          <div className="text-[10px] uppercase text-[#64748B]">Fixture source</div>
          <div className="mt-1 text-sm font-semibold text-[#F8FAFC]">football-data.org</div>
          <div className="mt-1 text-[11px] text-[#94A3B8]">Free scores may be delayed</div>
        </div>
        <div className="rounded-lg border border-[#1E293B] bg-[#0B0F17] p-3">
          <div className="text-[10px] uppercase text-[#64748B]">Lineups</div>
          <div className="mt-1 text-sm font-semibold text-[#F8FAFC]">Confirmation required</div>
          <div className="mt-1 text-[11px] text-[#94A3B8]">No predicted XI is used as confirmed</div>
        </div>
        <div className="rounded-lg border border-[#1E293B] bg-[#0B0F17] p-3">
          <div className="text-[10px] uppercase text-[#64748B]">Paper ledger</div>
          <div className="mt-1 text-sm font-semibold text-[#F8FAFC]">No decisions yet</div>
          <div className="mt-1 text-[11px] text-[#94A3B8]">No sample results are shown</div>
        </div>
      </div>
    </section>
  )
}
