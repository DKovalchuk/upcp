import { useState } from 'react';
import { Bookmark, BookmarkCheck, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useSavedViews } from '@/hooks/use-saved-views';
import type { SavedView } from '@/hooks/use-saved-views';

interface SavedViewsDropdownProps {
  currentFilters: Record<string, string>;
  onApplyView: (filters: Record<string, string>) => void;
}

export function SavedViewsDropdown({
  currentFilters,
  onApplyView,
}: SavedViewsDropdownProps) {
  const { views, addView, removeView } = useSavedViews();
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [newName, setNewName] = useState('');

  const handleSave = () => {
    if (!newName.trim()) return;
    addView(newName.trim(), currentFilters);
    setNewName('');
    setShowSaveDialog(false);
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-1.5">
            <Bookmark className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Views</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="text-xs">Saved Views</DropdownMenuLabel>
          <DropdownMenuSeparator />

          {views.length === 0 ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">
              No saved views
            </div>
          ) : (
            <DropdownMenuGroup>
              {views.map((view) => (
                <DropdownMenuItem
                  key={view.id}
                  className="flex items-center justify-between"
                  onSelect={() => onApplyView(view.filters)}
                >
                  <span className="flex items-center gap-2">
                    <BookmarkCheck className="h-3.5 w-3.5" />
                    {view.name}
                  </span>
                  <button
                    className="ml-2 text-muted-foreground hover:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeView(view.id);
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </DropdownMenuItem>
              ))}
            </DropdownMenuGroup>
          )}

          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={() => setShowSaveDialog(true)}>
            <Plus className="mr-2 h-3.5 w-3.5" />
            Save current filters
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Save View</DialogTitle>
          </DialogHeader>
          <Input
            placeholder="View name (e.g. My blocked tasks)"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!newName.trim()}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
