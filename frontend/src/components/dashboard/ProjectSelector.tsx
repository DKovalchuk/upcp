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
  const selectedId = search.project_id ?? '';
  const { data: projectsData } = useProjects({ limit: 100 });
  const projects = projectsData?.items ?? [];

  if (projects.length <= 1) return null;

  const handleChange = (value: string | null) => {
    const v = value ?? 'all';
    if (v === 'all') {
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
