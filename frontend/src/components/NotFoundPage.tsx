import { Link } from '@tanstack/react-router';
import { buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileQuestion } from 'lucide-react';
import { cn } from '@/lib/utils';

export function NotFoundPage() {
  return (
    <Card className="max-w-md mx-auto mt-8">
      <CardHeader className="text-center">
        <div className="flex justify-center mb-4">
          <FileQuestion className="h-12 w-12 text-muted-foreground" />
        </div>
        <CardTitle className="text-2xl font-bold">404</CardTitle>
        <p className="text-muted-foreground">Page not found</p>
      </CardHeader>
      <CardContent className="text-center space-y-4">
        <p className="text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/" className={cn(buttonVariants())}>
          Back to Dashboard
        </Link>
      </CardContent>
    </Card>
  );
}
