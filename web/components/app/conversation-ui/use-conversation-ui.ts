'use client';

import { useCallback, useMemo, useReducer } from 'react';
import { useDataChannel } from '@livekit/components-react';
import { conversationUiReducer, initialConversationUiState } from './reducer';
import {
  MANEUVER_UI_INPUT_TOPIC,
  MANEUVER_UI_TOPIC,
  detectVisualActionFromText,
  isManeuverUiAction,
  type LeadField,
  type ManeuverUiInputActionName,
} from './types';

const decoder = new TextDecoder();
const encoder = new TextEncoder();

function makeEventId(prefix: string) {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${prefix}-${crypto.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

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

  const { send } = useDataChannel(MANEUVER_UI_TOPIC, handleMessage);

  const publishLeadInput = useCallback(
    async (action: ManeuverUiInputActionName, field: LeadField, value: string) => {
      const trimmedValue = value.trim();
      if (!trimmedValue) {
        return;
      }

      const status = action === 'confirm_lead_field' ? 'confirmed' : 'corrected';
      dispatch({
        version: 1,
        id: makeEventId('local-lead'),
        action: 'update_lead_field',
        payload: {
          field,
          value: trimmedValue,
          status,
        },
        created_at: new Date().toISOString(),
      });

      await send(
        encoder.encode(
          JSON.stringify({
            version: 1,
            id: makeEventId('ui-input'),
            action,
            payload: {
              field,
              value: trimmedValue,
            },
            created_at: new Date().toISOString(),
          })
        ),
        {
          reliable: true,
          topic: MANEUVER_UI_INPUT_TOPIC,
        }
      );
    },
    [send]
  );

  const confirmLeadField = useCallback(
    async (field: LeadField, value: string) => {
      await publishLeadInput('confirm_lead_field', field, value);
    },
    [publishLeadInput]
  );

  const correctLeadField = useCallback(
    async (field: LeadField, value: string) => {
      await publishLeadInput('correct_lead_field', field, value);
    },
    [publishLeadInput]
  );

  const showVisualForUserText = useCallback((text: string) => {
    const visualAction = detectVisualActionFromText(text);
    if (!visualAction) {
      return false;
    }

    dispatch({
      version: 1,
      id: makeEventId('local-visual'),
      action: visualAction.action,
      payload: visualAction.payload,
      created_at: new Date().toISOString(),
    });

    return true;
  }, []);

  return useMemo(
    () => ({
      state,
      dispatch,
      confirmLeadField,
      correctLeadField,
      showVisualForUserText,
    }),
    [confirmLeadField, correctLeadField, showVisualForUserText, state]
  );
}
