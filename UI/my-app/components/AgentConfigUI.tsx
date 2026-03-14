'use client';

import { AgentConfig } from '@/types/agent-config';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

type Props = {
  config: AgentConfig | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  onChange: (nextConfig: AgentConfig) => void;
  onSave: () => void;
  onStartCall: () => void;
};

export default function AgentConfigUI({
  config,
  loading,
  saving,
  error,
  onChange,
  onSave,
  onStartCall,
}: Props) {
  if (loading || !config) {
    return (
      <Box
        minHeight="100vh"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <Stack spacing={2} alignItems="center">
          <CircularProgress />
          <Typography>Loading agent config...</Typography>
        </Stack>
      </Box>
    );
  }

  const updateAssistantField = (field: keyof AgentConfig['assistant'], value: any) => {
    onChange({
      ...config,
      assistant: {
        ...config.assistant,
        [field]: value,
      },
    });
  };

  const updateAssistantVoiceField = (
    field: keyof AgentConfig['assistant']['voice'],
    value: any
  ) => {
    onChange({
      ...config,
      assistant: {
        ...config.assistant,
        voice: {
          ...config.assistant.voice,
          [field]: value,
        },
      },
    });
  };

  const updateAssistantTool = (toolName: string, value: boolean) => {
    onChange({
      ...config,
      assistant: {
        ...config.assistant,
        tools: {
          ...config.assistant.tools,
          [toolName]: value,
        },
      },
    });
  };

  const updateNurseField = (field: keyof AgentConfig['nurse'], value: any) => {
    onChange({
      ...config,
      nurse: {
        ...config.nurse,
        [field]: value,
      },
    });
  };

  const updateNurseVoiceField = (
    field: keyof AgentConfig['nurse']['voice'],
    value: any
  ) => {
    onChange({
      ...config,
      nurse: {
        ...config.nurse,
        voice: {
          ...config.nurse.voice,
          [field]: value,
        },
      },
    });
  };

  const updateNurseTool = (toolName: string, value: boolean) => {
    onChange({
      ...config,
      nurse: {
        ...config.nurse,
        tools: {
          ...config.nurse.tools,
          [toolName]: value,
        },
      },
    });
  };

  const updateCollectConsentField = (
    field: keyof AgentConfig['collect_consent'],
    value: string
  ) => {
    onChange({
      ...config,
      collect_consent: {
        ...config.collect_consent,
        [field]: value,
      },
    });
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f6f8fb', py: 4 }}>
      <Box sx={{ maxWidth: 1200, mx: 'auto', px: 2 }}>
        <Stack spacing={3}>
          <Box>
            <Typography variant="h4" color='#000' fontWeight={700}>
              Hospital Agent Config
            </Typography>
            <Typography variant="body1" color="text.secondary" mt={1}>
              Edit prompts, persona, voice, and enabled tools before starting the call.
            </Typography>
          </Box>

          {error && <Alert severity="error">{error}</Alert>}

          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Typography variant="h6" fontWeight={700}>
                      Assistant
                    </Typography>

                    <TextField
                      label="Assistant Name"
                      value={config.assistant.name}
                      onChange={(e) => updateAssistantField('name', e.target.value)}
                      fullWidth
                    />

                    <TextField
                      label="Assistant Greeting"
                      value={config.assistant.greeting}
                      onChange={(e) => updateAssistantField('greeting', e.target.value)}
                      fullWidth
                      multiline
                      minRows={2}
                    />

                    <TextField
                      label="Assistant Instructions"
                      value={config.assistant.instructions}
                      onChange={(e) => updateAssistantField('instructions', e.target.value)}
                      fullWidth
                      multiline
                      minRows={6}
                    />

                    <Divider />

                    <Typography variant="subtitle1" fontWeight={600}>
                      Voice
                    </Typography>

                    <TextField
                      label="Voice Model"
                      value={config.assistant.voice.model}
                      onChange={(e) => updateAssistantVoiceField('model', e.target.value)}
                      fullWidth
                    />

                    <TextField
                      label="Voice ID"
                      value={config.assistant.voice.voice}
                      onChange={(e) => updateAssistantVoiceField('voice', e.target.value)}
                      fullWidth
                    />

                    <TextField
                      label="Speed"
                      type="number"
                      inputProps={{ step: 0.05 }}
                      value={config.assistant.voice.speed}
                      onChange={(e) =>
                        updateAssistantVoiceField('speed', Number(e.target.value))
                      }
                      fullWidth
                    />

                    <Divider />

                    <Typography variant="subtitle1" fontWeight={600}>
                      Tools
                    </Typography>

                    {Object.entries(config.assistant.tools).map(([toolName, enabled]) => (
                      <FormControl key={toolName} fullWidth>
                        <InputLabel>{toolName}</InputLabel>
                        <Select
                          label={toolName}
                          value={enabled ? 'true' : 'false'}
                          onChange={(e) =>
                            updateAssistantTool(toolName, e.target.value === 'true')
                          }
                        >
                          <MenuItem value="true">true</MenuItem>
                          <MenuItem value="false">false</MenuItem>
                        </Select>
                      </FormControl>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Stack spacing={3}>
                <Card>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6" fontWeight={700}>
                        Nurse
                      </Typography>

                      <TextField
                        label="Nurse Name"
                        value={config.nurse.name}
                        onChange={(e) => updateNurseField('name', e.target.value)}
                        fullWidth
                      />

                      <TextField
                        label="Nurse Greeting"
                        value={config.nurse.greeting}
                        onChange={(e) => updateNurseField('greeting', e.target.value)}
                        fullWidth
                        multiline
                        minRows={2}
                      />

                      <TextField
                        label="Nurse Instructions"
                        value={config.nurse.instructions}
                        onChange={(e) => updateNurseField('instructions', e.target.value)}
                        fullWidth
                        multiline
                        minRows={6}
                      />

                      <Divider />

                      <Typography variant="subtitle1" fontWeight={600}>
                        Voice
                      </Typography>

                      <TextField
                        label="Voice Model"
                        value={config.nurse.voice.model}
                        onChange={(e) => updateNurseVoiceField('model', e.target.value)}
                        fullWidth
                      />

                      <TextField
                        label="Voice ID"
                        value={config.nurse.voice.voice}
                        onChange={(e) => updateNurseVoiceField('voice', e.target.value)}
                        fullWidth
                      />

                      <TextField
                        label="Speed"
                        type="number"
                        inputProps={{ step: 0.05 }}
                        value={config.nurse.voice.speed}
                        onChange={(e) =>
                          updateNurseVoiceField('speed', Number(e.target.value))
                        }
                        fullWidth
                      />

                      <Divider />

                      <Typography variant="subtitle1" fontWeight={600}>
                        Tools
                      </Typography>

                      {Object.entries(config.nurse.tools).map(([toolName, enabled]) => (
                        <FormControl key={toolName} fullWidth>
                          <InputLabel>{toolName}</InputLabel>
                          <Select
                            label={toolName}
                            value={enabled ? 'true' : 'false'}
                            onChange={(e) =>
                              updateNurseTool(toolName, e.target.value === 'true')
                            }
                          >
                            <MenuItem value="true">true</MenuItem>
                            <MenuItem value="false">false</MenuItem>
                          </Select>
                        </FormControl>
                      ))}
                    </Stack>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6" fontWeight={700}>
                        Collect Consent
                      </Typography>

                      <TextField
                        label="Consent Instructions"
                        value={config.collect_consent.instructions}
                        onChange={(e) =>
                          updateCollectConsentField('instructions', e.target.value)
                        }
                        fullWidth
                        multiline
                        minRows={3}
                      />

                      <TextField
                        label="Consent Greeting"
                        value={config.collect_consent.greeting}
                        onChange={(e) =>
                          updateCollectConsentField('greeting', e.target.value)
                        }
                        fullWidth
                        multiline
                        minRows={3}
                      />
                    </Stack>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent>
                    <Stack spacing={2}>
                      <Typography variant="h6" fontWeight={700}>
                        Session Opening
                      </Typography>

                      <TextField
                        label="Session Opening Instruction"
                        value={config.session_opening_instruction}
                        onChange={(e) =>
                          onChange({
                            ...config,
                            session_opening_instruction: e.target.value,
                          })
                        }
                        fullWidth
                        multiline
                        minRows={3}
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Stack>
            </Grid>
          </Grid>

          <Stack direction="row" spacing={2} justifyContent="flex-end">
            <Button variant="outlined" onClick={onSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save config'}
            </Button>

            <Button variant="contained" onClick={onStartCall}>
              Start call
            </Button>
          </Stack>
        </Stack>
      </Box>
    </Box>
  );
}