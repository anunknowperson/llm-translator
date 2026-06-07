import { AppShell, Group, NavLink, Title } from "@mantine/core";
import { IconHistory, IconChartBar, IconLanguage } from "@tabler/icons-react";
import { Link, Route, Routes, useLocation } from "react-router-dom";

import { TranslatePage } from "./pages/TranslatePage";
import { HistoryPage } from "./pages/HistoryPage";
import { StatsPage } from "./pages/StatsPage";

const NAV_ITEMS = [
  { to: "/", label: "Перевод", icon: IconLanguage },
  { to: "/history", label: "История", icon: IconHistory },
  { to: "/stats", label: "Статистика", icon: IconChartBar },
];

export function App() {
  const location = useLocation();

  return (
    <AppShell header={{ height: 60 }} navbar={{ width: 220, breakpoint: "sm" }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md">
          <Title order={3}>LLM Translator</Title>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            component={Link}
            to={item.to}
            label={item.label}
            leftSection={<item.icon size={18} />}
            active={location.pathname === item.to}
          />
        ))}
      </AppShell.Navbar>

      <AppShell.Main>
        <Routes>
          <Route path="/" element={<TranslatePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/stats" element={<StatsPage />} />
        </Routes>
      </AppShell.Main>
    </AppShell>
  );
}
