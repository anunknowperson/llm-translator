import { Alert } from "@mantine/core";
import { IconAlertTriangle } from "@tabler/icons-react";

// Обработка сбоев: единая "красивая" заглушка вместо падения UI с трейсбеком,
// когда бэкенд недоступен или вернул 503
export function ServiceErrorBanner({ message }: { message?: string }) {
  return (
    <Alert
      icon={<IconAlertTriangle size={18} />}
      color="red"
      title="Сервис временно недоступен"
      variant="light"
    >
      {message ?? "Не удалось связаться с сервером. Пожалуйста, попробуйте немного позже."}
    </Alert>
  );
}
