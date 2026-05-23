import {
  type ConversationUiState,
  type ManeuverUiAction,
  isLeadField,
  normalizeServiceId,
} from './types';

const MAX_SEEN_EVENTS = 30;

export const initialConversationUiState: ConversationUiState = {
  mode: 'default',
  leadFields: {},
  seenEventIds: [],
};

function rememberEvent(state: ConversationUiState, action: ManeuverUiAction) {
  return {
    seenEventIds: [...state.seenEventIds, action.id].slice(-MAX_SEEN_EVENTS),
    lastUpdatedAt: action.created_at,
  };
}

export function conversationUiReducer(
  state: ConversationUiState,
  action: ManeuverUiAction
): ConversationUiState {
  if (state.seenEventIds.includes(action.id)) {
    return state;
  }

  const eventState = rememberEvent(state, action);

  switch (action.action) {
    case 'show_services_slide':
      return {
        ...state,
        ...eventState,
        mode: 'services',
        selectedServiceId: undefined,
      };

    case 'show_service_detail': {
      const selectedServiceId = normalizeServiceId(
        action.payload?.service_id ?? action.payload?.service_name ?? action.payload?.name
      );

      if (!selectedServiceId) {
        return {
          ...state,
          ...eventState,
        };
      }

      return {
        ...state,
        ...eventState,
        mode: 'service_detail',
        selectedServiceId,
      };
    }

    case 'show_process_diagram':
      return {
        ...state,
        ...eventState,
        mode: 'process',
        selectedServiceId: undefined,
      };

    case 'show_default_view':
      return {
        ...state,
        ...eventState,
        mode: 'default',
        selectedServiceId: undefined,
      };

    case 'update_lead_field': {
      const field = action.payload?.field;
      const value = action.payload?.value;

      if (!isLeadField(field) || typeof value !== 'string' || !value.trim()) {
        return {
          ...state,
          ...eventState,
        };
      }

      return {
        ...state,
        ...eventState,
        leadFields: {
          ...state.leadFields,
          [field]: value.trim(),
        },
      };
    }
  }
}
