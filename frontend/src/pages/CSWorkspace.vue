<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="CS Workspace" />
      </template>
      <template #right-header>
        <Button
          variant="outline"
          :label="__('Start client cycle')"
          iconLeft="plus"
          @click="showCycleDialog = true"
        />
        <Button
          variant="solid"
          :label="__('Schedule meeting')"
          iconLeft="calendar"
          @click="router.push({ name: 'Calendar' })"
        />
      </template>
    </LayoutHeader>

    <main class="flex-1 overflow-y-auto">
      <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-5">
        <section>
          <p class="text-sm text-ink-gray-5">{{ formattedToday }}</p>
          <h1 class="mt-1 text-2xl font-semibold text-ink-gray-9">
            {{ __('Good morning, CS') }}
          </h1>
          <p class="mt-1 text-base text-ink-gray-6">
            {{ __('Here is what needs your attention today.') }}
          </p>
        </section>

        <section class="grid grid-cols-1 gap-3 md:grid-cols-3">
          <button
            v-for="metric in metrics"
            :key="metric.label"
            class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 text-left transition hover:border-outline-gray-4"
            @click="router.push(metric.to)"
          >
            <div class="flex items-center justify-between">
              <span class="text-sm text-ink-gray-6">{{ __(metric.label) }}</span>
              <component :is="metric.icon" class="size-4 text-ink-gray-5" />
            </div>
            <div class="mt-2 text-2xl font-semibold text-ink-gray-9">
              {{ metric.value }}
            </div>
          </button>
        </section>

        <section class="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white">
            <div class="flex items-center justify-between border-b p-4">
              <div>
                <h2 class="font-semibold text-ink-gray-9">
                  {{ __('Today’s agenda') }}
                </h2>
                <p class="mt-1 text-sm text-ink-gray-5">
                  {{ __('Meetings linked to your calendar') }}
                </p>
              </div>
              <Button
                variant="ghost"
                :label="__('Open calendar')"
                @click="router.push({ name: 'Calendar' })"
              />
            </div>
            <div v-if="events.loading" class="p-4 text-sm text-ink-gray-5">
              {{ __('Loading...') }}
            </div>
            <div
              v-else-if="todayEvents.length"
              class="divide-y divide-outline-gray-1"
            >
              <button
                v-for="event in todayEvents"
                :key="event.name"
                class="flex w-full items-center gap-3 p-4 text-left hover:bg-surface-gray-1"
                @click="router.push({ name: 'Calendar' })"
              >
                <span class="w-14 shrink-0 text-sm font-medium text-ink-gray-7">
                  {{ formatTime(event.starts_on) }}
                </span>
                <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-9">
                  {{ event.subject }}
                </span>
                <span class="text-xs text-ink-gray-5">
                  {{ formatTime(event.ends_on) }}
                </span>
              </button>
            </div>
            <div v-else class="p-4 text-sm text-ink-gray-5">
              {{ __('No meetings scheduled for today.') }}
            </div>
          </div>

          <div class="rounded-lg border border-outline-gray-2 bg-surface-white">
            <div class="flex items-center justify-between border-b p-4">
              <div>
                <h2 class="font-semibold text-ink-gray-9">
                  {{ __('Next actions') }}
                </h2>
                <p class="mt-1 text-sm text-ink-gray-5">
                  {{ __('Tasks that keep the client cycle moving') }}
                </p>
              </div>
              <Button
                variant="ghost"
                :label="__('Open tasks')"
                @click="router.push({ name: 'Tasks' })"
              />
            </div>
            <div v-if="tasks.loading" class="p-4 text-sm text-ink-gray-5">
              {{ __('Loading...') }}
            </div>
            <div
              v-else-if="nextTasks.length"
              class="divide-y divide-outline-gray-1"
            >
              <button
                v-for="task in nextTasks"
                :key="task.name"
                class="flex w-full items-center gap-3 p-4 text-left hover:bg-surface-gray-1"
                @click="router.push({ name: 'Tasks' })"
              >
                <span
                  class="size-2 shrink-0 rounded-full"
                  :class="task.status === 'In Progress' ? 'bg-surface-blue-6' : 'bg-surface-amber-6'"
                />
                <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-9">
                  {{ task.title }}
                </span>
                <span class="shrink-0 text-xs text-ink-gray-5">
                  {{ formatDueDate(task.due_date) }}
                </span>
              </button>
            </div>
            <div v-else class="p-4 text-sm text-ink-gray-5">
              {{ __('No open tasks found.') }}
            </div>
          </div>
        </section>

        <section class="rounded-lg border border-outline-gray-2 bg-surface-white">
          <div
            class="flex flex-col gap-3 border-b p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <h2 class="font-semibold text-ink-gray-9">
                {{ __('Client cycle') }}
              </h2>
              <p class="mt-1 text-sm text-ink-gray-5">
                {{ __('Track the playbook by phase and client.') }}
              </p>
            </div>
            <Link
              class="form-control w-full sm:w-64"
              :value="cycleClientLabel"
              doctype="CRM Organization"
              :placeholder="__('Select client')"
              :hideMe="true"
              @change="selectCycleClient"
            />
          </div>
          <div v-if="cycleClientName && cycleTasks.length" class="p-4">
            <div class="mb-4 flex items-center justify-between">
              <span class="text-sm text-ink-gray-6">
                {{ cycleCompletedTasks }} / {{ cycleTasks.length }}
                {{ __('tasks completed') }}
              </span>
              <span class="text-sm font-medium text-ink-gray-8">
                {{ cycleProgress }}%
              </span>
            </div>
            <div class="mb-5 h-2 overflow-hidden rounded-full bg-surface-gray-2">
              <div
                class="h-full rounded-full bg-surface-green-6 transition-all"
                :style="{ width: `${cycleProgress}%` }"
              />
            </div>
            <div class="grid grid-cols-2 gap-3 md:grid-cols-3">
              <div
                v-for="phase in playbookPhases"
                :key="phase"
                class="rounded-md border border-outline-gray-1 p-3"
              >
                <div class="truncate text-xs text-ink-gray-5">{{ __(phase) }}</div>
                <div class="mt-1 text-sm font-medium text-ink-gray-8">
                  {{ phaseCounts[phase]?.done || 0 }} /
                  {{ phaseCounts[phase]?.total || 0 }}
                </div>
              </div>
            </div>
            <div class="mt-5 divide-y divide-outline-gray-1 border-t">
              <div
                v-for="task in cycleNextTasks"
                :key="task.name"
                class="flex items-center gap-3 py-3"
              >
                <span
                  class="size-2 shrink-0 rounded-full"
                  :class="
                    task.status === 'In Progress'
                      ? 'bg-surface-blue-6'
                      : 'bg-surface-amber-6'
                  "
                />
                <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">
                  {{ task.title }}
                </span>
                <span class="shrink-0 text-xs text-ink-gray-5">
                  {{ formatDueDate(task.due_date) }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="p-4 text-sm text-ink-gray-5">
            {{
              cycleClientName
                ? __('No playbook tasks found for this client.')
                : __('Select a client to view its five-week cycle.')
            }}
          </div>
        </section>

        <section
          class="flex flex-col gap-3 rounded-lg border border-dashed border-outline-gray-3 bg-surface-gray-1 p-5 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <h2 class="font-semibold text-ink-gray-9">
              {{ __('Start with a client') }}
            </h2>
            <p class="mt-1 text-sm text-ink-gray-6">
              {{ __('Open your client list to review context and next steps.') }}
            </p>
          </div>
          <Button
            variant="outline"
            :label="__('View organizations')"
            @click="router.push({ name: 'Organizations' })"
          />
        </section>
      </div>
    </main>
  </div>

  <Dialog
    v-model:open="showCycleDialog"
    :title="__('Start client cycle')"
    :size="'md'"
  >
    <template #default>
      <div class="flex flex-col gap-4 p-1">
        <p class="text-sm text-ink-gray-6">
          {{
            __(
              'This creates the standard CS playbook with 15 tasks for the selected client.',
            )
          }}
        </p>
        <Link
          class="form-control w-full"
          :value="selectedClientLabel"
          doctype="CRM Organization"
          :placeholder="__('Select client')"
          :hideMe="true"
          @change="selectClient"
        />
        <FormControl
          v-model="cycleStartDate"
          type="date"
          :label="__('Cycle start date')"
          :description="__('Weekend dates start on the next business day.')"
        />
        <ErrorMessage v-if="cycleError" :message="cycleError" />
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="w-full"
        :label="__('Create playbook tasks')"
        :loading="creatingCycle"
        :disabled="!selectedClient || !cycleStartDate"
        @click="startClientCycle"
      />
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import {
  buildCSPlaybookTasks,
  CS_PLAYBOOK_PHASES,
} from '@/utils/csPlaybook'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { sessionStore } from '@/stores/session'
import {
  call,
  createListResource,
  dayjs,
  Dialog,
  ErrorMessage,
  FormControl,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import CalendarDaysIcon from '~icons/lucide/calendar-days'
import ClipboardListIcon from '~icons/lucide/clipboard-list'
import TriangleAlertIcon from '~icons/lucide/triangle-alert'

const router = useRouter()
const { user } = sessionStore()
const today = dayjs().format('YYYY-MM-DD')
const showCycleDialog = ref(false)
const selectedClient = ref(null)
const cycleClient = ref(null)
const cycleStartDate = ref(today)
const creatingCycle = ref(false)
const cycleError = ref(null)

const selectedClientLabel = computed(
  () => selectedClient.value?.label || selectedClient.value?.value || '',
)
const cycleClientName = computed(
  () => cycleClient.value?.value || cycleClient.value?.name || '',
)
const cycleClientLabel = computed(
  () => cycleClient.value?.label || cycleClientName.value,
)

const events = createListResource({
  doctype: 'Event',
  fields: ['name', 'subject', 'starts_on', 'ends_on', 'status', 'owner'],
  filters: [
    ['status', '=', 'Open'],
    ['starts_on', '>=', `${today} 00:00:00`],
    ['starts_on', '<=', `${today} 23:59:59`],
    ['owner', '=', user],
  ],
  orderBy: 'starts_on asc',
  pageLength: 20,
  auto: true,
})

const tasks = createListResource({
  doctype: 'CRM Task',
  fields: [
    'name',
    'title',
    'status',
    'due_date',
    'assigned_to',
    'reference_doctype',
    'reference_docname',
    'cs_phase',
  ],
  filters: [
    ['status', 'in', ['Backlog', 'Todo', 'In Progress']],
    ['assigned_to', '=', user],
  ],
  orderBy: 'due_date asc',
  pageLength: 20,
  auto: true,
})

const todayEvents = computed(() => events.data || [])
const nextTasks = computed(() => (tasks.data || []).slice(0, 5))
const playbookPhases = CS_PLAYBOOK_PHASES
const cycleTasks = computed(() =>
  cycleClientName.value
    ? (tasks.data || []).filter(
        (task) =>
          task.reference_doctype === 'CRM Organization' &&
          task.reference_docname === cycleClientName.value,
      )
    : [],
)
const cycleCompletedTasks = computed(
  () => cycleTasks.value.filter((task) => task.status === 'Done').length,
)
const cycleProgress = computed(() =>
  cycleTasks.value.length
    ? Math.round((cycleCompletedTasks.value / cycleTasks.value.length) * 100)
    : 0,
)
const phaseCounts = computed(() =>
  playbookPhases.reduce((counts, phase) => {
    const phaseTasks = cycleTasks.value.filter((task) => task.cs_phase === phase)
    counts[phase] = {
      total: phaseTasks.length,
      done: phaseTasks.filter((task) => task.status === 'Done').length,
    }
    return counts
  }, {}),
)
const cycleNextTasks = computed(() =>
  cycleTasks.value.filter((task) => task.status !== 'Done').slice(0, 5),
)
const overdueTasks = computed(
  () =>
    (tasks.data || []).filter(
      (task) => task.due_date && dayjs(task.due_date).isBefore(dayjs()),
    ).length,
)

const metrics = computed(() => [
  {
    label: 'Meetings today',
    value: todayEvents.value.length,
    icon: CalendarDaysIcon,
    to: { name: 'Calendar' },
  },
  {
    label: 'Open tasks',
    value: tasks.data?.length || 0,
    icon: ClipboardListIcon,
    to: { name: 'Tasks' },
  },
  {
    label: 'Overdue tasks',
    value: overdueTasks.value,
    icon: TriangleAlertIcon,
    to: { name: 'Tasks' },
  },
])

function selectClient(client) {
  selectedClient.value =
    typeof client === 'string'
      ? { value: client, label: client }
      : client
  cycleError.value = null
}

function selectCycleClient(client) {
  cycleClient.value =
    typeof client === 'string' ? { value: client, label: client } : client
}

async function startClientCycle() {
  if (!selectedClient.value?.value || !cycleStartDate.value) return

  creatingCycle.value = true
  cycleError.value = null
  const clientName = selectedClient.value.value
  const playbookTasks = buildCSPlaybookTasks(cycleStartDate.value, {
    doctype: 'CRM Organization',
    name: clientName,
  })

  try {
    for (const task of playbookTasks) {
      await call('frappe.client.insert', {
        doc: {
          doctype: 'CRM Task',
          ...task,
          assigned_to: user,
        },
      })
    }

    showCycleDialog.value = false
    selectedClient.value = null
    await tasks.reload()
    toast.success(__('CS playbook created successfully'))
  } catch (error) {
    cycleError.value =
      error?.messages?.[0] ||
      error?.message ||
      __(
        'The playbook could not be completed. Some tasks may already have been created.',
      )
    console.error('Failed creating CS playbook', error)
  } finally {
    creatingCycle.value = false
  }
}

const formattedToday = computed(() => dayjs().format('dddd, D [of] MMMM'))

function formatTime(value) {
  return value ? dayjs(value).format('HH:mm') : '--:--'
}

function formatDueDate(value) {
  if (!value) return __('No date')
  const date = dayjs(value)
  return date.isBefore(dayjs(), 'day')
    ? __('Overdue')
    : date.format('DD/MM')
}
</script>
