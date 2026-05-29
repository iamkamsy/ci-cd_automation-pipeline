import type { Task } from "@/types/task"

export class SessionExpiredError extends Error {}

async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(input, { credentials: "include", ...init })
  if (res.status === 401) {
    throw new SessionExpiredError("Session expired.")
  }
  return res
}

export async function getTasks(): Promise<Task[]> {
  const res = await apiFetch("/api/tasks")
  if (!res.ok) throw new Error("Failed to load tasks.")
  return res.json()
}

export async function createTask(
  name: string,
  deadline: string,
  description: string
): Promise<Task> {
  const res = await apiFetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, deadline, description }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || "Failed to create task.")
  return data
}

export async function updateTask(
  id: string,
  name: string,
  deadline: string,
  description: string
): Promise<Task> {
  const res = await apiFetch(`/api/tasks/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, deadline, description }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || "Failed to update task.")
  return data
}

export async function deleteTask(id: string): Promise<void> {
  const res = await apiFetch(`/api/tasks/${id}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error || "Failed to delete task.")
  }
}
