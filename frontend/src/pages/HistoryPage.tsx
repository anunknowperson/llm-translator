import { useEffect, useState } from "react";
import { Badge, Button, Card, Group, Loader, Pagination, Stack, Text, Title } from "@mantine/core";

import { apiClient, ServiceUnavailableError, TranslationHistoryItem } from "../api/client";
import { ServiceErrorBanner } from "../components/ServiceErrorBanner";

const PAGE_SIZE = 10;

export function HistoryPage() {
  const [items, setItems] = useState<TranslationHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [serviceDown, setServiceDown] = useState(false);

  async function load(p: number) {
    setLoading(true);
    setServiceDown(false);
    try {
      const data = await apiClient.getHistory(PAGE_SIZE, (p - 1) * PAGE_SIZE);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof ServiceUnavailableError) {
        setServiceDown(true);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  if (serviceDown) return <ServiceErrorBanner />;

  return (
    <Stack maw={900}>
      <Group justify="space-between">
        <Title order={2}>История переводов</Title>
        <Button variant="light" onClick={() => load(page)}>
          Обновить
        </Button>
      </Group>

      {loading && <Loader />}

      {!loading && items.length === 0 && <Text c="dimmed">Переводов пока нет</Text>}

      {!loading &&
        items.map((item) => (
          <Card key={item.id} withBorder radius="md" padding="md">
            <Group justify="space-between" mb={6}>
              <Badge variant="light">
                {item.source_lang.toUpperCase()} → {item.target_lang.toUpperCase()}
              </Badge>
              <Text size="xs" c="dimmed">
                {new Date(item.created_at).toLocaleString()}
              </Text>
            </Group>
            <Text size="sm" mb={4}>
              <b>Источник:</b> {item.source_text}
            </Text>
            <Text size="sm">
              <b>Перевод:</b> {item.translated_text}
            </Text>
          </Card>
        ))}

      {total > PAGE_SIZE && (
        <Pagination value={page} onChange={setPage} total={Math.ceil(total / PAGE_SIZE)} />
      )}
    </Stack>
  );
}
