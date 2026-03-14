'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { SessionProvider, useSession } from '@livekit/components-react';
import { TokenSource } from 'livekit-client';
import AgentConfigLobby from '@/components/AgentConfigUI';
import AgentCallView from '@/components/AgentCallUI';
import { AgentConfig } from '@/types/agent-config';

const tokenSource = TokenSource.endpoint('/api/token');

type ViewMode = 'lobby' | 'call';
type InnerAppProps = {
  session: ReturnType<typeof useSession>; 
};

function InnerApp({ session }: InnerAppProps) {

  const [viewMode, setViewMode] = useState<ViewMode>('lobby');
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  console.log(loading)

  const loadConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch('/api/agent-config', {
        method: 'GET',
        cache: 'no-store',
      });

      if (!res.ok) {
        throw new Error('Failed to load config');
      }

      const data = await res.json();
      setConfig(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load agent config.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();

  }, [loadConfig]);

  const handleSave = async () => {
    if (!config) return;

    try {
      setSaving(true);
      setError(null);

      const res = await fetch('/api/agent-config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.error || 'Failed to save config');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to save agent config.');
    } finally {
      setSaving(false);
    }
  };

  const handleStartCall = async () => {
    try {
      setLoading(true)
      setError(null);
      await session.start();
      setViewMode('call');
    } catch (err) {
      console.error(err);
      setError('Failed to start call session.');
    } finally {
      setLoading(false); 
    }
  };

  const handleEndCall = async () => {
    try {
      await session.end();
    } finally {
      setViewMode('lobby');
    }
  };

  if (loading) {
    return (
      <div className="loading-dots min-h-screen w-full flex items-center justify-center">
        {[1, 2, 3].map((dot) => (
          <div
            key={dot}
            className="dot"
            style={{ backgroundColor: "#444", width: "10px", height: "10px" }}
          />
        ))}
      </div>
    );
  }

  if (viewMode === 'call') {
    return <AgentCallView onEndCall={handleEndCall} />;
  }

  return (
    <AgentConfigLobby
      config={config}
      loading={loading}
      saving={saving}
      error={error}
      onChange={setConfig}
      onSave={handleSave}
      onStartCall={handleStartCall}
    />
  );
}

export default function Page() {
  const session = useSession(tokenSource, { agentName: 'Hospital_Agent' });

  return (
    <SessionProvider session={session}>
      <InnerApp session={session}/>
    </SessionProvider>
  );
}