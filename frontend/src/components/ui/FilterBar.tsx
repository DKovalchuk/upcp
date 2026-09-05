import { useFilters } from '@/hooks/use-filters';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Search, X } from 'lucide-react';

interface FilterBarProps {
  statusOptions?: { value: string; label: string }[];
  showSearch?: boolean;
  showStatus?: boolean;
  searchPlaceholder?: string;
}

export function FilterBar({
  statusOptions = [],
  showSearch = true,
  showStatus = true,
  searchPlaceholder = 'Search...',
}: FilterBarProps) {
  const { filters, setFilter, clearFilters, hasActiveFilters } = useFilters();

  return (
    <div className="flex flex-wrap items-center gap-2">
      {showSearch && (
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={searchPlaceholder}
            value={filters.search ?? ''}
            onChange={(e) => setFilter('search', e.target.value || undefined)}
            className="h-8 w-48 pl-8"
          />
        </div>
      )}

      {showStatus && statusOptions.length > 0 && (
        <Select
          value={filters.status ?? 'all'}
          onValueChange={(v) => setFilter('status', v === 'all' ? undefined : v ?? undefined)}
        >
          <SelectTrigger className="h-8 w-36">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {statusOptions.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {hasActiveFilters && (
        <Button variant="ghost" size="sm" onClick={clearFilters} className="h-8 px-2">
          <X className="h-3.5 w-3.5 mr-1" />
          Clear
        </Button>
      )}
    </div>
  );
}
