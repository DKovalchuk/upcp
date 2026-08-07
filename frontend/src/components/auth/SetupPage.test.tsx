import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SetupPage } from './SetupPage';

const mockNavigate = vi.fn();

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}));

const mockSetTokens = vi.fn();
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ setTokens: mockSetTokens }),
}));

vi.mock('@/lib/auth', () => ({
  authSetup: vi.fn(),
}));

function renderSetup() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <SetupPage />
    </QueryClientProvider>,
  );
}

describe('SetupPage', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockSetTokens.mockClear();
  });

  it('renders display name, email, and password fields', () => {
    renderSetup();
    expect(screen.getByLabelText('Display Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('renders create account button', () => {
    renderSetup();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('password field is type=password by default', () => {
    renderSetup();
    const passwordInput = screen.getByLabelText('Password');
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('toggles password visibility on button click', () => {
    renderSetup();
    const toggleButton = screen.getByRole('button', { name: /show password/i });
    const passwordInput = screen.getByLabelText('Password');

    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /hide password/i }));
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('shows minimum 8 characters hint', () => {
    renderSetup();
    expect(screen.getByText('Minimum 8 characters')).toBeInTheDocument();
  });

  it('uses navigate instead of window.location after setup', async () => {
    const { authSetup } = await import('@/lib/auth');
    vi.mocked(authSetup).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
    });

    renderSetup();

    fireEvent.change(screen.getByLabelText('Display Name'), { target: { value: 'Admin' } });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith({ to: '/', replace: true });
    });
  });

  it('shows error message on setup failure', async () => {
    const { authSetup } = await import('@/lib/auth');
    vi.mocked(authSetup).mockRejectedValue(new Error('Setup failed'));

    renderSetup();

    fireEvent.change(screen.getByLabelText('Display Name'), { target: { value: 'Admin' } });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText('Setup failed')).toBeInTheDocument();
    });
  });

  it('password has minLength=8 constraint', () => {
    renderSetup();
    const passwordInput = screen.getByLabelText('Password');
    expect(passwordInput).toHaveAttribute('minLength', '8');
  });
});
