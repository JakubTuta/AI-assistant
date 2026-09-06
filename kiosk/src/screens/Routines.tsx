import { useEffect, useState } from 'react'
import { Repeat } from 'lucide-react'
import { fetchRoutines } from '../api'
import type { RoutinesPanel } from '../api'

/** The routines you have, and what each one does.
 *
 *  Read-only on purpose. Every other screen acts by calling a job, but a
 *  routine returns steps for the model to carry out — a Run button here would
 *  show the instructions and do none of them. The Briefing tile runs one the
 *  right way, through the chat; this screen is how you find out what is in it.
 */
export function Routines() {
  const [data, setData] = useState<RoutinesPanel | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    fetchRoutines().then((result) => {
      setData(result.data)
      setError(result.error)
      setLoaded(true)
    })
  }, [])

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 px-8">
        <Repeat size={40} className="text-muted" />
        <p className="t-body text-muted">{error}</p>
      </div>
    )
  }

  if (!loaded) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="t-body text-muted">Checking…</p>
      </div>
    )
  }

  const routines = data?.routines ?? []
  if (routines.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 px-8">
        <Repeat size={40} className="text-muted" />
        <p className="t-body text-muted">No routines yet.</p>
        <p className="t-small text-muted">
          Ask for "save a routine called good night that turns off the lights".
        </p>
      </div>
    )
  }

  return (
    <div className="scroll-y flex-1 px-4 py-4 flex flex-col gap-3">
      {routines.map((item) => (
        <div
          key={item.name}
          className="px-4 py-3 rounded-xl bg-surface border border-line flex flex-col gap-1"
        >
          <span className="t-body capitalize">{item.name}</span>
          <span className="t-small text-muted">{item.steps}</span>
        </div>
      ))}
      <p className="t-small text-muted px-1">Run one by asking for it by name.</p>
    </div>
  )
}
