import type { FormField } from './EntityFormDialog';

export const projectFields: FormField[] = [
  { name: 'name', label: 'Name', required: true, placeholder: 'My Project' },
  { name: 'slug', label: 'Slug', placeholder: 'auto-generated-from-name' },
  { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Project description...' },
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Active', value: 'active' },
      { label: 'Paused', value: 'paused' },
      { label: 'Archived', value: 'archived' },
    ],
  },
];

export const componentFields: FormField[] = [
  { name: 'name', label: 'Name', required: true, placeholder: 'Backend' },
  { name: 'slug', label: 'Slug', placeholder: 'auto-generated-from-name' },
  { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Component description...' },
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Active', value: 'active' },
      { label: 'Paused', value: 'paused' },
      { label: 'Archived', value: 'archived' },
    ],
  },
];

export const moduleFields: FormField[] = [
  { name: 'name', label: 'Name', required: true, placeholder: 'Authentication' },
  { name: 'slug', label: 'Slug', placeholder: 'auto-generated-from-name' },
  { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Module description...' },
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Active', value: 'active' },
      { label: 'Paused', value: 'paused' },
      { label: 'Archived', value: 'archived' },
    ],
  },
];

export const featureFields: FormField[] = [
  { name: 'name', label: 'Name', required: true, placeholder: 'User Authentication' },
  { name: 'slug', label: 'Slug', placeholder: 'auto-generated-from-name' },
  { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Feature description...' },
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Backlog', value: 'backlog' },
      { label: 'In Progress', value: 'in-progress' },
      { label: 'Done', value: 'done' },
      { label: 'Archived', value: 'archived' },
    ],
  },
];

export const taskFields: FormField[] = [
  { name: 'title', label: 'Title', required: true, placeholder: 'Implement login form' },
  { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Task description...' },
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Backlog', value: 'backlog' },
      { label: 'In Progress', value: 'in-progress' },
      { label: 'Review', value: 'review' },
      { label: 'Done', value: 'done' },
    ],
  },
  {
    name: 'priority',
    label: 'Priority',
    type: 'select',
    options: [
      { label: 'P0 — Critical', value: '0' },
      { label: 'P1 — High', value: '1' },
      { label: 'P2 — Medium', value: '2' },
      { label: 'P3 — Low', value: '3' },
    ],
  },
];
