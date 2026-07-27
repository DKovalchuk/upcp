import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface ShortcutGroup {
  title: string;
  shortcuts: { keys: string; description: string }[];
}

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: 'Navigation',
    shortcuts: [
      { keys: 'Ctrl+K', description: 'Command palette' },
      { keys: 'Ctrl+/', description: 'Search' },
      { keys: 'Ctrl+B', description: 'Toggle sidebar' },
      { keys: 'Ctrl+J', description: 'Toggle theme' },
      { keys: 'G D', description: 'Go to Dashboard' },
      { keys: 'G P', description: 'Go to Projects' },
      { keys: 'G R', description: 'Go to Reports' },
      { keys: 'G S', description: 'Go to Settings' },
    ],
  },
  {
    title: 'Tasks',
    shortcuts: [
      { keys: 'T C', description: 'Claim task' },
      { keys: 'T R', description: 'Release task' },
      { keys: 'T S', description: 'Submit for review' },
      { keys: 'T E', description: 'Attach evidence' },
      { keys: 'T Q', description: 'Request clarification' },
    ],
  },
  {
    title: 'General',
    shortcuts: [
      { keys: '?', description: 'Show keyboard shortcuts' },
      { keys: 'Esc', description: 'Close dialog / Cancel' },
      { keys: 'Enter', description: 'Confirm / Select' },
      { keys: '↑ ↓', description: 'Navigate lists' },
    ],
  },
];

interface ShortcutsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ShortcutsDialog({ open, onOpenChange }: ShortcutsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.title}>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                {group.title}
              </h3>
              <div className="space-y-1">
                {group.shortcuts.map((shortcut) => (
                  <div
                    key={shortcut.keys}
                    className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-muted/50"
                  >
                    <span className="text-sm">{shortcut.description}</span>
                    <kbd className="inline-flex items-center gap-1 rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] font-medium text-muted-foreground">
                      {shortcut.keys}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
