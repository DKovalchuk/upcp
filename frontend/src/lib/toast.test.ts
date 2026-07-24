import { describe, it, expect, vi } from 'vitest';
import { showToast } from './toast';

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

import { toast } from 'sonner';
const mockToast = vi.mocked(toast);

describe('showToast', () => {
  it('calls toast.success for success', () => {
    showToast.success('It worked');
    expect(mockToast.success).toHaveBeenCalledWith('It worked');
  });

  it('calls toast.error for error', () => {
    showToast.error('Something broke');
    expect(mockToast.error).toHaveBeenCalledWith('Something broke');
  });

  it('calls toast.info for info', () => {
    showToast.info('FYI');
    expect(mockToast.info).toHaveBeenCalledWith('FYI');
  });

  it('formats created message', () => {
    showToast.created('Project');
    expect(mockToast.success).toHaveBeenCalledWith('Project created successfully');
  });

  it('formats updated message', () => {
    showToast.updated('Task');
    expect(mockToast.success).toHaveBeenCalledWith('Task updated successfully');
  });

  it('formats deleted message', () => {
    showToast.deleted('Component');
    expect(mockToast.success).toHaveBeenCalledWith('Component deleted successfully');
  });

  it('formats mutation error', () => {
    showToast.mutationError('create', 'feature');
    expect(mockToast.error).toHaveBeenCalledWith('Failed to create feature');
  });
});
