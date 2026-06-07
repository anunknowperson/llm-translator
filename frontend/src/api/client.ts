// Слабая связность: фронтенд общается с бэкендом только через REST API по относительному пути /api,
// который проксирует Nginx. Никаких прямых импортов из бэкенда и никакого доступа к БД/Redis.
const API_BASE = "/api";

export class ServiceUnavailableError extends Error {
  constructor() {
    super("Сервис временно недоступен");
    this.name = "ServiceUnavailableError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    // Обработка сбоев: сетевые ошибки (бэкенд недоступен) превращаются в понятную ошибку,
    // а не падение интерфейса с трейсбеком
    throw new ServiceUnavailableError();
  }

  if (response.status === 503) {
    throw new ServiceUnavailableError();
  }

  if (!response.ok) {
    let message = `Ошибка запроса (${response.status})`;
    try {
      const body = await response.json();
      message = body.message ?? message;
    } catch {
      /* ignore body parse errors */
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export type Language =
  | "auto"
  | "en"
  | "ru"
  | "de"
  | "fr"
  | "es"
  | "zh"
  | "it"
  | "pt"
  | "ja"
  | "ko"
  | "ar"
  | "tr"
  | "pl"
  | "nl"
  | "sv"
  | "uk"
  | "cs"
  | "el"
  | "hi"
  | "id"
  | "vi"
  | "th"
  | "fi"
  | "da"
  | "no"
  | "ro"
  | "hu";

// "auto" допустим только для source_lang (автоопределение языка)
export type TargetLanguage = Exclude<Language, "auto">;

export interface TranslateRequestBody {
  text: string;
  source_lang: Language;
  target_lang: TargetLanguage;
  creativity: number;
}

export interface TaskEnqueuedResponse {
  task_id: string;
  status: string;
}

export interface TaskResultPayload {
  source_text: string;
  translated_text: string;
  source_lang: string;
  target_lang: Language;
  creativity: number;
}

export interface TaskStatusResponse {
  task_id: string;
  status: "PENDING" | "STARTED" | "SUCCESS" | "FAILURE";
  result?: TaskResultPayload | null;
  error?: string | null;
}

export interface TranslationHistoryItem {
  id: string;
  source_text: string;
  translated_text: string;
  source_lang: string;
  target_lang: Language;
  creativity: number;
  created_at: string;
}

export interface TranslationHistoryPage {
  items: TranslationHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface LanguagePairStat {
  source_lang: string;
  target_lang: string;
  count: number;
}

export interface DailyStat {
  date: string;
  count: number;
}

export interface StatsResponse {
  total_translations: number;
  by_language_pair: LanguagePairStat[];
  by_day: DailyStat[];
}

export interface HealthResponse {
  status: string;
  components: { name: string; status: string; detail?: string | null }[];
}

// (*) Проверка статуса задачи через WebSocket: открывает соединение с бэкендом,
// который сам проталкивает обновления статуса до тех пор, пока задача не завершится
export function openTaskStatusSocket(
  taskId: string,
  onMessage: (status: TaskStatusResponse) => void,
  onError: () => void
): () => void {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}${API_BASE}/translate/ws/${taskId}`);

  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data) as TaskStatusResponse);
    } catch {
      onError();
    }
  };
  socket.onerror = () => onError();

  return () => socket.close();
}

export const apiClient = {
  enqueueTranslation: (body: TranslateRequestBody) =>
    request<TaskEnqueuedResponse>("/translate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getTaskStatus: (taskId: string) =>
    request<TaskStatusResponse>(`/translate/tasks/${taskId}`),

  getHistory: (limit = 20, offset = 0) =>
    request<TranslationHistoryPage>(`/history?limit=${limit}&offset=${offset}`),

  getStats: () => request<StatsResponse>("/stats"),

  getHealth: () => request<HealthResponse>("/health"),
};
