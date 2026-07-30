import { useProjectId } from '@/hooks/use-project-id';
import { useGitProviders, useGitBranches, useGitCommits } from '@/hooks/use-git';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { Badge } from '@/components/ui/badge';
import { GitBranch, GitCommit, Plug } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export function GitIntegrationPage() {
  const projectId = useProjectId();

  const { data: providers, isLoading: providersLoading, error: providersError } =
    useGitProviders(projectId);

  if (providersLoading) return <PageSkeleton rows={5} />;
  if (providersError) return <ErrorState message="Failed to load git providers" />;

  if (!providers?.length) {
    return (
      <EmptyState
        icon={Plug}
        title="No git providers"
        description="Connect a git repository to track branches and commits."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <GitBranch className="h-5 w-5" />
        <h2 className="text-lg font-semibold">Git Integration</h2>
      </div>

      {providers.map((provider) => (
        <ProviderCard key={provider.id} provider={provider} />
      ))}
    </div>
  );
}

function ProviderCard({
  provider,
}: {
  provider: { id: string; name: string; provider_type: string; url: string; status: string };
}) {
  const { data: branches = [], isLoading: branchesLoading } = useGitBranches(provider.id);
  const { data: commits = [], isLoading: commitsLoading } = useGitCommits(provider.id);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <CardTitle className="text-base">{provider.name}</CardTitle>
          <StatusBadge status={provider.status} />
          <Badge variant="outline" className="text-xs">
            {provider.provider_type}
          </Badge>
        </div>
        <span className="text-xs text-muted-foreground font-mono">{provider.url}</span>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="mb-2 text-sm font-medium text-muted-foreground">Branches</h4>
          {branchesLoading ? (
            <div className="h-16 animate-pulse rounded bg-muted" />
          ) : branches.length === 0 ? (
            <p className="text-xs text-muted-foreground">No branches found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Last Commit</TableHead>
                  <TableHead className="w-[80px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {branches.map((branch) => (
                  <TableRow key={branch.id}>
                    <TableCell className="font-mono text-sm">{branch.name}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {branch.last_commit_sha?.slice(0, 8) ?? '—'}
                    </TableCell>
                    <TableCell>
                      {branch.is_default && (
                        <Badge variant="secondary" className="text-xs">default</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        <div>
          <h4 className="mb-2 text-sm font-medium text-muted-foreground flex items-center gap-1">
            <GitCommit className="h-4 w-4" />
            Recent Commits
          </h4>
          {commitsLoading ? (
            <div className="h-16 animate-pulse rounded bg-muted" />
          ) : commits.length === 0 ? (
            <p className="text-xs text-muted-foreground">No commits found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">SHA</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead>Author</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {commits.map((commit) => (
                  <TableRow key={commit.id}>
                    <TableCell className="font-mono text-xs">{commit.sha.slice(0, 8)}</TableCell>
                    <TableCell className="text-sm">{commit.message}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{commit.author}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(commit.committed_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
