export const MANEUVER_UI_TOPIC = 'maneuver.ui';

export const SERVICES = [
  {
    id: 'intelligent_workflows',
    name: 'Intelligent workflows',
    short:
      'Automation for repetitive operations, approvals, follow-ups, data movement, and internal processes.',
    detail:
      'Practical workflow automation around the way the business already runs, with AI used where it moves speed, accuracy, or throughput.',
  },
  {
    id: 'voice_ai',
    name: 'Voice AI',
    short:
      'Inbound and outbound voice agents for questions, lead qualification, routine calls, and business-system actions.',
    detail:
      'Voice agents that handle the repetitive parts of calls while integrating with the tools the team already depends on.',
  },
  {
    id: 'self_learning_ai_agents',
    name: 'Self-learning AI agents',
    short: 'Agents that reason through repeatable business tasks and improve workflows over time.',
    detail:
      'Task-focused agents for repeatable business work, designed around measurable operating outcomes rather than demos.',
  },
  {
    id: 'bespoke_applications',
    name: 'Bespoke applications',
    short: "Custom AI-enabled software built around the client's workflow.",
    detail:
      'Custom applications shaped around the actual workflow, data, users, and commercial constraints of the business.',
  },
  {
    id: 'systems_integration',
    name: 'Systems integration',
    short: 'Connecting AI workflows with CRMs, booking systems, WhatsApp, spreadsheets, ERPs, and internal tools.',
    detail:
      'Integration work that lets AI systems act inside the operational stack instead of sitting outside it.',
  },
] as const;

export const PROCESS_STEPS = [
  {
    id: 'understand',
    title: 'Understand',
    body: 'Learn the business, workflow, problem, and commercial impact.',
  },
  {
    id: 'design_build',
    title: 'Design and build',
    body: 'Create the AI system around real operations, not abstract demos.',
  },
  {
    id: 'launch_evolve',
    title: 'Launch and evolve',
    body: 'Deploy, measure, improve, and expand.',
  },
] as const;

export const LEAD_FIELDS = [
  { id: 'name', label: 'Name' },
  { id: 'role', label: 'Role' },
  { id: 'company', label: 'Company' },
  { id: 'website', label: 'Website' },
  { id: 'email', label: 'Email' },
  { id: 'phone', label: 'Phone' },
  { id: 'location', label: 'Location' },
  { id: 'industry', label: 'Industry' },
  { id: 'company_size', label: 'Company size' },
  { id: 'problem', label: 'Problem' },
  { id: 'current_workflow', label: 'Current workflow' },
  { id: 'current_tools', label: 'Current tools' },
  { id: 'desired_solution', label: 'Desired solution' },
  { id: 'timeline', label: 'Timeline' },
  { id: 'budget', label: 'Budget' },
  { id: 'decision_maker', label: 'Decision maker' },
  { id: 'success_metric', label: 'Success metric' },
  { id: 'next_step', label: 'Next step' },
] as const;

export type ServiceId = (typeof SERVICES)[number]['id'];
export type LeadField = (typeof LEAD_FIELDS)[number]['id'];

export type VisualMode = 'default' | 'services' | 'service_detail' | 'process';

export type ManeuverUiActionName =
  | 'show_services_slide'
  | 'show_service_detail'
  | 'show_process_diagram'
  | 'show_default_view'
  | 'update_lead_field';

export interface ManeuverUiAction {
  version: 1;
  id: string;
  action: ManeuverUiActionName;
  payload?: Record<string, unknown>;
  created_at?: string;
}

export interface ConversationUiState {
  mode: VisualMode;
  selectedServiceId?: ServiceId;
  leadFields: Partial<Record<LeadField, string>>;
  seenEventIds: string[];
  lastUpdatedAt?: string;
}

const SERVICE_ALIAS_BY_NAME = new Map<string, ServiceId>(
  SERVICES.flatMap((service): Array<[string, ServiceId]> => [
    [service.id, service.id],
    [service.name.toLowerCase(), service.id],
    [service.name.toLowerCase().replace(/-/g, ' '), service.id],
  ])
);

const SERVICE_ALIASES: Record<string, ServiceId> = {
  workflow: 'intelligent_workflows',
  workflows: 'intelligent_workflows',
  'intelligent workflow': 'intelligent_workflows',
  'intelligent workflows': 'intelligent_workflows',
  automation: 'intelligent_workflows',
  voice: 'voice_ai',
  'voice ai': 'voice_ai',
  'voice agent': 'voice_ai',
  'voice agents': 'voice_ai',
  agents: 'self_learning_ai_agents',
  'ai agents': 'self_learning_ai_agents',
  'self learning ai agents': 'self_learning_ai_agents',
  'self-learning ai agents': 'self_learning_ai_agents',
  'bespoke application': 'bespoke_applications',
  'bespoke applications': 'bespoke_applications',
  'custom application': 'bespoke_applications',
  'custom applications': 'bespoke_applications',
  'custom apps': 'bespoke_applications',
  integration: 'systems_integration',
  integrations: 'systems_integration',
  'system integration': 'systems_integration',
  'systems integration': 'systems_integration',
};

export function normalizeServiceId(value: unknown): ServiceId | undefined {
  if (typeof value !== 'string') {
    return undefined;
  }

  const normalized = value.trim().toLowerCase().replace(/_/g, ' ').replace(/\s+/g, ' ');
  const underscoreId = normalized.replace(/\s+/g, '_') as ServiceId;

  if (SERVICES.some((service) => service.id === underscoreId)) {
    return underscoreId;
  }

  return SERVICE_ALIAS_BY_NAME.get(normalized) ?? SERVICE_ALIASES[normalized];
}

export function isLeadField(value: unknown): value is LeadField {
  return typeof value === 'string' && LEAD_FIELDS.some((field) => field.id === value);
}

export function isManeuverUiAction(value: unknown): value is ManeuverUiAction {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const candidate = value as Partial<ManeuverUiAction>;
  const validActionNames: ManeuverUiActionName[] = [
    'show_services_slide',
    'show_service_detail',
    'show_process_diagram',
    'show_default_view',
    'update_lead_field',
  ];

  return (
    candidate.version === 1 &&
    typeof candidate.id === 'string' &&
    validActionNames.includes(candidate.action as ManeuverUiActionName) &&
    (candidate.payload === undefined ||
      (typeof candidate.payload === 'object' && candidate.payload !== null))
  );
}
