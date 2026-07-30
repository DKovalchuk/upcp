import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export interface FormField {
  name: string;
  label: string;
  type?: 'text' | 'textarea' | 'select';
  required?: boolean;
  options?: { label: string; value: string }[];
  placeholder?: string;
}

interface EntityFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  fields: FormField[];
  initialData?: Record<string, string | null>;
  onSubmit: (data: Record<string, string>) => Promise<void>;
  submitLabel?: string;
}

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export function EntityFormDialog({
  open,
  onOpenChange,
  title,
  description,
  fields,
  initialData,
  onSubmit,
  submitLabel = 'Save',
}: EntityFormDialogProps) {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) {
      const initial: Record<string, string> = {};
      for (const field of fields) {
        initial[field.name] = initialData?.[field.name] ?? '';
      }
      setFormData(initial);
      setErrors({});
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, fields, JSON.stringify(initialData)]);

  const handleChange = (name: string, value: string) => {
    setFormData((prev) => {
      const next = { ...prev, [name]: value };
      // Auto-generate slug from name (only if slug field exists and is empty)
      if (name === 'name' && fields.some((f) => f.name === 'slug') && !prev.slug) {
        next.slug = toSlug(value);
      }
      return next;
    });
    if (errors[name]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    for (const field of fields) {
      if (field.required && !formData[field.name]?.trim()) {
        newErrors[field.name] = `${field.label} is required`;
      }
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      // Clean empty strings to undefined for optional fields
      const cleaned: Record<string, string> = {};
      for (const [key, value] of Object.entries(formData)) {
        if (value.trim()) cleaned[key] = value.trim();
      }
      await onSubmit(cleaned);
      onOpenChange(false);
    } catch {
      setErrors({ _form: 'Something went wrong. Please try again.' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            {description && <DialogDescription>{description}</DialogDescription>}
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {errors._form && (
              <p className="text-sm text-destructive">{errors._form}</p>
            )}
            {fields.map((field) => (
              <div key={field.name} className="space-y-2">
                <label
                  htmlFor={field.name}
                  className="text-sm font-medium leading-none"
                >
                  {field.label}
                  {field.required && (
                    <span className="ml-1 text-destructive">*</span>
                  )}
                </label>
                {field.type === 'textarea' ? (
                  <textarea
                    id={field.name}
                    value={formData[field.name] ?? ''}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                ) : field.type === 'select' && field.options ? (
                  <Select value={formData[field.name] || ''} onValueChange={(v) => handleChange(field.name, v ?? '')}>
                    <SelectTrigger className="h-10 w-full">
                      <SelectValue placeholder="Select..." />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    id={field.name}
                    value={formData[field.name] ?? ''}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                  />
                )}
                {errors[field.name] && (
                  <p className="text-sm text-destructive">{errors[field.name]}</p>
                )}
              </div>
            ))}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Saving...' : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
