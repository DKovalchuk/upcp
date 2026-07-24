import { toast } from 'sonner';

export const showToast = {
  success(message: string) {
    toast.success(message);
  },
  error(message: string) {
    toast.error(message);
  },
  info(message: string) {
    toast.info(message);
  },
  created(entity: string) {
    toast.success(`${entity} created successfully`);
  },
  updated(entity: string) {
    toast.success(`${entity} updated successfully`);
  },
  deleted(entity: string) {
    toast.success(`${entity} deleted successfully`);
  },
  mutationError(action: string, entity: string) {
    toast.error(`Failed to ${action} ${entity}`);
  },
};
