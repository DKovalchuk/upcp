import { useState, useCallback } from 'react';
import { useTask, useUpdateTask, useDeleteTask } from '@/hooks/use-tasks';
import {
  useCreateAcceptanceCriterion,
  useCreateDoDItem,
  useSubmitReviewVerdict,
} from '@/hooks/use-quality';
import { useCreateSubtask } from '@/hooks/use-subtasks';
import { useReleaseTask } from '@/hooks/use-task-execution';
import { showToast } from '@/lib/toast';

export function useTaskDetail(taskId: string | null) {
  const { data: task, isLoading } = useTask(taskId ?? '');
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();
  const createAC = useCreateAcceptanceCriterion();
  const createDoD = useCreateDoDItem();
  const createSubtask = useCreateSubtask();
  const releaseTask = useReleaseTask();
  const submitVerdict = useSubmitReviewVerdict();

  const [newAC, setNewAC] = useState('');
  const [newDoD, setNewDoD] = useState('');
  const [newSubtask, setNewSubtask] = useState('');
  const [activeTab, setActiveTab] = useState('details');
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleAddAC = useCallback(async () => {
    if (!taskId || !newAC.trim()) return;
    try {
      await createAC.mutateAsync({ taskId, data: { description: newAC.trim() } });
      setNewAC('');
      showToast.created('Acceptance criterion');
    } catch {
      showToast.mutationError('create', 'acceptance criterion');
    }
  }, [taskId, newAC, createAC]);

  const handleAddDoD = useCallback(async () => {
    if (!taskId || !newDoD.trim()) return;
    try {
      await createDoD.mutateAsync({ taskId, data: { name: newDoD.trim() } });
      setNewDoD('');
      showToast.created('DoD item');
    } catch {
      showToast.mutationError('create', 'DoD item');
    }
  }, [taskId, newDoD, createDoD]);

  const handleAddSubtask = useCallback(async () => {
    if (!taskId || !newSubtask.trim()) return;
    try {
      await createSubtask.mutateAsync({ taskId, data: { title: newSubtask.trim() } });
      setNewSubtask('');
      showToast.created('Subtask');
    } catch {
      showToast.mutationError('create', 'subtask');
    }
  }, [taskId, newSubtask, createSubtask]);

  const handleStatusChange = useCallback(
    async (newStatus: string) => {
      if (!taskId) return;
      try {
        await updateTask.mutateAsync({ id: taskId, data: { status: newStatus } });
        showToast.updated('Task');
      } catch {
        showToast.mutationError('update', 'task');
      }
    },
    [taskId, updateTask]
  );

  const handleDelete = useCallback(async () => {
    if (!taskId) return;
    try {
      await deleteTask.mutateAsync(taskId);
      showToast.deleted('Task');
    } catch {
      showToast.mutationError('delete', 'task');
    }
  }, [taskId, deleteTask]);

  const handleReleaseClaim = useCallback(async () => {
    if (!taskId) return;
    try {
      await releaseTask.mutateAsync(taskId);
      showToast.success('Claim released');
    } catch {
      showToast.mutationError('release', 'claim');
    }
  }, [taskId, releaseTask]);

  const handleSubmitVerdict = useCallback(
    async (roundId: string, verdict: string, confidence: number, summary: string) => {
      try {
        await submitVerdict.mutateAsync({ roundId, data: { verdict, confidence, summary } });
        showToast.updated('Review verdict');
      } catch {
        showToast.mutationError('submit', 'review verdict');
      }
    },
    [submitVerdict]
  );

  return {
    task,
    isLoading,
    isReleasing: releaseTask.isPending,
    newAC,
    setNewAC,
    newDoD,
    setNewDoD,
    newSubtask,
    setNewSubtask,
    activeTab,
    setActiveTab,
    confirmDelete,
    setConfirmDelete,
    handleAddAC,
    handleAddDoD,
    handleAddSubtask,
    handleStatusChange,
    handleDelete,
    handleReleaseClaim,
    handleSubmitVerdict,
  };
}
