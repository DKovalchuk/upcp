import { useNavigate, useSearch } from '@tanstack/react-router';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useProjects } from '@/hooks/use-projects';

export function ProjectSelector() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as Record<string, string | undefined>;
  const { data: projectsData } = useProjects({ limit: 100 });
  const projects = projectsData?.items ?? [];
  // B15.3/B15.4 (TASK-0154): a project_id not present in the loaded list
  // (unknown or non-UUID) falls back to "All Projects".
  const rawProjectId = search.project_id ?? '';
  const selectedId = projects.some((p) => p.id === rawProjectId)
    ? rawProjectId
    : '';

  if (projects.length <= 1) return null;

  const handleChange = (value: string | null) => {
    const v = value ?? 'all';
    if (v === 'all') {
      // Documented escapes (TASK-0155): routes have no search validators —
      // typed navigate() rejects object-form search (probe: TS2322/TS2353).
      navigate({ search: {} as any });
    } else {
      navigate({ search: { project_id: v } as any });
    }
  };

  return (
    <Select value={selectedId || 'all'} onValueChange={handleChange}>
      <SelectTrigger className="w-56">
        <SelectValue placeholder="All Projects" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Projects</SelectItem>
        {projects.map((p) => (
          <SelectItem key={p.id} value={p.id}>
            {p.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
