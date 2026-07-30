import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EntityFormDialog } from './EntityFormDialog';
import type { FormField } from './EntityFormDialog';

const simpleFields: FormField[] = [
  { name: 'name', label: 'Name', required: true, placeholder: 'Enter name' },
  { name: 'description', label: 'Description', type: 'textarea' },
];

const selectFields: FormField[] = [
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Active', value: 'active' },
      { label: 'Paused', value: 'paused' },
    ],
  },
];

describe('EntityFormDialog', () => {
  it('renders dialog when open', () => {
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Create Item"
        fields={simpleFields}
        onSubmit={async () => {}}
      />
    );
    expect(screen.getByText('Create Item')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <EntityFormDialog
        open={false}
        onOpenChange={() => {}}
        title="Create Item"
        fields={simpleFields}
        onSubmit={async () => {}}
      />
    );
    expect(screen.queryByText('Create Item')).not.toBeInTheDocument();
  });

  it('renders all fields', () => {
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        fields={simpleFields}
        onSubmit={async () => {}}
      />
    );
    expect(screen.getByLabelText(/Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/)).toBeInTheDocument();
  });

  it('shows required indicator for required fields', () => {
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        fields={simpleFields}
        onSubmit={async () => {}}
      />
    );
    const nameLabel = screen.getByText('Name');
    expect(nameLabel.parentElement?.textContent).toContain('*');
  });

  it('validates required fields on submit', async () => {
    const onSubmit = vi.fn();
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        fields={simpleFields}
        onSubmit={onSubmit}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('calls onSubmit with form data when valid', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        fields={simpleFields}
        onSubmit={onSubmit}
      />
    );

    fireEvent.change(screen.getByPlaceholderText('Enter name'), {
      target: { value: 'Test Item' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({ name: 'Test Item' });
    });
  });

  it('auto-generates slug from name', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const fieldsWithSlug: FormField[] = [
      { name: 'name', label: 'Name', required: true },
      { name: 'slug', label: 'Slug' },
    ];

    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        fields={fieldsWithSlug}
        onSubmit={onSubmit}
      />
    );

    fireEvent.change(screen.getByLabelText(/Name/), {
      target: { value: 'My Cool Project' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'My Cool Project',
        slug: 'my-cool-project',
      });
    });
  });

  it('renders select field with shadcn Select component', () => {
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        fields={selectFields}
        onSubmit={async () => {}}
      />
    );
    // shadcn Select renders a combobox trigger; options are in a portal (visible only when opened)
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('calls onOpenChange when cancel is clicked', () => {
    const onOpenChange = vi.fn();
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={onOpenChange}
        title="Form"
        fields={simpleFields}
        onSubmit={async () => {}}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('shows description when provided', () => {
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        description="Fill in the details"
        fields={simpleFields}
        onSubmit={async () => {}}
      />
    );
    expect(screen.getByText('Fill in the details')).toBeInTheDocument();
  });

  it('uses custom submit label', () => {
    render(
      <EntityFormDialog
        open={true}
        onOpenChange={() => {}}
        title="Form"
        fields={simpleFields}
        onSubmit={async () => {}}
        submitLabel="Create"
      />
    );
    expect(screen.getByRole('button', { name: 'Create' })).toBeInTheDocument();
  });
});
