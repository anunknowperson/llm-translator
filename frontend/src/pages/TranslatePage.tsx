import { useEffect, useRef, useState } from "react";
import {
  Button,
  Card,
  Group,
  Loader,
  Select,
  Slider,
  Stack,
  Text,
  Textarea,
  Title,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

import {
  apiClient,
  Language,
  openTaskStatusSocket,
  ServiceUnavailableError,
  TargetLanguage,
  TaskResultPayload,
} from "../api/client";
import { ServiceErrorBanner } from "../components/ServiceErrorBanner";

const LANGUAGES: { value: TargetLanguage; label: string }[] = [
  { value: "en", label: "Английский" },
  { value: "ru", label: "Русский" },
  { value: "de", label: "Немецкий" },
  { value: "fr", label: "Французский" },
  { value: "es", label: "Испанский" },
  { value: "zh", label: "Китайский" },
  { value: "it", label: "Итальянский" },
  { value: "pt", label: "Португальский" },
  { value: "ja", label: "Японский" },
  { value: "ko", label: "Корейский" },
  { value: "ar", label: "Арабский" },
  { value: "tr", label: "Турецкий" },
  { value: "pl", label: "Польский" },
  { value: "nl", label: "Нидерландский" },
  { value: "sv", label: "Шведский" },
  { value: "uk", label: "Украинский" },
  { value: "cs", label: "Чешский" },
  { value: "el", label: "Греческий" },
  { value: "hi", label: "Хинди" },
  { value: "id", label: "Индонезийский" },
  { value: "vi", label: "Вьетнамский" },
  { value: "th", label: "Тайский" },
  { value: "fi", label: "Финский" },
  { value: "da", label: "Датский" },
  { value: "no", label: "Норвежский" },
  { value: "ro", label: "Румынский" },
  { value: "hu", label: "Венгерский" },
];

// Источник: те же языки + опция автоопределения
const SOURCE_LANGUAGES: { value: Language; label: string }[] = [
  { value: "auto", label: "Определить автоматически" },
  ...LANGUAGES,
];

// Карта код -> человекочитаемое название, используется для отображения
// языка, который модель определила автоматически
const LANGUAGE_LABELS: Record<string, string> = Object.fromEntries(
  LANGUAGES.map((l) => [l.value, l.label])
);

type Phase = "idle" | "queued" | "running" | "done" | "error" | "service_down";

export function TranslatePage() {
  const [text, setText] = useState("");
  const [sourceLang, setSourceLang] = useState<Language>("auto");
  const [targetLang, setTargetLang] = useState<TargetLanguage>("ru");
  const [creativity, setCreativity] = useState(0.3);

  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<TaskResultPayload | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const closeSocket = useRef<(() => void) | null>(null);

  useEffect(() => {
    return () => {
      closeSocket.current?.();
    };
  }, []);

  async function handleSubmit() {
    if (!text.trim()) return;

    closeSocket.current?.();
    setResult(null);
    setErrorMessage(null);
    setPhase("queued");

    try {
      const enqueued = await apiClient.enqueueTranslation({
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
        creativity,
      });

      // UX асинхронности + (*) WebSocket: вместо ручного опроса подписываемся на сервер по WS,
      // он сам присылает обновления статуса, пока бэкенд генерирует перевод
      closeSocket.current = openTaskStatusSocket(
        enqueued.task_id,
        (statusUpdate) => {
          if (statusUpdate.status === "STARTED") {
            setPhase("running");
          } else if (statusUpdate.status === "SUCCESS" && statusUpdate.result) {
            setResult(statusUpdate.result);
            setPhase("done");
          } else if (statusUpdate.status === "FAILURE") {
            setErrorMessage(statusUpdate.error ?? "Не удалось выполнить перевод");
            setPhase("error");
          }
        },
        () => setPhase("service_down")
      );
    } catch (err) {
      if (err instanceof ServiceUnavailableError) {
        setPhase("service_down");
      } else {
        notifications.show({ color: "red", title: "Ошибка", message: (err as Error).message });
        setPhase("idle");
      }
    }
  }

  const isBusy = phase === "queued" || phase === "running";

  return (
    <Stack maw={760}>
      <Title order={2}>Перевод текста</Title>

      <Textarea
        label="Текст для перевода"
        placeholder="Введите текст..."
        autosize
        minRows={4}
        value={text}
        onChange={(e) => setText(e.currentTarget.value)}
      />

      <Group grow>
        <Select
          label="Исходный язык"
          data={SOURCE_LANGUAGES}
          value={sourceLang}
          onChange={(v) => v && setSourceLang(v as Language)}
          searchable
        />
        <Select
          label="Целевой язык"
          data={LANGUAGES}
          value={targetLang}
          onChange={(v) => v && setTargetLang(v as TargetLanguage)}
          searchable
        />
      </Group>

      <Stack gap={4}>
        <Text size="sm" fw={500}>
          Креативность перевода: {creativity.toFixed(2)}
        </Text>
        <Slider min={0} max={1} step={0.05} value={creativity} onChange={setCreativity} />
      </Stack>

      <Group>
        <Button onClick={handleSubmit} loading={isBusy} disabled={!text.trim()}>
          Перевести
        </Button>
        {isBusy && (
          <Group gap={6}>
            <Loader size="sm" />
            <Text size="sm" c="dimmed">
              {phase === "queued" ? "Задача поставлена в очередь..." : "Модель генерирует перевод..."}
            </Text>
          </Group>
        )}
      </Group>

      {phase === "service_down" && <ServiceErrorBanner />}
      {phase === "error" && errorMessage && <ServiceErrorBanner message={errorMessage} />}

      {phase === "done" && result && (
        <Card withBorder padding="lg" radius="md">
          <Text size="sm" c="dimmed" mb={4}>
            Перевод ({result.source_lang.toUpperCase()} → {result.target_lang.toUpperCase()})
            {sourceLang === "auto" && (
              <> — язык источника определён автоматически: {LANGUAGE_LABELS[result.source_lang] ?? result.source_lang.toUpperCase()}</>
            )}
          </Text>
          <Text>{result.translated_text}</Text>
        </Card>
      )}
    </Stack>
  );
}
