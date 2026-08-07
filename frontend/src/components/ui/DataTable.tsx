import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { SearchInput } from '@/components/ui/SearchInput';
import { DataTablePagination } from '@/components/ui/DataTablePagination';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Rows3,
  List,
  LayoutList,
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export type SortDirection = 'asc' | 'desc' | null;

export interface ColumnDef<T> {
  key: string;
  header: string;
  sortable?: boolean;
  className?: string;
  render: (item: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  total?: number;
  offset?: number;
  limit?: number;
  onPageChange?: (offset: number) => void;
  onPageSizeChange?: (limit: number) => void;
  onSortChange?: (key: string, direction: SortDirection) => void;
  onFilterChange?: (query: string) => void;
  filterPlaceholder?: string;
  density?: 'compact' | 'default' | 'comfortable';
  onDensityChange?: (density: 'compact' | 'default' | 'comfortable') => void;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  filterable?: boolean;
  sortable?: boolean;
}

const ROW_CLASSES = {
  compact: 'h-8',
  default: 'h-10',
  comfortable: 'h-12',
};

const CELL_CLASSES = {
  compact: 'px-2 py-1',
  default: 'px-2 py-2',
  comfortable: 'px-3 py-3',
};

const DENSITY_ICONS = {
  compact: Rows3,
  default: LayoutList,
  comfortable: List,
};

const DENSITY_LABELS = {
  compact: 'Compact',
  default: 'Default',
  comfortable: 'Comfortable',
};

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  total,
  offset = 0,
  limit = 20,
  onPageChange,
  onPageSizeChange,
  onSortChange,
  onFilterChange,
  filterPlaceholder = 'Filter...',
  density: controlledDensity,
  onDensityChange,
  emptyMessage = 'No results',
  onRowClick,
  filterable = false,
  sortable = false,
}: DataTableProps<T>) {
  const [internalDensity, setInternalDensity] = useState<'compact' | 'default' | 'comfortable'>('default');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>(null);

  const density = controlledDensity ?? internalDensity;
  const handleDensityChange = (d: 'compact' | 'default' | 'comfortable') => {
    if (onDensityChange) onDensityChange(d);
    else setInternalDensity(d);
  };

  const handleSort = (key: string) => {
    if (!sortable) return;
    let newDir: SortDirection;
    if (sortKey === key) {
      newDir = sortDir === 'asc' ? 'desc' : sortDir === 'desc' ? null : 'asc';
    } else {
      newDir = 'asc';
    }
    setSortKey(newDir ? key : null);
    setSortDir(newDir);
    onSortChange?.(key, newDir);
  };

  const DensityIcon = DENSITY_ICONS[density];

  return (
    <div className="space-y-2">
      {(filterable || sortable) && (
        <div className="flex items-center justify-between gap-2">
          {filterable && onFilterChange && (
            <SearchInput
              placeholder={filterPlaceholder}
              onSearch={onFilterChange}
            />
          )}
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger render={<Button variant="ghost" size="icon" className="min-h-[44px] min-w-[44px]" onClick={() => {
                const densities: Array<'compact' | 'default' | 'comfortable'> = ['compact', 'default', 'comfortable'];
                const idx = densities.indexOf(density);
                handleDensityChange(densities[(idx + 1) % densities.length]);
              }} aria-label="Toggle density" />}>
                <DensityIcon className="h-4 w-4" />
              </TooltipTrigger>
              <TooltipContent>{DENSITY_LABELS[density]}</TooltipContent>
            </Tooltip>
          </div>
        </div>
      )}

      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((col) => (
              <TableHead
                key={col.key}
                className={`${col.className} ${col.sortable && sortable ? 'cursor-pointer select-none hover:bg-muted/50' : ''}`}
                onClick={() => col.sortable && handleSort(col.key)}
              >
                <div className="flex items-center gap-1">
                  {col.header}
                  {col.sortable && sortable && (
                    <span className="text-muted-foreground">
                      {sortKey === col.key ? (
                        sortDir === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      ) : (
                        <ArrowUpDown className="h-3 w-3 opacity-50" />
                      )}
                    </span>
                  )}
                </div>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            data.map((item, idx) => (
              <TableRow
                key={idx}
                className={`${ROW_CLASSES[density]} ${onRowClick ? 'cursor-pointer hover:bg-muted/50' : ''}`}
                onClick={() => onRowClick?.(item)}
                onKeyDown={onRowClick ? (e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onRowClick(item);
                  }
                } : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                role={onRowClick ? 'button' : undefined}
              >
                {columns.map((col) => (
                  <TableCell key={col.key} className={`${CELL_CLASSES[density]} ${col.className}`}>
                    {col.render(item)}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {total !== undefined && onPageChange && onPageSizeChange && (
        <DataTablePagination
          offset={offset}
          limit={limit}
          total={total}
          onPageChange={onPageChange}
          onPageSizeChange={onPageSizeChange}
        />
      )}
    </div>
  );
}
