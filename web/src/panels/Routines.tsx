import { useEffect, useState } from 'react';
import { Repeat } from 'lucide-react';
import { fetchPanel } from '../api';
import type { RoutinesPanel } from '../api';
import { CARD, MUTED, Resting } from './ui';

/** The user's named routines and what each one does.
 *
 *  Read-only on purpose. Every other panel acts by calling a job directly, but
 *  a routine returns steps for the model to carry out — running one from a
 *  button would print the instructions and do none of them. Say the name
 *  instead; the point of a routine is that it has a name you can say.
 */
export function Routines() {
  const [data, setData] = useState<RoutinesPanel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetchPanel<RoutinesPanel>('routines').then((result) => {
      setData(result.data);
      setError(result.error);
      setLoaded(true);
    });
  }, []);

  if (!loaded) return <Resting title="…" />;
  if (error) return <Resting icon={<Repeat size={30} />} title={error} />;

  const routines = data?.routines ?? [];
  if (routines.length === 0) {
    return (
      <Resting icon={<Repeat size={32} />} title="No routines yet">
        Ask for one — "save a routine called good night that turns off the lights
        and sets an alarm for seven".
      </Resting>
    );
  }

  return (
    <div className="p-4 space-y-3">
      {routines.map((item) => (
        <div key={item.name} className={`${CARD} p-3`}>
          <div className="text-sm text-gray-900 dark:text-gray-100 capitalize">
            {item.name}
          </div>
          <div className={`text-xs ${MUTED} pt-1`}>{item.steps}</div>
        </div>
      ))}
      <p className={`text-xs ${MUTED} px-1`}>
        Run one by asking for it by name.
      </p>
    </div>
  );
}
