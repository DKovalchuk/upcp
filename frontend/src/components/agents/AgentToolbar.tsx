// Agent Toolbar component — TASK-0099 Sprint 2

import { SearchInput } from '@/components/ui/SearchInput';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LayoutGrid, List } from 'lucide-react';

interface AgentToolbarProps {
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusFilterChange: (value: string) => void;
  viewMode: 'grid' | 'table';
  onViewModeChange: (mode: 'grid' | 'table') => void;
}

export function AgentToolbar({
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  viewMode,
  onViewModeChange,
}: AgentToolbarProps) {
  return (
    <div className="flex items-center gap-3">
      <SearchInput
        onSearch={onSearchChange}
        placeholder="Search agents..."
      />
      <Select value={statusFilter} onValueChange={(v) => onStatusFilterChange(v ?? 'all')}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Status</SelectItem>
          <SelectItem value="working">Working</SelectItem>
          <SelectItem value="idle">Idle</SelectItem>
          <SelectItem value="stale">Stale</SelectItem>
          <SelectItem value="offline">Offline</SelectItem>
        </SelectContent>
      </Select>
      <div className="flex items-center rounded-md border ml-auto">
        <Button
          variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
          size="icon"
          onClick={() => onViewModeChange('grid')}
        >
          <LayoutGrid className="h-4 w-4" />
        </Button>
        <Button
          variant={viewMode === 'table' ? 'secondary' : 'ghost'}
          size="icon"
          onClick={() => onViewModeChange('table')}
        >
          <List className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
