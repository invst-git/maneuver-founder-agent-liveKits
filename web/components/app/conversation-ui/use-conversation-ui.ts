'use client';

import { useCallback, useMemo, useReducer } from 'react';
import { useDataChannel } from '@livekit/components-react';
import { conversationUiReducer, initialConversationUiState } from './reducer';
import { MANEUVER_UI_TOPIC, isManeuverUiAction } from './types';

const decoder = new TextDecoder();

export function useConversationUi() {
  const [state, dispatch] = useReducer(conversationUiReducer, initialConversationUiState);

  const handleMessage = useCallback((message: { payload: Uint8Array }) => {
    try {
      const parsed = JSON.parse(decoder.decode(message.payload));

      if (isManeuverUiAction(parsed)) {
        dispatch(parsed);
      }
    } catch {
      // Ignore malformed UI events. Voice and room state should continue unaffected.
    }
  }, []);

  useDataChannel(MANEUVER_UI_TOPIC, handleMessage);

  return useMemo(
    () => ({
      state,
      dispatch,
    }),
    [state]
  );
}
