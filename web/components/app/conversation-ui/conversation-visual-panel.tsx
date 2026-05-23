'use client';

import type { ComponentType } from 'react';
import {
  AppWindow,
  BrainCircuit,
  Building2,
  Cable,
  CalendarDays,
  CheckCircle2,
  CircleDot,
  GitBranch,
  PhoneCall,
  UserRound,
  Workflow,
} from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { cn } from '@/lib/shadcn/utils';
import {
  LEAD_FIELDS,
  PROCESS_STEPS,
  SERVICES,
  type ConversationUiState,
  type LeadField,
  type ServiceId,
} from './types';

interface ConversationVisualPanelProps {
  state: ConversationUiState;
  className?: string;
}

const serviceIconById = {
  intelligent_workflows: Workflow,
  voice_ai: PhoneCall,
  self_learning_ai_agents: BrainCircuit,
  bespoke_applications: AppWindow,
  systems_integration: Cable,
} satisfies Record<ServiceId, ComponentType<{ className?: string }>>;

const serviceAccentById = {
  intelligent_workflows: 'border-chart-1/40 bg-chart-1/10 text-chart-1',
  voice_ai: 'border-chart-2/40 bg-chart-2/10 text-chart-2',
  self_learning_ai_agents: 'border-chart-3/40 bg-chart-3/10 text-chart-3',
  bespoke_applications: 'border-chart-4/40 bg-chart-4/10 text-chart-4',
  systems_integration: 'border-chart-5/40 bg-chart-5/10 text-chart-5',
} satisfies Record<ServiceId, string>;

const priorityLeadFields: LeadField[] = ['name', 'company', 'problem', 'timeline'];

function SectionTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div className="space-y-1">
      <p className="text-muted-foreground text-[11px] font-semibold uppercase">
        {eyebrow}
      </p>
      <h2 className="text-foreground text-xl leading-tight font-semibold md:text-2xl">{title}</h2>
    </div>
  );
}

