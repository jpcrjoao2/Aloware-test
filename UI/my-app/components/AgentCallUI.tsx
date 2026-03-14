'use client';

import {
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from '@mui/material';
import {
  BarVisualizer,
  ControlBar,
  RoomAudioRenderer,
  useAgent,
  useVoiceAssistant
} from '@livekit/components-react';
import { useEffect } from 'react';

type Props = {
  onEndCall: () => void;
};

function AgentVisualizer({ onEndCall }: { onEndCall: () => void }) {
  const agent = useAgent();
  const { state, audioTrack } = useVoiceAssistant();

  useEffect(() => {
    if (agent.state === 'disconnected') {
      onEndCall();
    }
  }, [agent.state, onEndCall]);

  console.log({state}, {audioTrack})

  return (
    <Card sx={{ width: '100%', maxWidth: 800 }}>
      <CardContent>
        <Stack spacing={3}>
          <Box>
            <Typography variant="h5" fontWeight={700}>
              Live Call
            </Typography>
            <Typography variant="body1" color="text.secondary" mt={1}>
              Agent state: {agent.state || 'unknown'}
            </Typography>
          </Box>

          <Box
            sx={{
              minHeight: 180,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 2,
              p: 2,
            }}
          >
            {agent.canListen ? (
              <BarVisualizer
                track={audioTrack}
                state={state}
                barCount={11}
                options={{ minHeight: 20, maxHeight: 100 }}
              />
            ) : (
              <Typography color="text.secondary">
                Waiting for microphone / agent audio...
              </Typography>
            )}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function AgentCallUI({ onEndCall }: Props) {
  return (
    <Box
      data-lk-theme="default"
      sx={{
        minHeight: '100vh',
        bgcolor: '#f6f8fb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        px: 2,
        py: 4,
      }}
    >
      <Stack spacing={3} alignItems="center" sx={{ width: '100%' }}>
        <AgentVisualizer onEndCall={onEndCall}/>

        <div className="mx-auto inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3">
          <ControlBar
            controls={{
              microphone: true,
              camera: false,
              screenShare: false,
              leave: false,
            }}
          />
        </div>


        <Button color="error" variant="contained" onClick={onEndCall}>
          End call
        </Button>

        <RoomAudioRenderer />
      </Stack>
    </Box>
  );
}