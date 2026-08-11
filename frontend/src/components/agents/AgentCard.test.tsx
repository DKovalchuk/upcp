// Agent Card tests — TASK-0099 Sprint 2

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AgentCard } from './AgentCard';
import type { AgentProfile } from '@/types/agent';

const mockAgent: AgentProfile = {
  id: 'agent-1',
  name: 'claude-builder',
  description: 'Code builder agent',
  is_active: true,
  created_by: 'user-1',
  created_at: '2026-08-01T10:00:00Z',
};

describe('AgentCard', () => {
  it('renders agent name', () => {
    render(<AgentCard agent={mockAgent} onSelect={vi.fn()} />);
    expect(screen.getByText('claude-builder')).toBeDefined();
  });

  it('renders description', () => {
    render(<AgentCard agent={mockAgent} onSelect={vi.fn()} />);
    expect(screen.getByText('Code builder agent')).toBeDefined();
  });

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn();
    render(<AgentCard agent={mockAgent} onSelect={onSelect} />);
    screen.getByText('claude-builder').click();
    expect(onSelect).toHaveBeenCalledOnce();
  });

  it('renders without description', () => {
    const agent = { ...mockAgent, description: null };
    render(<AgentCard agent={agent} onSelect={vi.fn()} />);
    expect(screen.getByText('claude-builder')).toBeDefined();
  });
});