function DefaultStage({ leadFields }: { leadFields: ConversationUiState['leadFields'] }) {
  const capturedCount = Object.values(leadFields).filter(Boolean).length;
  const metrics = [
    { label: 'Services', value: SERVICES.length },
    { label: 'Process', value: PROCESS_STEPS.length },
    { label: 'Discovery', value: capturedCount },
  ];

  return (
    <motion.div
      key="default"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="flex h-full flex-col justify-between gap-5"
    >
      <div className="space-y-4">
        <SectionTitle eyebrow="Maneuver" title="Founder-led AI systems for SMB operations" />
        <p className="text-muted-foreground max-w-xl text-sm leading-6">
          Fortune 500 AI thinking, built around practical workflows, real integrations, and
          measurable business impact.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {metrics.map((metric) => (
          <div key={metric.label} className="border-border/70 rounded-md border p-3">
            <p className="text-muted-foreground text-[11px] font-medium">{metric.label}</p>
            <p className="text-foreground pt-1 text-lg font-semibold">
              {metric.value}
            </p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function ServicesStage() {
  return (
    <motion.div
      key="services"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="space-y-5"
    >
      <SectionTitle eyebrow="Services" title="Practical AI systems, not demos" />
      <div className="grid gap-2 sm:grid-cols-2">
        {SERVICES.map((service) => {
          const Icon = serviceIconById[service.id];

          return (
            <motion.div
              layout
              key={service.id}
              className={cn(
                'border-border/70 rounded-md border bg-background/70 p-3',
                serviceAccentById[service.id]
              )}
            >
              <div className="flex items-start gap-3">
                <Icon className="mt-0.5 size-4 shrink-0" />
                <div className="min-w-0 space-y-1">
                  <h3 className="text-foreground text-sm leading-5 font-semibold">{service.name}</h3>
                  <p className="text-muted-foreground text-xs leading-5">{service.short}</p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}

function ServiceDetailStage({ selectedServiceId }: { selectedServiceId?: ServiceId }) {
  const service = SERVICES.find((item) => item.id === selectedServiceId) ?? SERVICES[0];
  const Icon = serviceIconById[service.id];

  return (
    <motion.div
      key={`service-${service.id}`}
      initial={{ opacity: 0, scale: 0.98, y: 12 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98, y: -8 }}
      className="space-y-5"
    >
      <div className={cn('w-fit rounded-md border p-3', serviceAccentById[service.id])}>
        <Icon className="size-6" />
      </div>
      <SectionTitle eyebrow="Service detail" title={service.name} />
      <p className="text-muted-foreground text-sm leading-6">{service.detail}</p>

      <div className="border-border/70 rounded-md border p-4">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="text-chart-2 mt-0.5 size-4 shrink-0" />
          <p className="text-foreground text-sm leading-6">{service.short}</p>
        </div>
      </div>
    </motion.div>
  );
}

function ProcessStage() {
  return (
    <motion.div
      key="process"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="space-y-5"
    >
      <SectionTitle eyebrow="Process" title="Understand, build, evolve" />
      <div className="space-y-3">
        {PROCESS_STEPS.map((step, index) => (
          <div key={step.id} className="grid grid-cols-[32px_1fr] gap-3">
            <div className="flex flex-col items-center">
              <div className="border-chart-2/40 bg-chart-2/10 text-chart-2 grid size-8 place-items-center rounded-full border text-sm font-semibold">
                {index + 1}
              </div>
              {index < PROCESS_STEPS.length - 1 && <div className="bg-border mt-2 h-10 w-px" />}
            </div>
            <div className="border-border/70 rounded-md border p-3">
              <h3 className="text-foreground text-sm font-semibold">{step.title}</h3>
              <p className="text-muted-foreground pt-1 text-xs leading-5">{step.body}</p>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function VisualStage({ state }: { state: ConversationUiState }) {
  return (
    <div className="min-h-[260px] flex-1 overflow-hidden p-4 md:p-5">
      <AnimatePresence mode="wait">
        {state.mode === 'default' && <DefaultStage leadFields={state.leadFields} />}
        {state.mode === 'services' && <ServicesStage />}
        {state.mode === 'service_detail' && (
          <ServiceDetailStage selectedServiceId={state.selectedServiceId} />
        )}
        {state.mode === 'process' && <ProcessStage />}
      </AnimatePresence>
    </div>
  );
}

function LeadIcon({ field }: { field: LeadField }) {
  if (field === 'name') {
    return <UserRound className="size-3.5" />;
  }

  if (field === 'company') {
    return <Building2 className="size-3.5" />;
  }

  if (field === 'timeline') {
    return <CalendarDays className="size-3.5" />;
  }

  return <CircleDot className="size-3.5" />;
}

function DiscoveryPanel({ leadFields }: { leadFields: ConversationUiState['leadFields'] }) {
  const orderedFields = [
    ...priorityLeadFields,
    ...LEAD_FIELDS.map((field) => field.id).filter((field) => !priorityLeadFields.includes(field)),
  ];

  return (
    <div className="border-border/70 min-h-0 border-t p-4 md:p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <GitBranch className="text-chart-2 size-4" />
          <h2 className="text-foreground text-sm font-semibold">Discovery</h2>
        </div>
        <p className="text-muted-foreground text-xs font-medium">
          {Object.values(leadFields).filter(Boolean).length} captured
        </p>
      </div>

      <div className="max-h-[190px] space-y-2 overflow-y-auto pr-1 md:max-h-[260px]">
        {orderedFields.map((fieldId) => {
          const field = LEAD_FIELDS.find((item) => item.id === fieldId);
          if (!field) {
            return null;
          }

          const value = leadFields[field.id];

          return (
            <div
              key={field.id}
              className={cn(
                'grid grid-cols-[18px_minmax(82px,0.45fr)_minmax(0,1fr)] items-start gap-2 rounded-md border px-2.5 py-2',
                value
                  ? 'border-chart-2/35 bg-chart-2/10'
                  : 'border-border/60 bg-muted/20 text-muted-foreground'
              )}
            >
              <div className={cn('pt-0.5', value ? 'text-chart-2' : 'text-muted-foreground')}>
                <LeadIcon field={field.id} />
              </div>
              <p className="text-[11px] leading-5 font-medium">{field.label}</p>
              <p
                className={cn(
                  'min-w-0 text-xs leading-5 break-words',
                  value ? 'text-foreground font-medium' : 'text-muted-foreground'
                )}
              >
                {value || 'Pending'}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ConversationVisualPanel({ state, className }: ConversationVisualPanelProps) {
  return (
    <aside
      className={cn(
        'bg-background/95 relative z-40 flex h-full min-h-0 flex-col overflow-hidden border-border/70',
        className
      )}
    >
      <VisualStage state={state} />
      <DiscoveryPanel leadFields={state.leadFields} />
    </aside>
  );
}
