import { useEffect, useState } from "react";
import { Button, Card, Group, Loader, SimpleGrid, Stack, Text, Title } from "@mantine/core";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiClient, ServiceUnavailableError, StatsResponse } from "../api/client";
import { ServiceErrorBanner } from "../components/ServiceErrorBanner";

// (*) Визуальная репрезентация: статистика использования сервиса отражена на графиках,
// которые можно перерисовать по запросу (косвенный вызов модели через накопленную историю)
export function StatsPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [serviceDown, setServiceDown] = useState(false);

  async function load() {
    setLoading(true);
    setServiceDown(false);
    try {
      setStats(await apiClient.getStats());
    } catch (err) {
      if (err instanceof ServiceUnavailableError) setServiceDown(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (serviceDown) return <ServiceErrorBanner />;
  if (loading || !stats) return <Loader />;

  const pairData = stats.by_language_pair.map((p) => ({
    pair: `${p.source_lang.toUpperCase()}→${p.target_lang.toUpperCase()}`,
    count: p.count,
  }));

  return (
    <Stack maw={1000}>
      <Group justify="space-between">
        <Title order={2}>Статистика использования</Title>
        <Button variant="light" onClick={load}>
          Обновить
        </Button>
      </Group>

      <Text>
        Всего выполнено переводов: <b>{stats.total_translations}</b>
      </Text>

      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <Card withBorder radius="md" padding="md">
          <Text fw={500} mb="sm">
            Переводы по языковым парам
          </Text>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={pairData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="pair" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#228be6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card withBorder radius="md" padding="md">
          <Text fw={500} mb="sm">
            Переводы по дням (последние 14 дней)
          </Text>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={stats.by_day}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#40c057" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </SimpleGrid>
    </Stack>
  );
}
