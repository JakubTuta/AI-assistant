import { useCallback, useEffect, useState } from 'react'
import { ListChecks, X } from 'lucide-react'
import { fetchNotes, invokeJob } from '../api'
import type { NotesPanel } from '../api'

/** Shopping and todo lists.
 *
 *  Ticking something off goes through the same `note` job the chat would have
 *  called, so the screen and a sentence do exactly the same thing.
 */
export function Notes() {
  const [data, setData] = useState<NotesPanel | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)

  const load = useCallback(() => {
    fetchNotes().then((result) => {
      setData(result.data)
      setError(result.error)
      setLoaded(true)
    })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const remove = async (list: string, item: string) => {
    setBusy(`${list} ${item}`)
    await invokeJob('note', { action: 'remove', text: item, list_name: list })
    setBusy(null)
    load()
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 px-8">
        <ListChecks size={40} className="text-muted" />
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

  const lists = data?.lists ?? []
  if (lists.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 px-8">
        <ListChecks size={40} className="text-muted" />
        <p className="t-body text-muted">No lists yet.</p>
        <p className="t-small text-muted">Ask for "add milk to my shopping list".</p>
      </div>
    )
  }

  return (
    <div className="scroll-y flex-1 px-4 py-4 flex flex-col gap-4">
      {lists.map((list) => (
        <div key={list.name} className="flex flex-col gap-2">
          <div className="t-small text-muted capitalize px-1">
            {list.name} · {list.count}
          </div>
          {list.items.map((item, index) => (
            <div
              key={`${item}-${index}`}
              className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surface border border-line"
            >
              <span className="t-body flex-1 min-w-0 truncate">{item}</span>
              <button
                onClick={() => remove(list.name, item)}
                disabled={busy === `${list.name} ${item}`}
                aria-label={`Take ${item} off the ${list.name} list`}
                className="shrink-0 w-11 h-11 rounded-full grid place-items-center
                           text-muted hover:text-text active:scale-95 disabled:opacity-40"
              >
                <X size={20} />
              </button>
            </div>
          ))}
          {list.count > list.items.length && (
            <p className="t-small text-muted px-1">
              and {list.count - list.items.length} more
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
